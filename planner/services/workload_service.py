import frappe
from frappe import _
from frappe.utils import getdate, add_days, date_diff
from .task_service import TaskService

class WorkloadService:
    @staticmethod
    def get_department_employees(department=None):
        """Get all employees in a department with their details"""
        try:
            filters = {"status": "Active"}
            if department:
                # Use department_name field instead of department for filtering
                filters["department_name"] = department
            
            try:
                employees = frappe.get_all(
                    "Employee",
                    filters=filters,
                    fields=[
                        "name", "employee_name", "user_id", "image", 
                        "department_name", "designation", "company"
                    ]
                )
            except Exception as e:
                frappe.logger().error(f"Error getting employees: {str(e)}")
                return [{
                    "id": "unassigned",
                    "name": "Unassigned",
                    "email": "",
                    "image": None,
                    "department": department
                }]
            
            if not employees:
                return [{
                    "id": "unassigned",
                    "name": "Unassigned",
                    "email": "",
                    "image": None,
                    "department": department
                }]
            
            employee_list = []
            for emp in employees:
                try:
                    # Get user details if user_id exists
                    user_info = {}
                    if emp.user_id:
                        try:
                            user_info = frappe.get_cached_value(
                                "User", 
                                emp.user_id, 
                                ["full_name", "user_image", "email"], 
                                as_dict=True
                            ) or {}
                        except Exception as user_error:
                            frappe.logger().error(f"Error getting user info for {emp.user_id}: {str(user_error)}")
                    
                    employee_data = {
                        "id": emp.user_id or emp.name,
                        "employee_id": emp.name,
                        "name": user_info.get("full_name") or emp.employee_name or "Unknown",
                        "email": user_info.get("email") or emp.user_id or "",
                        "image": user_info.get("user_image") or emp.image,
                        "role": emp.designation or "Employee",
                        "department": emp.department_name or department or "Unknown",
                        "company": emp.company
                    }
                    employee_list.append(employee_data)
                except Exception as emp_error:
                    frappe.logger().error(f"Error processing employee {emp.name}: {str(emp_error)}")
                    continue
            
            if not employee_list:
                return [{
                    "id": "unassigned",
                    "name": "Unassigned",
                    "email": "",
                    "image": None,
                    "department": department
                }]
            
            return employee_list
            
        except Exception as e:
            frappe.logger().error(f"Error in get_department_employees: {str(e)}")
            return [{
                "id": "unassigned",
                "name": "Unassigned",
                "email": "",
                "image": None,
                "department": department
            }]

    @staticmethod
    def get_employee_working_hours(employee_id):
        """Get employee working hours from HRMS"""
        try:
            if employee_id == "unassigned":
                # Return default working hours for unassigned
                return {
                    "hours_per_day": 8,
                    "days_per_week": 5,
                    "holiday_list": None,
                    "start_time": "09:00",
                    "end_time": "17:00"
                }
            employee = frappe.get_doc("Employee", {"user_id": employee_id})
            holiday_list = employee.holiday_list or WorkloadService.get_default_holiday_list(employee.company)
            
            return {
                "hours_per_day": 8,
                "days_per_week": 5,
                "holiday_list": holiday_list,
                "start_time": "09:00",
                "end_time": "17:00"
            }
        except Exception as e:
            frappe.logger().error(f"Error getting working hours for {employee_id}: {str(e)}")
            return {
                "hours_per_day": 8,
                "days_per_week": 5,
                "holiday_list": None,
                "start_time": "09:00",
                "end_time": "17:00"
            }

    @staticmethod
    def get_working_days(employee_id, start_date, end_date):
        """Calculate working days excluding weekends and holidays"""
        try:
            # Handle case when dates are None
            if not start_date or not end_date:
                return 0

            # Convert string dates to datetime if needed
            if isinstance(start_date, str):
                start_date = getdate(start_date)
            if isinstance(end_date, str):
                end_date = getdate(end_date)

            # Skip holiday calculation for unassigned
            if employee_id == "unassigned":
                total_days = date_diff(end_date, start_date) + 1
                weeks = total_days // 7
                remaining_days = total_days % 7
                
                weekend_days = 0
                current_date = start_date
                for i in range(remaining_days):
                    if current_date.weekday() >= 5:
                        weekend_days += 1
                    current_date = add_days(current_date, 1)
                
                return total_days - (weeks * 2) - weekend_days

            # For assigned employees, include holiday calculation
            try:
                from hrms.hr.utils import get_holidays_for_employee
            except ImportError:
                get_holidays_for_employee = None
            
            holiday_dates = []
            if get_holidays_for_employee:
                holidays = get_holidays_for_employee(employee_id, start_date, end_date)
                holiday_dates = [holiday.holiday_date for holiday in holidays]
            
            working_days = 0
            current_date = start_date
            
            while current_date <= end_date:
                if current_date.weekday() < 5 and current_date not in holiday_dates:
                    working_days += 1
                current_date = add_days(current_date, 1)
            
            return working_days
            
        except Exception as e:
            frappe.logger().error(f"Error calculating working days: {str(e)}")
            return 0  # Return 0 working days on error instead of trying fallback calculation

    @staticmethod
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
            
        except Exception as e:
            frappe.logger().error(f"Error getting employee leaves: {str(e)}")
            return []

    @staticmethod
    def calculate_employee_capacity(employee_id, start_date=None, end_date=None):
        """Calculate employee capacity and availability"""
        working_hours = WorkloadService.get_employee_working_hours(employee_id)
        
        if not start_date:
            start_date = getdate()
        if not end_date:
            end_date = add_days(start_date, 30)
        
        start_date = getdate(start_date)
        end_date = getdate(end_date)
        
        working_days = WorkloadService.get_working_days(employee_id, start_date, end_date)
        daily_hours = working_hours.get("hours_per_day", 8)
        total_capacity = working_days * daily_hours
        
        leaves = WorkloadService.get_employee_leaves(employee_id, start_date, end_date)
        leave_hours = sum(leave.get("hours", daily_hours) for leave in leaves)
        
        available_capacity = total_capacity - leave_hours
        
        return {
            "total_capacity": total_capacity,
            "available_capacity": available_capacity,
            "working_hours": working_hours,
            "working_days": working_days,
            "leave_hours": leave_hours,
            "availability": (available_capacity / total_capacity * 100) if total_capacity > 0 else 0
        }

    @staticmethod
    def get_workload_data(department=None, start_date=None, end_date=None):
        """Get comprehensive workload data for planning"""
        try:
            # Debug logging for department filter
            frappe.logger().info(f"get_workload_data: Requested department: {department}")

            # Check if department exists
            if department and not frappe.db.exists("Department", department):
                frappe.logger().warning(f"get_workload_data: Department {department} not found")
                # Return empty workload data for invalid department
                return {
                    "assignees": [],
                    "tasks": [],
                    "capacity_settings": WorkloadService.get_capacity_settings(department)
                }

            employees = WorkloadService.get_department_employees(department)
            frappe.logger().info(f"get_workload_data: Found {len(employees)} employees")

            if not employees:
                employees = [{
                    "id": "unassigned",
                    "name": "Unassigned",
                    "email": "",
                    "image": None,
                    "department": department
                }]
            
            tasks = TaskService.get_all_tasks(department, start_date, end_date)
            frappe.logger().info(f"get_workload_data: Found {len(tasks)} tasks")
            
            workload_data = {
                "assignees": [],
                "tasks": tasks,
                "capacity_settings": WorkloadService.get_capacity_settings(department)
            }
        
            for employee in employees:
                capacity_info = WorkloadService.calculate_employee_capacity(
                    employee["id"], 
                    start_date, 
                    end_date
                )
                
                assignee_data = {
                    "id": employee["id"],
                    "name": employee["name"],
                    "email": employee.get("email", ""),
                    "image": employee.get("image"),
                    "role": employee.get("role", "Employee"),
                    "department": employee.get("department"),
                    "capacity": capacity_info["total_capacity"],
                    "working_hours": capacity_info["working_hours"],
                    "availability": capacity_info["availability"]
                }
                
                workload_data["assignees"].append(assignee_data)
            
            return workload_data
            
        except Exception as e:
            frappe.logger().error(f"Error in get_workload_data: {str(e)}")
            # Return empty data structure instead of throwing error
            return {
                "assignees": [],
                "tasks": [],
                "capacity_settings": WorkloadService.get_capacity_settings(department)
            }

    @staticmethod
    def get_capacity_settings(department=None):
        """Get capacity planning settings"""
        return {
            "default_hours_per_day": 8,
            "default_days_per_week": 5,
            "overtime_threshold": 1.2,  # 120% capacity
            "underutilization_threshold": 0.7,  # 70% capacity
            "planning_horizon_days": 30
        }

    @staticmethod
    def get_default_holiday_list(company):
        """Get default holiday list for company"""
        try:
            return frappe.get_cached_value("Company", company, "default_holiday_list")
        except Exception:
            return None

    @staticmethod
    def get_capacity_analysis(department=None, start_date=None, end_date=None):
        """Get detailed capacity analysis for workload planning"""
        workload_data = WorkloadService.get_workload_data(department, start_date, end_date)
        
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
