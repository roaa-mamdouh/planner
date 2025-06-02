import frappe
from frappe import _
from frappe.utils import getdate, add_days, date_diff
from .task_service import TaskService

class WorkloadService:
    @staticmethod
    def get_department_employees(department=None):
        """Get all employees in a department with their details"""
        try:
            # Get only active employees with specific fields
            query = """
                SELECT 
                    name, employee_name, user_id, image,
                    department, designation, company
                FROM `tabEmployee`
                WHERE status = 'Active'
                AND user_id IS NOT NULL
            """
            
            if department:
                query += " AND department = %(department)s"
            
            employees = frappe.db.sql(query, {"department": department}, as_dict=True)
            
            if not employees:
                frappe.logger().warning(f"No active employees found for department: {department}")
                return []
            
            employee_list = []
            for emp in employees:
                try:
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
            
            return employee_list
            
        except Exception as e:
            frappe.logger().error(f"Error in get_department_employees: {str(e)}")
            return []

    @staticmethod
    def _get_unassigned_employee(department=None):
        """Helper method to create unassigned employee entry"""
        return {
            "id": "unassigned",
            "employee_id": "unassigned",
            "name": "Unassigned",
            "email": "",
            "image": None,
            "role": "Unassigned",
            "department": department or "Unknown",
            "company": None
        }

    @staticmethod
    def get_working_days(employee_id, start_date, end_date):
        """Calculate working days excluding weekends and holidays"""
        try:
            if not start_date or not end_date:
                return 0

            start_date = getdate(start_date)
            end_date = getdate(end_date)

            # Basic working days calculation (excluding weekends)
            total_days = date_diff(end_date, start_date) + 1
            working_days = 0
            current_date = start_date
            
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                    working_days += 1
                current_date = add_days(current_date, 1)
            
            # For assigned employees, subtract holidays if available
            if employee_id != "unassigned":
                try:
                    # Try to get holidays if HRMS is available
                    from hrms.hr.utils import get_holidays_for_employee
                    holidays = get_holidays_for_employee(employee_id, start_date, end_date)
                    holiday_count = len([h for h in holidays if getdate(h.holiday_date).weekday() < 5])
                    working_days -= holiday_count
                except (ImportError, Exception):
                    # HRMS not available or error getting holidays
                    pass
            
            return max(0, working_days)
            
        except Exception as e:
            frappe.logger().error(f"Error calculating working days: {str(e)}")
            return 0

    @staticmethod
    def calculate_employee_capacity(employee_id, start_date=None, end_date=None):
        """Calculate employee capacity and availability"""
        try:
            if not start_date:
                start_date = getdate()
            if not end_date:
                end_date = add_days(start_date, 30)
            
            start_date = getdate(start_date)
            end_date = getdate(end_date)
            
            working_days = WorkloadService.get_working_days(employee_id, start_date, end_date)
            daily_hours = 8  # Standard 8 hours per day
            total_capacity = working_days * daily_hours
            
            # Get leave hours if employee is not unassigned
            leave_hours = 0
            if employee_id != "unassigned":
                try:
                    leaves = frappe.get_all(
                        "Leave Application",
                        filters={
                            "employee": {"in": frappe.get_all("Employee", {"user_id": employee_id}, "name")},
                            "status": "Approved",
                            "from_date": ["<=", end_date],
                            "to_date": [">=", start_date]
                        },
                        fields=["total_leave_days"]
                    )
                    leave_hours = sum(leave.total_leave_days * daily_hours for leave in leaves)
                except Exception:
                    pass
            
            available_capacity = max(0, total_capacity - leave_hours)
            
            return {
                "total_capacity": total_capacity,
                "available_capacity": available_capacity,
                "working_days": working_days,
                "leave_hours": leave_hours,
                "availability": (available_capacity / total_capacity * 100) if total_capacity > 0 else 0
            }
            
        except Exception as e:
            frappe.logger().error(f"Error calculating capacity for {employee_id}: {str(e)}")
            return {
                "total_capacity": 0,
                "available_capacity": 0,
                "working_days": 0,
                "leave_hours": 0,
                "availability": 0
            }

    @staticmethod
    def get_workload_data(department=None, start_date=None, end_date=None):
        """Get comprehensive workload data for planning"""
        try:
            frappe.logger().info(f"Getting workload data for department: {department}")

            # Validate department exists if specified
            if department and not frappe.db.exists("Department", department):
                frappe.logger().warning(f"Department {department} not found")
                return WorkloadService._get_empty_workload_data(department)

            # Get employees and tasks
            employees = WorkloadService.get_department_employees(department)
            tasks = TaskService.get_all_tasks(department, start_date, end_date)
            
            frappe.logger().info(f"Found {len(employees)} employees and {len(tasks)} tasks")
            
            # Process assignees with capacity information
            assignees = []
            for employee in employees:
                capacity_info = WorkloadService.calculate_employee_capacity(
                    employee["id"], start_date, end_date
                )
                
                assignee_data = {
                    **employee,
                    "capacity": capacity_info["available_capacity"],
                    "total_capacity": capacity_info["total_capacity"],
                    "working_hours": {
                        "hours_per_day": 8,
                        "days_per_week": 5,
                        "start_time": "09:00",
                        "end_time": "17:00"
                    },
                    "availability": capacity_info["availability"]
                }
                assignees.append(assignee_data)
            
            return {
                "assignees": assignees,
                "tasks": tasks,
                "capacity_settings": WorkloadService.get_capacity_settings()
            }
            
        except Exception as e:
            frappe.logger().error(f"Error in get_workload_data: {str(e)}")
            return WorkloadService._get_empty_workload_data(department)

    @staticmethod
    def _get_empty_workload_data(department=None):
        """Helper method to return empty workload data structure"""
        return {
            "assignees": [],
            "tasks": [],
            "capacity_settings": WorkloadService.get_capacity_settings()
        }

    @staticmethod
    def get_capacity_settings():
        """Get capacity planning settings"""
        return {
            "default_hours_per_day": 8,
            "default_days_per_week": 5,
            "overtime_threshold": 1.2,
            "underutilization_threshold": 0.7,
            "planning_horizon_days": 30
        }

    @staticmethod
    def get_capacity_analysis(department=None, start_date=None, end_date=None):
        """Get detailed capacity analysis for workload planning"""
        try:
            workload_data = WorkloadService.get_workload_data(department, start_date, end_date)
            
            total_employees = len([a for a in workload_data["assignees"] if a["id"] != "unassigned"])
            scheduled_tasks = [t for t in workload_data["tasks"] if t.get("isScheduled")]
            unscheduled_tasks = [t for t in workload_data["tasks"] if not t.get("isScheduled")]
            
            analysis = {
                "summary": {
                    "total_employees": total_employees,
                    "total_tasks": len(workload_data["tasks"]),
                    "scheduled_tasks": len(scheduled_tasks),
                    "unscheduled_tasks": len(unscheduled_tasks)
                },
                "capacity_breakdown": [],
                "overallocated_employees": [],
                "underutilized_employees": [],
                "recommendations": []
            }
            
            # Analyze each assignee
            for assignee in workload_data["assignees"]:
                if assignee["id"] == "unassigned":
                    continue
                    
                assignee_tasks = [t for t in scheduled_tasks if t.get("assignee") == assignee["id"]]
                scheduled_hours = sum(float(t.get("duration", 0)) for t in assignee_tasks)
                
                capacity = assignee.get("capacity", 0)
                utilization = (scheduled_hours / capacity * 100) if capacity > 0 else 0
                
                capacity_info = {
                    "employee": assignee["name"],
                    "employee_id": assignee["id"],
                    "capacity": capacity,
                    "scheduled_hours": scheduled_hours,
                    "utilization": round(utilization, 1),
                    "available_hours": max(0, capacity - scheduled_hours),
                    "task_count": len(assignee_tasks)
                }
                
                analysis["capacity_breakdown"].append(capacity_info)
                
                # Categorize employees
                if utilization > 120:
                    analysis["overallocated_employees"].append(capacity_info)
                elif utilization < 70 and utilization > 0:
                    analysis["underutilized_employees"].append(capacity_info)
            
            # Generate recommendations
            if analysis["overallocated_employees"]:
                analysis["recommendations"].append({
                    "type": "overallocation",
                    "message": f"{len(analysis['overallocated_employees'])} employees are overallocated",
                    "action": "Consider redistributing tasks or extending deadlines"
                })
            
            if analysis["summary"]["unscheduled_tasks"] > 0:
                analysis["recommendations"].append({
                    "type": "unscheduled",
                    "message": f"{analysis['summary']['unscheduled_tasks']} tasks need scheduling",
                    "action": "Schedule unassigned tasks to available capacity"
                })
            
            return analysis
            
        except Exception as e:
            frappe.logger().error(f"Error in get_capacity_analysis: {str(e)}")
            return {
                "summary": {"total_employees": 0, "total_tasks": 0, "scheduled_tasks": 0, "unscheduled_tasks": 0},
                "capacity_breakdown": [],
                "overallocated_employees": [],
                "underutilized_employees": [],
                "recommendations": []
            }