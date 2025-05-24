import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime
from .realtime import emit_task_update, emit_batch_update

@frappe.whitelist()
def get_planner_tasks(department=None):
    """Get all tasks for the planner view grouped by employees"""
    filters = {
        "status": ["in", ["Open", "Working", "Completed", "Overdue"]],
        "exp_start_date": ["is", "set"],
        "exp_end_date": ["is", "set"]
    }
    
    if department:
        filters["department"] = department
    
    tasks = frappe.get_all(
        "Task",
        filters=filters,
        fields=[
            "name", "subject", "status", "priority", "project",
            "exp_start_date", "exp_end_date", "expected_time",
            "department", "description", "color",
            "_assign", "_comments", "_seen"
        ],
        order_by="exp_start_date asc"
    )
    
    # Group tasks by employee
    employees_dict = {}
    
    for task in tasks:
        task.color = get_task_color(task)
        task.assignees = get_task_assignees(task)
        task.comments = get_task_comments(task)
        
        # Get assigned users
        assigned_users = []
        if task._assign:
            assigned_users = frappe.parse_json(task._assign)
        
        # If no assignment, add to unassigned
        if not assigned_users:
            assigned_users = ["Unassigned"]
        
        # Add task to each assigned user
        for user in assigned_users:
            if user not in employees_dict:
                # Get user details
                if user != "Unassigned":
                    user_info = frappe.get_cached_value(
                        "User", user, ["full_name", "user_image"], as_dict=True
                    )
                    employee_name = user_info.get("full_name", user) if user_info else user
                else:
                    employee_name = "Unassigned"
                    
                employees_dict[user] = {
                    "id": user,
                    "name": employee_name,
                    "tasks": []
                }
            
            # Format task for timeline
            formatted_task = {
                "id": task.name,
                "name": task.name,
                "title": f"{task.project} - {task.subject}" if task.project else task.subject,
                "startDate": task.exp_start_date,
                "endDate": task.exp_end_date,
                "status": task.status,
                "priority": task.priority,
                "project": task.project,
                "expected_time": task.expected_time,
                "color": task.color,
                "subject": task.subject
            }
            
            employees_dict[user]["tasks"].append(formatted_task)
    
    # Convert to list format expected by frontend
    employees_list = list(employees_dict.values())
    
    return employees_list

@frappe.whitelist()
def planner_get_backlog(searchtext=None, projectText=None):
    """Get tasks for the backlog with enhanced search"""
    filters = {
        "status": ["in", ["Open", "Working"]],
        "exp_start_date": ["is", "not set"]
    }
    
    if searchtext:
        filters.update({
            "subject": ["like", f"%{searchtext}%"]
        })
    
    if projectText:
        filters.update({
            "project": ["like", f"%{projectText}%"]
        })
    
    tasks = frappe.get_all(
        "Task",
        filters=filters,
        fields=[
            "name", "subject", "status", "priority", "project",
            "exp_start_date", "exp_end_date", "expected_time",
            "department", "color", "_assign"
        ],
        order_by="creation desc"
    )
    
    for task in tasks:
        task.color = get_task_color(task)
        task.assigned_to = get_primary_assignee(task)
    
    return tasks

@frappe.whitelist()
def update_task(task_id, updates):
    """Update task with enhanced validation and real-time updates"""
    if not task_id:
        frappe.throw(_("Task ID is required"))
    
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
    
    return task.as_dict()

@frappe.whitelist()
def batch_update_tasks(updates):
    """Update multiple tasks in batch with real-time notifications"""
    if not updates:
        frappe.throw(_("No updates provided"))
    
    updated_tasks = []
    
    for update in updates:
        task_id = update.get("task_id")
        changes = update.get("changes", {})
        
        if not task_id or not changes:
            continue
        
        task = frappe.get_doc("Task", task_id)
        
        for field, value in changes.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        task.modified = now_datetime()
        task.save()
        updated_tasks.append(task)
    
    # Emit batch update
    if updated_tasks:
        emit_batch_update(updated_tasks)
    
    return [task.as_dict() for task in updated_tasks]

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
    
    # Return status color by default, or priority color if specified
    return status_colors.get(task.status) or priority_colors.get(task.priority) or "#6B7280"

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

def get_primary_assignee(task):
    """Get the primary assignee from _assign field"""
    if task._assign:
        assigned_users = frappe.parse_json(task._assign)
        if assigned_users and len(assigned_users) > 0:
            # Return the first assigned user as primary assignee
            return assigned_users[0]
    return "Unassigned"

def get_task_comments(task):
    """Get formatted task comments"""
    comments = []
    if task._comments:
        comment_data = frappe.parse_json(task._comments)
        for comment in comment_data:
            comments.append({
                "by": comment.get("comment_email"),
                "content": comment.get("content"),
                "timestamp": comment.get("creation")
            })
    return comments
