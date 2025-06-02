import frappe
from frappe import _
from frappe.utils import cint
from ..services.task_service import TaskService
from ..services.workload_service import WorkloadService

@frappe.whitelist()
def list_tasks():
    """List all tasks with optional filtering"""
    try:
        tasks = TaskService.get_all_tasks()
        return {
            "success": True,
            "total_count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        frappe.logger().error(f"Error listing tasks: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "total_count": 0,
            "tasks": []
        }

@frappe.whitelist()
def get_task(task_id):
    """Get single task by ID"""
    try:
        if not task_id:
            frappe.throw(_("Task ID is required"))
        
        task = frappe.get_doc("Task", task_id)
        return {
            "success": True,
            "task": TaskService.format_task(task)
        }
    except Exception as e:
        frappe.logger().error(f"Error getting task {task_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def update_task():
    """Update task with validation"""
    try:
        task_id = frappe.form_dict.get("task_id")
        updates = frappe.parse_json(frappe.form_dict.get("updates", "{}"))
        
        if not task_id:
            frappe.throw(_("Task ID is required"))
        if not updates:
            frappe.throw(_("No updates provided"))
        
        updated_task = TaskService.update_task(
            task_id, 
            updates,
            user=frappe.session.user
        )
        
        return {
            "success": True,
            "task": updated_task
        }
    except Exception as e:
        frappe.logger().error(f"Error updating task: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def batch_update_tasks():
    """Batch update multiple tasks"""
    try:
        updates = frappe.parse_json(frappe.form_dict.get("updates", "[]"))
        
        if not updates:
            frappe.throw(_("No updates provided"))
        
        updated_tasks = TaskService.batch_update_tasks(
            updates,
            user=frappe.session.user
        )
        
        return {
            "success": True,
            "tasks": updated_tasks
        }
    except Exception as e:
        frappe.logger().error(f"Error in batch update: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def move_task():
    """Move task to different assignee or schedule"""
    try:
        task_id = frappe.form_dict.get("task_id")
        assignee_id = frappe.form_dict.get("assignee_id")
        start_date = frappe.form_dict.get("start_date")
        end_date = frappe.form_dict.get("end_date")
        
        if not task_id:
            frappe.throw(_("Task ID is required"))
        
        result = TaskService.move_task(
            task_id,
            assignee_id,
            start_date,
            end_date,
            user=frappe.session.user
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        frappe.logger().error(f"Error moving task: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_workload():
    """Get workload data for planning"""
    try:
        department = frappe.form_dict.get("department")
        start_date = frappe.form_dict.get("start_date")
        end_date = frappe.form_dict.get("end_date")
        
        workload_data = WorkloadService.get_workload_data(
            department,
            start_date,
            end_date
        )
        
        return {
            "success": True,
            **workload_data
        }
    except Exception as e:
        frappe.logger().error(f"Error getting workload data: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "assignees": [],
            "tasks": []
        }

@frappe.whitelist()
def get_capacity_analysis():
    """Get capacity analysis for workload planning"""
    try:
        department = frappe.form_dict.get("department")
        start_date = frappe.form_dict.get("start_date")
        end_date = frappe.form_dict.get("end_date")
        
        analysis = WorkloadService.get_capacity_analysis(
            department,
            start_date,
            end_date
        )
        
        return {
            "success": True,
            **analysis
        }
    except Exception as e:
        frappe.logger().error(f"Error getting capacity analysis: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_planner_tasks():
    """Get tasks for planner view (legacy support)"""
    try:
        department = frappe.form_dict.get("department")
        workload_data = WorkloadService.get_workload_data(department)
        
        # Convert to legacy format
        employees_dict = {}
        for assignee in workload_data["assignees"]:
            assignee_tasks = [
                task for task in workload_data["tasks"]
                if task.get("assignee") == assignee["id"]
            ]
            
            employees_dict[assignee["id"]] = {
                "id": assignee["id"],
                "name": assignee["name"],
                "tasks": assignee_tasks
            }
        
        return {
            "success": True,
            "data": list(employees_dict.values())
        }
    except Exception as e:
        frappe.logger().error(f"Error getting planner tasks: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@frappe.whitelist()
def get_backlog():
    """Get unscheduled tasks for backlog"""
    try:
        searchtext = frappe.form_dict.get("searchtext")
        project = frappe.form_dict.get("project")
        
        filters = {
            "status": ["in", ["Open", "Working"]],
            "exp_start_date": ["is", "not set"]
        }
        
        if searchtext:
            filters["subject"] = ["like", f"%{searchtext}%"]
        
        if project:
            filters["project"] = ["like", f"%{project}%"]
        
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
        
        formatted_tasks = []
        for task in tasks:
            try:
                formatted_task = TaskService.format_task(task)
                formatted_tasks.append(formatted_task)
            except Exception as e:
                frappe.logger().error(f"Error formatting task {task.name}: {str(e)}")
                continue
        
        return {
            "success": True,
            "tasks": formatted_tasks
        }
    except Exception as e:
        frappe.logger().error(f"Error getting backlog: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "tasks": []
        }
