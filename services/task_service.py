import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, getdate, add_days, date_diff
from ..realtime import emit_task_update, emit_batch_update

class TaskService:
    @staticmethod
    def get_task_color(task):
        """Get color based on task status and priority"""
        status_colors = {
            "Completed": "#10B981",  # green
            "Working": "#3B82F6",    # blue
            "Overdue": "#EF4444",    # red
            "Open": "#6B7280"        # gray
        }
        
        priority_colors = {
            "High": "#DC2626",       # red
            "Medium": "#F59E0B",     # amber
            "Low": "#10B981"         # green
        }
        
        return status_colors.get(task.status) or priority_colors.get(task.priority) or "#6B7280"

    @staticmethod
    def get_task_assignees(task):
        """Get detailed assignee information"""
        assignees = []
        if task._assign:
            assigned_users = frappe.parse_json(task._assign)
            for user in assigned_users:
                user_info = frappe.get_cached_value(
                    "User",
                    user,
                    ["full_name", "user_image"],
                    as_dict=True
                )
                if user_info:
                    assignees.append({
                        "id": user,
                        "name": user_info.full_name,
                        "image": user_info.user_image
                    })
        return assignees

    @staticmethod
    def get_primary_assignee(task):
        """Get the primary assignee from _assign field"""
        try:
            if task._assign:
                assigned_users = frappe.parse_json(task._assign)
                if assigned_users and len(assigned_users) > 0:
                    assignee = assigned_users[0]
                    if frappe.db.exists("User", assignee):
                        return assignee
                    frappe.logger().warning(f"Invalid user {assignee} assigned to task {task.name}")
        except Exception as e:
            frappe.logger().error(f"Error getting primary assignee for task {task.name}: {str(e)}")
        return "Unassigned"

    @staticmethod
    def format_task(task):
        """Format task for API response"""
        try:
            assignee = TaskService.get_primary_assignee(task)
            
            return {
                "id": task.name,
                "title": task.subject,
                "project": task.project or "",
                "status": task.status or "Open",
                "priority": task.priority or "Medium",
                "assignee": assignee,
                "startDate": task.exp_start_date,
                "endDate": task.exp_end_date,
                "duration": float(task.expected_time or 0),
                "color": TaskService.get_task_color(task),
                "type": task.type or "Task",
                "description": task.description or "",
                "isScheduled": bool(task.exp_start_date and task.exp_end_date),
                "isOverdue": TaskService.is_task_overdue(task),
                "assignees": TaskService.get_task_assignees(task),
                "comments_count": len(frappe.parse_json(task._comments or "[]")),
                "created": task.creation,
                "modified": task.modified
            }
        except Exception as e:
            frappe.logger().error(f"Error formatting task {task.name}: {str(e)}")
            raise

    @staticmethod
    def is_task_overdue(task):
        """Check if task is overdue"""
        if not task.exp_end_date or task.status == "Completed":
            return False
        return getdate(task.exp_end_date) < getdate()

    @staticmethod
    def update_task(task_id, updates, user=None):
        """Update task with validation and real-time updates"""
        if not task_id:
            frappe.throw(_("Task ID is required"))

        # Authorization check
        if user and not frappe.has_permission("Task", "write", user=user):
            frappe.throw(_("Not authorized to update tasks"), frappe.PermissionError)
        
        task = frappe.get_doc("Task", task_id)
        
        # Validate updates
        valid_fields = [
            "status", "priority", "exp_start_date",
            "exp_end_date", "expected_time", "description"
        ]
        
        for field, value in updates.items():
            if field not in valid_fields:
                frappe.throw(_(f"Invalid field: {field}"))
            
            setattr(task, field, value)
        
        task.modified = now_datetime()
        task.save()
        
        # Emit real-time update
        emit_task_update(task)
        
        return TaskService.format_task(task)

    @staticmethod
    def batch_update_tasks(updates, user=None):
        """Update multiple tasks in batch with validation"""
        if not updates:
            frappe.throw(_("No updates provided"))
        
        # Authorization check
        if user and not frappe.has_permission("Task", "write", user=user):
            frappe.throw(_("Not authorized to update tasks"), frappe.PermissionError)
        
        updated_tasks = []
        
        for update in updates:
            task_id = update.get("task_id")
            changes = update.get("changes", {})
            
            if not task_id or not changes:
                continue
            
            try:
                task = frappe.get_doc("Task", task_id)
                
                for field, value in changes.items():
                    if hasattr(task, field):
                        setattr(task, field, value)
                
                task.modified = now_datetime()
                task.save()
                updated_tasks.append(task)
            except Exception as e:
                frappe.logger().error(f"Error updating task {task_id}: {str(e)}")
                continue
        
        # Emit batch update
        if updated_tasks:
            emit_batch_update(updated_tasks)
        
        return [TaskService.format_task(task) for task in updated_tasks]

    @staticmethod
    def move_task(task_id, assignee_id=None, start_date=None, end_date=None, user=None):
        """Move task to different assignee or schedule with validation"""
        if not task_id:
            frappe.throw(_("Task ID is required"))
        
        # Authorization check
        if user and not frappe.has_permission("Task", "write", user=user):
            frappe.throw(_("Not authorized to move tasks"), frappe.PermissionError)
        
        task = frappe.get_doc("Task", task_id)
        
        # Update assignment
        if assignee_id:
            if assignee_id == "Unassigned":
                task._assign = None
            else:
                # Get employee record to validate
                employee = frappe.get_value("Employee", {"user_id": assignee_id}, "name")
                if employee:
                    task._assign = frappe.as_json([assignee_id])
                else:
                    frappe.throw(_("Invalid assignee"))
        
        # Update schedule
        if start_date:
            task.exp_start_date = getdate(start_date)
        else:
            task.exp_start_date = None
            
        if end_date:
            task.exp_end_date = getdate(end_date)
        else:
            task.exp_end_date = None
        
        task.modified = now_datetime()
        task.save()
        
        # Emit real-time update
        emit_task_update(task)
        
        return {
            "success": True,
            "task": TaskService.format_task(task),
            "message": "Task moved successfully"
        }

    @staticmethod
    def get_all_tasks(department=None, start_date=None, end_date=None):
        """Get all tasks with filtering and formatting"""
        try:
            filters = {
                "status": ["in", ["Open", "Working", "Completed", "Overdue"]]
            }
            
            if department:
                if not frappe.db.exists("Department", department):
                    frappe.logger().warning(f"Department {department} not found")
                else:
                    filters["department"] = department
            
            tasks = frappe.get_all(
                "Task",
                filters=filters,
                fields=[
                    "name", "subject", "status", "priority", "project",
                    "exp_start_date", "exp_end_date", "expected_time",
                    "department", "description", "color", "type",
                    "_assign", "_comments", "_seen", "creation",
                    "modified", "owner"
                ],
                order_by="creation desc"
            )
            
            return [TaskService.format_task(task) for task in tasks]
            
        except Exception as e:
            frappe.logger().error(f"Error in get_all_tasks: {str(e)}")
            # Return empty list instead of raising error
            return []
