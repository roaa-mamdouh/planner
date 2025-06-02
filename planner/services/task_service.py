import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, getdate
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
        return "unassigned"

    @staticmethod
    def format_task(task):
        """Format task for API response"""
        try:
            # Get primary assignee with fallback
            try:
                assignee = TaskService.get_primary_assignee(task)
            except Exception as e:
                frappe.logger().error(f"Error getting primary assignee: {str(e)}")
                assignee = "unassigned"

            # Get task color with fallback
            try:
                color = TaskService.get_task_color(task)
            except Exception as e:
                frappe.logger().error(f"Error getting task color: {str(e)}")
                color = "#6B7280"  # Default gray

            # Get assignees list with fallback
            try:
                assignees = TaskService.get_task_assignees(task)
            except Exception as e:
                frappe.logger().error(f"Error getting task assignees: {str(e)}")
                assignees = []

            # Parse comments safely
            try:
                comments_count = len(frappe.parse_json(task._comments or "[]"))
            except Exception as e:
                frappe.logger().error(f"Error parsing comments: {str(e)}")
                comments_count = 0

            return {
                "id": task.name,
                "title": task.subject or "Untitled Task",
                "project": task.project or "",
                "status": task.status or "Open",
                "priority": task.priority or "Medium",
                "assignee": assignee,
                "startDate": task.exp_start_date,
                "endDate": task.exp_end_date,
                "duration": float(task.expected_time or 0),
                "color": color,
                "type": task.type or "Task",
                "description": task.description or "",
                "isScheduled": bool(task.exp_start_date and task.exp_end_date),
                "isOverdue": TaskService.is_task_overdue(task),
                "assignees": assignees,
                "comments_count": comments_count,
                "created": task.creation,
                "modified": task.modified
            }
        except Exception as e:
            frappe.logger().error(f"Error formatting task {task.name}: {str(e)}")
            # Return a minimal valid task object instead of raising
            return {
                "id": task.name if hasattr(task, 'name') else "unknown",
                "title": task.subject if hasattr(task, 'subject') else "Error Loading Task",
                "status": "Error",
                "priority": "Medium",
                "assignee": "Unassigned",
                "startDate": None,
                "endDate": None,
                "duration": 0,
                "color": "#EF4444",  # Red to indicate error
                "type": "Task",
                "description": "Error loading task details",
                "isScheduled": False,
                "isOverdue": False,
                "assignees": [],
                "comments_count": 0,
                "created": task.creation if hasattr(task, 'creation') else None,
                "modified": task.modified if hasattr(task, 'modified') else None
            }

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

                # Debug logging for batch update
                frappe.logger().info(f"batch_update_tasks: Updating task {task_id} with changes {changes}")
                
                for field, value in changes.items():
                    if hasattr(task, field):
                        setattr(task, field, value)
                
                task.modified = now_datetime()
                task.save()
                frappe.db.commit()
                updated_tasks.append(task)
            except Exception as e:
                frappe.logger().error(f"Error updating task {task_id}: {str(e)}")
                continue
        
        # Emit batch update
        if updated_tasks:
            emit_batch_update(updated_tasks)
        
        # Debug logging for batch update result
        frappe.logger().info(f"batch_update_tasks: Updated tasks count {len(updated_tasks)}")
        
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
            if assignee_id == "unassigned":
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
            # Convert to string in ISO format to ensure consistency
            if isinstance(start_date, str):
                task.exp_start_date = getdate(start_date)
            else:
                task.exp_start_date = start_date.strftime("%Y-%m-%d")
        else:
            task.exp_start_date = None
            
        if end_date:
            if isinstance(end_date, str):
                task.exp_end_date = getdate(end_date)
            else:
                task.exp_end_date = end_date.strftime("%Y-%m-%d")
        else:
            task.exp_end_date = None
        
        task.modified = now_datetime()
        try:
            task.save()
            frappe.db.commit()
        except frappe.TimestampMismatchError:
            # Reload and retry save to handle concurrent modification
            task.reload()
            task.save()
            frappe.db.commit()

        # Debug logging for move_task
        frappe.logger().info(f"move_task: Updated task {task.name} with start_date={task.exp_start_date} end_date={task.exp_end_date} assignee={task._assign}")

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
            
            formatted_tasks = []
            for task in tasks:
                try:
                    formatted_task = TaskService.format_task(task)
                    formatted_tasks.append(formatted_task)
                except Exception as format_error:
                    frappe.logger().error(f"Error formatting task {task.name}: {str(format_error)}")
                    continue
            
            return formatted_tasks
            
        except Exception as e:
            frappe.logger().error(f"Error in get_all_tasks: {str(e)}")
            return []  # Return empty list instead of raising
