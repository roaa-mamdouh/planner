import frappe

def emit_task_update(task, event_type="task_update"):
    """Emit task update event to all connected clients"""
    task_data = {
        "name": task.name,
        "subject": task.subject,
        "status": task.status,
        "priority": task.priority,
        "project": task.project,
        "assigned_to": task.assigned_to,
        "exp_start_date": str(task.exp_start_date),
        "exp_end_date": str(task.exp_end_date),
        "expected_time": task.expected_time,
        "department": task.department
    }
    
    frappe.publish_realtime(event_type, task_data, user=None)

def emit_batch_update(tasks, event_type="batch_task_update"):
    """Emit batch task update event to all connected clients"""
    task_data = [{
        "name": task.name,
        "subject": task.subject,
        "status": task.status,
        "priority": task.priority,
        "project": task.project,
        "assigned_to": task.assigned_to,
        "exp_start_date": str(task.exp_start_date),
        "exp_end_date": str(task.exp_end_date),
        "expected_time": task.expected_time,
        "department": task.department
    } for task in tasks]
    
    frappe.publish_realtime(event_type, task_data, user=None)
