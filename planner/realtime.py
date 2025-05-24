import frappe
from frappe.realtime import get_redis_connection

def emit_task_update(task, event_type="task_update"):
    """Emit task update event to all connected clients"""
    redis = get_redis_connection()
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
    
    redis.publish("task_updates", frappe.as_json({
        "event": event_type,
        "task": task_data
    }))

def emit_batch_update(tasks, event_type="batch_task_update"):
    """Emit batch task update event to all connected clients"""
    redis = get_redis_connection()
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
    
    redis.publish("task_updates", frappe.as_json({
        "event": event_type,
        "tasks": task_data
    }))
