import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, getdate, add_days, date_diff
from .realtime import emit_task_update, emit_batch_update

@frappe.whitelist(allow_guest=True)
def oauth_providers():
    """Get OAuth providers for authentication (required by frappe-ui)"""
    return []

@frappe.whitelist()
def verify_task_structure():
    """Verify Task doctype structure and required fields"""
    try:
        print("\n=== Verifying Task Structure ===")
        
        # Check if Task doctype exists
        if not frappe.db.exists("DocType", "Task"):
            print("ERROR: Task DocType does not exist!")
            return {"error": "Task DocType not found"}
            
        # Get Task doctype fields
        task_meta = frappe.get_meta("Task")
        print("\nTask Fields:")
        for field in task_meta.fields:
            print(f"- {field.fieldname} ({field.fieldtype})")
            
        # Check required fields exist
        required_fields = [
            "name", "subject", "status", "priority", 
            "exp_start_date", "exp_end_date", "expected_time",
            "department", "_assign"
        ]
        
        missing_fields = []
        for field in required_fields:
            if not task_meta.get_field(field):
                missing_fields.append(field)
                
        if missing_fields:
            print("\nMissing required fields:", missing_fields)
            return {"error": "Missing required fields", "fields": missing_fields}
            
        print("\nAll required fields present")
        return {"success": True, "message": "Task structure verified"}
        
    except Exception as e:
        print(f"Error verifying task structure: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def create_test_task():
    """Create a test task for debugging"""
    try:
        # First verify task structure
        verify_result = verify_task_structure()
        if "error" in verify_result:
            print("Task structure verification failed!")
            return verify_result
            
        # Get first department
        departments = frappe.get_all("Department", fields=["name"])
        if not departments:
            print("No departments found!")
            return
            
        department = departments[0].name
        
        # Get first employee in department
        employees = frappe.get_all(
            "Employee",
            filters={"department": department, "status": "Active"},
            fields=["name", "user_id"]
        )
        if not employees:
            print(f"No employees found in department {department}!")
            return
            
        employee = employees[0]
        
        # Create task
        task = frappe.get_doc({
            "doctype": "Task",
            "subject": "Test Task",
            "status": "Open",
            "priority": "Medium",
            "department": department,
            "_assign": frappe.as_json([employee.user_id]) if employee.user_id else None,
            "exp_start_date": frappe.utils.nowdate(),
            "exp_end_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
            "expected_time": 16
        })
        task.insert()
        
        print(f"""
Created test task:
- Name: {task.name}
- Department: {task.department}
- Assigned to: {task._assign}
""")
        
        return task.as_dict()
        
    except Exception as e:
        print(f"Error creating test task: {str(e)}")
        return None

@frappe.whitelist()
def list_tasks():
    """List all tasks in the system with their details"""
    try:
        # Get all tasks without any filters
        tasks = frappe.get_all(
            "Task",
            fields=[
                "name", "subject", "status", "priority", "project",
                "exp_start_date", "exp_end_date", "expected_time",
                "department", "_assign", "owner", "creation"
            ],
            order_by="creation desc"
        )
        
        formatted_tasks = []
        for task in tasks:
            try:
                assignee = "Unassigned"
                if task._assign:
                    assigned_users = frappe.parse_json(task._assign)
                    if assigned_users and len(assigned_users) > 0:
                        assignee = assigned_users[0]
                
                formatted_tasks.append({
                    "id": task.name,
                    "title": task.subject,
                    "status": task.status,
                    "department": task.department,
                    "assignee": assignee,
                    "project": task.project,
                    "scheduled": bool(task.exp_start_date and task.exp_end_date),
                    "created_by": task.owner,
                    "created_at": task.creation
                })
            except Exception as e:
                print(f"Error formatting task {task.name}: {str(e)}")
                continue
        
        print(f"Found {len(tasks)} total tasks, {len(formatted_tasks)} formatted successfully")
        return {
            "total_count": len(tasks),
            "tasks": formatted_tasks
        }
        
    except Exception as e:
        print(f"Error listing tasks: {str(e)}")
        return {"error": str(e), "total_count": 0, "tasks": []}

@frappe.whitelist()
def get_workload_data(department=None, start_date=None, end_date=None):
    """Get workload data for ClickUp-style workload view"""
    try:
        print("\n=== Workload Data Request ===")
        print(f"Department: {department}")
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        
        # Get all employees in department
        employees = get_department_employees(department)
        print(f"\nFound {len(employees)} employees in department")
        if employees:
            print("Sample employees:")
            for emp in employees[:2]:
                print(f"- {emp['name']} ({emp['id']})")
        
        # Get all tasks (scheduled and unscheduled)
        all_tasks = get_all_tasks(department, start_date, end_date)
        print(f"\nFound {len(all_tasks)} tasks")
        if all_tasks:
            print("Sample tasks:")
            for task in all_tasks[:2]:
                print(f"- {task['title']} (Assignee: {task['assignee']})")
        
        # Process workload data
        workload_data = {
            "assignees": [],
            "tasks": [],
            "capacity_settings": get_capacity_settings(department)
        }
    
        # Process each employee
        for employee in employees:
            employee_tasks = [task for task in all_tasks if task.get("assignee") == employee["id"]]
            print(f"\nEmployee {employee['name']}: {len(employee_tasks)} tasks")
            
            # Calculate capacity and utilization
            capacity_info = calculate_employee_capacity(employee["id"], start_date, end_date)
            
            assignee_data = {
                "id": employee["id"],
                "name": employee["name"],
                "email": employee["email"],
                "image": employee.get("image"),
                "role": employee.get("role", "Employee"),
                "department": employee.get("department"),
                "capacity": capacity_info["total_capacity"],
                "working_hours": capacity_info["working_hours"],
                "availability": capacity_info["availability"]
            }
            
            workload_data["assignees"].append(assignee_data)
            workload_data["tasks"].extend(employee_tasks)
        
        print(f"\n=== Final Workload Data ===")
        print(f"Total Assignees: {len(workload_data['assignees'])}")
        print(f"Total Tasks: {len(workload_data['tasks'])}")
        return workload_data
        
    except Exception as e:
        frappe.logger().error(f"Error in get_workload_data: {str(e)}")
        frappe.throw(_("Error getting workload data: {0}").format(str(e)))

@frappe.whitelist()
def get_planner_tasks(department=None):
    """Get all tasks for the planner view grouped by employees (legacy support)"""
    workload_data = get_workload_data(department)
    
    # Convert to legacy format for backward compatibility
    employees_dict = {}
    
    for assignee in workload_data["assignees"]:
        assignee_tasks = [task for task in workload_data["tasks"] if task.get("assignee") == assignee["id"]]
        
        employees_dict[assignee["id"]] = {
            "id": assignee["id"],
            "name": assignee["name"],
            "tasks": assignee_tasks
        }
    
    return list(employees_dict.values())

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
    try:
        if task._assign:
            frappe.logger().debug(f"Task {task.name} _assign field: {task._assign}")
            assigned_users = frappe.parse_json(task._assign)
            frappe.logger().debug(f"Parsed assigned users: {assigned_users}")
            
            if assigned_users and len(assigned_users) > 0:
                assignee = assigned_users[0]
                # Verify if user exists
                user_exists = frappe.db.exists("User", assignee)
                if user_exists:
                    return assignee
                else:
                    frappe.logger().warning(f"Invalid user {assignee} assigned to task {task.name}")
            else:
                frappe.logger().debug(f"No users in _assign list for task {task.name}")
        else:
            frappe.logger().debug(f"No _assign field for task {task.name}")
    except Exception as e:
        frappe.logger().error(f"Error getting primary assignee for task {task.name}: {str(e)}")
    
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

def get_department_employees(department=None):
    """Get all employees in a department with their details"""
    filters = {"status": "Active"}
    if department:
        filters["department"] = department
    
    employees = frappe.get_all(
        "Employee",
        filters=filters,
        fields=[
            "name", "employee_name", "user_id", "image", 
            "department", "designation", "company"
        ]
    )
    
    employee_list = []
    for emp in employees:
        # Get user details if user_id exists
        user_info = {}
        if emp.user_id:
            user_info = frappe.get_cached_value(
                "User", 
                emp.user_id, 
                ["full_name", "user_image", "email"], 
                as_dict=True
            ) or {}
        
        employee_data = {
            "id": emp.user_id or emp.name,
            "employee_id": emp.name,
            "name": user_info.get("full_name") or emp.employee_name,
            "email": user_info.get("email") or emp.user_id,
            "image": user_info.get("user_image") or emp.image,
            "role": emp.designation,
            "department": emp.department,
            "company": emp.company
        }
        employee_list.append(employee_data)
    
    return employee_list

def get_all_tasks(department=None, start_date=None, end_date=None):
    """Get all tasks (scheduled and unscheduled) for workload view"""
    try:
        # First check if there are any tasks at all
        all_tasks = frappe.get_all(
            "Task",
            fields=["name", "subject", "status", "department"]
        )
        print(f"DEBUG: Total tasks in system (unfiltered): {len(all_tasks)}")
        if all_tasks:
            print(f"DEBUG: Sample task: {all_tasks[0]}")
            
        # Check department exists if specified
        if department:
            dept_exists = frappe.db.exists("Department", department)
            print(f"DEBUG: Department {department} exists: {dept_exists}")
            if not dept_exists:
                print(f"WARNING: Department {department} not found")
                return []
        
        # Apply filters
        filters = {
            "status": ["in", ["Open", "Working", "Completed", "Overdue"]]
        }
        
        if department:
            filters["department"] = department
            
        print(f"DEBUG: Applying filters: {filters}")
        
        filtered_tasks = frappe.get_all(
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
        
        print(f"DEBUG: Found {len(filtered_tasks)} tasks after filtering")
        if len(filtered_tasks) > 0:
            print(f"DEBUG: Sample filtered task: {filtered_tasks[0]}")
        else:
            print("DEBUG: No tasks match the filters")
        
        formatted_tasks = []
    
        print("\nDEBUG: Starting task formatting...")
        for task in filtered_tasks:
            try:
                print(f"\nDEBUG: Formatting task {task.name}")
                # Get primary assignee
                assignee = get_primary_assignee(task)
                print(f"DEBUG: Primary assignee: {assignee}")
                
                # Format task for workload view
                formatted_task = {
                    "id": task.name,
                    "title": task.subject,
                    "project": task.project or "",
                    "status": task.status or "Open",
                    "priority": task.priority or "Medium",
                    "assignee": assignee,
                    "startDate": task.exp_start_date,
                    "endDate": task.exp_end_date,
                    "duration": float(task.expected_time or 0),
                    "color": get_task_color(task),
                    "type": task.type or "Task",
                    "description": task.description or "",
                    "isScheduled": bool(task.exp_start_date and task.exp_end_date),
                    "isOverdue": is_task_overdue(task),
                    "assignees": get_task_assignees(task),
                    "comments_count": len(frappe.parse_json(task._comments or "[]")),
                    "created": task.creation,
                    "modified": task.modified
                }
                
                print(f"DEBUG: Formatted task data: {formatted_task}")
                
                formatted_tasks.append(formatted_task)
                print(f"DEBUG: Successfully formatted task {task.name}")
            except Exception as e:
                frappe.logger().error(f"Error formatting task {task.name}: {str(e)}")
                continue
        
        return formatted_tasks
    except Exception as e:
        frappe.logger().error(f"Error in get_all_tasks: {str(e)}")
        return []

def calculate_employee_capacity(employee_id, start_date=None, end_date=None):
    """Calculate employee capacity and availability"""
    
    # Get employee working hours from HRMS
    working_hours = get_employee_working_hours(employee_id)
    
    # Calculate date range
    if not start_date:
        start_date = getdate()
    if not end_date:
        end_date = add_days(start_date, 30)  # Default 30 days
    
    start_date = getdate(start_date)
    end_date = getdate(end_date)
    
    # Calculate working days (excluding weekends and holidays)
    working_days = get_working_days(employee_id, start_date, end_date)
    
    # Calculate total capacity
    daily_hours = working_hours.get("hours_per_day", 8)
    total_capacity = working_days * daily_hours
    
    # Get leave applications
    leaves = get_employee_leaves(employee_id, start_date, end_date)
    leave_hours = sum(leave.get("hours", daily_hours) for leave in leaves)
    
    # Calculate availability
    available_capacity = total_capacity - leave_hours
    
    return {
        "total_capacity": total_capacity,
        "available_capacity": available_capacity,
        "working_hours": working_hours,
        "working_days": working_days,
        "leave_hours": leave_hours,
        "availability": (available_capacity / total_capacity * 100) if total_capacity > 0 else 0
    }

def get_employee_working_hours(employee_id):
    """Get employee working hours from HRMS"""
    try:
        # Try to get from Employee doctype
        employee = frappe.get_doc("Employee", {"user_id": employee_id})
        
        # Get holiday list
        holiday_list = employee.holiday_list or get_default_holiday_list(employee.company)
        
        # Default working hours
        working_hours = {
            "hours_per_day": 8,
            "days_per_week": 5,
            "holiday_list": holiday_list,
            "start_time": "09:00",
            "end_time": "17:00"
        }
        
        return working_hours
        
    except Exception:
        # Fallback to default
        return {
            "hours_per_day": 8,
            "days_per_week": 5,
            "holiday_list": None,
            "start_time": "09:00",
            "end_time": "17:00"
        }

def get_working_days(employee_id, start_date, end_date):
    """Calculate working days excluding weekends and holidays"""
    try:
        try:
            from hrms.hr.utils import get_holidays_for_employee
        except ImportError:
            get_holidays_for_employee = None
        
        holiday_dates = []
        if get_holidays_for_employee:
            # Get holidays for employee
            holidays = get_holidays_for_employee(employee_id, start_date, end_date)
            holiday_dates = [holiday.holiday_date for holiday in holidays]
        
        # Count working days
        working_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5 and current_date not in holiday_dates:
                working_days += 1
            current_date = add_days(current_date, 1)
        
        return working_days
        
    except Exception:
        # Fallback calculation (exclude weekends only)
        total_days = date_diff(end_date, start_date) + 1
        weeks = total_days // 7
        remaining_days = total_days % 7
        
        # Count weekend days in remaining days
        weekend_days = 0
        current_date = start_date
        for i in range(remaining_days):
            if current_date.weekday() >= 5:  # Saturday or Sunday
                weekend_days += 1
            current_date = add_days(current_date, 1)
        
        return total_days - (weeks * 2) - weekend_days

def get_employee_leaves(employee_id, start_date, end_date):
    """Get employee leave applications in date range"""
    try:
        leaves = frappe.get_all(
            "Leave Application",
            filters={
                "employee": {"in": frappe.get_all("Employee", {"user_id": employee_id}, "name")},
                "status": "Approved",
                "from_date": ["<=", end_date],
                "to_date": [">=", start_date]
            },
            fields=["from_date", "to_date", "total_leave_days", "leave_type"]
        )
        
        return [{"hours": leave.total_leave_days * 8} for leave in leaves]
        
    except Exception:
        return []

def get_default_holiday_list(company):
    """Get default holiday list for company"""
    try:
        return frappe.get_cached_value("Company", company, "default_holiday_list")
    except Exception:
        return None

def get_capacity_settings(department=None):
    """Get capacity planning settings"""
    return {
        "default_hours_per_day": 8,
        "default_days_per_week": 5,
        "overtime_threshold": 1.2,  # 120% capacity
        "underutilization_threshold": 0.7,  # 70% capacity
        "planning_horizon_days": 30
    }

def is_task_overdue(task):
    """Check if task is overdue"""
    if not task.exp_end_date or task.status == "Completed":
        return False
    
    return getdate(task.exp_end_date) < getdate()

@frappe.whitelist()
def move_task(task_id, assignee_id=None, start_date=None, end_date=None):
    """Move task to different assignee or schedule"""
    if not task_id:
        frappe.throw(_("Task ID is required"))
    
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
        "task": task.as_dict(),
        "message": "Task moved successfully"
    }

@frappe.whitelist()
def get_capacity_analysis(department=None, start_date=None, end_date=None):
    """Get detailed capacity analysis for workload planning"""
    
    workload_data = get_workload_data(department, start_date, end_date)
    
    analysis = {
        "summary": {
            "total_employees": len(workload_data["assignees"]),
            "total_tasks": len(workload_data["tasks"]),
            "scheduled_tasks": len([t for t in workload_data["tasks"] if t["isScheduled"]]),
            "unscheduled_tasks": len([t for t in workload_data["tasks"] if not t["isScheduled"]])
        },
        "capacity_breakdown": [],
        "overallocated_employees": [],
        "underutilized_employees": [],
        "recommendations": []
    }
    
    for assignee in workload_data["assignees"]:
        assignee_tasks = [t for t in workload_data["tasks"] if t["assignee"] == assignee["id"]]
        scheduled_hours = sum(t["duration"] for t in assignee_tasks if t["isScheduled"])
        
        utilization = (scheduled_hours / assignee["capacity"]) * 100 if assignee["capacity"] > 0 else 0
        
        capacity_info = {
            "employee": assignee["name"],
            "employee_id": assignee["id"],
            "capacity": assignee["capacity"],
            "scheduled_hours": scheduled_hours,
            "utilization": utilization,
            "available_hours": max(0, assignee["capacity"] - scheduled_hours),
            "task_count": len(assignee_tasks)
        }
        
        analysis["capacity_breakdown"].append(capacity_info)
        
        # Identify over/under allocated
        if utilization > 120:
            analysis["overallocated_employees"].append(capacity_info)
        elif utilization < 70:
            analysis["underutilized_employees"].append(capacity_info)
    
    # Generate recommendations
    if analysis["overallocated_employees"]:
        analysis["recommendations"].append({
            "type": "overallocation",
            "message": f"{len(analysis['overallocated_employees'])} employees are overallocated",
            "action": "Consider redistributing tasks or extending deadlines"
        })
    
    if analysis["unscheduled_tasks"] > 0:
        analysis["recommendations"].append({
            "type": "unscheduled",
            "message": f"{analysis['summary']['unscheduled_tasks']} tasks need scheduling",
            "action": "Schedule unassigned tasks to available capacity"
        })
    
    return analysis
