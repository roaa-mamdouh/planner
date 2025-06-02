import frappe

def emit_task_update(task):
    """Emit real-time update for task changes"""
    try:
        frappe.publish_realtime(
            'task_update',
            {
                'task_id': task.name,
                'status': task.status,
                'assignee': task._assign,
                'modified': str(task.modified)
            },
            user=frappe.session.user
        )
    except Exception as e:
        frappe.logger().error(f"Error emitting task update: {str(e)}")

def emit_batch_update(tasks):
    """Emit real-time update for batch task changes"""
    try:
        updates = [{
            'task_id': task.name,
            'status': task.status,
            'assignee': task._assign,
            'modified': str(task.modified)
        } for task in tasks]
        
        frappe.publish_realtime(
            'batch_task_update',
            {'updates': updates},
            user=frappe.session.user
        )
    except Exception as e:
        frappe.logger().error(f"Error emitting batch update: {str(e)}")
