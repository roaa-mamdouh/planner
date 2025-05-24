import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime
from .realtime import emit_task_update, emit_batch_update

@frappe.whitelist()
def get_planner_tasks(department=None):
    """Get all tasks for the planner view with enhanced filtering"""
    filters = {
        "status": ["in", ["Open", "Working", "Completed", "Overdue"]],
    }
    
    if department:
        filters["department"] = department
    
    tasks = frappe.get_all(
        "Task",
        filters=filters,
        fields=[
            "name", "subject", "status", "priority", "project",
            "exp_start_date", "exp_end_date", "expected_time",
            "assigned_to", "department", "description", "color",
            "_assign", "_comments", "_seen"
        ],
        order_by="exp_start_date asc"
    )
    
    # Enhance task data with additional information
    for task in tasks:
        task.color = get_task_color(task)
        task.assignees = get_task_assignees(task)
        task.comments = get_task_comments(task)
        
    return tasks

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
            "assigned_to", "department", "color"
        ],
        order_by="creation desc"
    )
    
    for task in tasks:
        task.color = get_task_color(task)
    
    return tasks

@frappe.whitelist()
def update_task(task_id, updates):
    """Update task with enhanced validation and real-time updates"""
    if not task_id:
        frappe.throw(_("Task ID is required"))
    
    task = frappe.get_doc("Task", task_id)
    
    # Validate updates
    valid_fields = [
        "status", "priority", "assigned_to", "exp_start_date",
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
