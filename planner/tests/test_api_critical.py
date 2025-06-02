import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from planner.services.task_service import TaskService
from planner.services.workload_service import WorkloadService

class TestPlannerBase(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure we're in test mode
        frappe.flags.in_test = True
        
        # Clear test data at the start
        cls.clear_test_data()

    @classmethod
    def clear_test_data(cls):
        """Clear any existing test data"""
        try:
            frappe.db.sql("""DELETE FROM `tabTask` WHERE name = 'TEST-TASK-001'""")
            frappe.db.sql("""DELETE FROM `tabEmployee` WHERE employee_number = 'TEST-EMP-001'""")
            frappe.db.sql("""DELETE FROM `tabDepartment` WHERE name LIKE 'Test Department%'""")
            frappe.db.sql("""DELETE FROM `tabUser` WHERE name = 'test.employee@example.com'""")
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()

class TestPlannerAPICritical(TestPlannerBase):
    def setUp(self):
        """Create test data before each test"""
        self.create_test_data()

    def create_test_data(self):
        try:
            # Create test user first
            if not frappe.db.exists("User", "test.employee@example.com"):
                user = frappe.new_doc("User")
                user.email = "test.employee@example.com"
                user.first_name = "Test"
                user.last_name = "Employee"
                user.send_welcome_email = 0
                user.enabled = 1
                user.new_password = "test@123"
                user.insert()

            # Create test department
            if not frappe.db.exists("Department", {"department_name": "Test Department"}):
                dept = frappe.new_doc("Department")
                dept.department_name = "Test Department"
                dept.insert()
                frappe.db.commit()  # Commit to ensure Department exists

            # Retrieve actual department name for linking
            dept_name = frappe.db.get_value("Department", {"department_name": "Test Department"})
            if not dept_name:
                raise Exception("Failed to create Test Department")

            # Create test employee with all required fields
            if not frappe.db.exists("Employee", {"employee_number": "TEST-EMP-001"}):
                emp = frappe.new_doc("Employee")
                emp.employee_name = "Test Employee"
                emp.first_name = "Test"
                emp.last_name = "Employee"
                emp.email = "test.employee@example.com"
                emp.status = "Active"
                emp.gender = "Male"  # Required field
                emp.date_of_birth = "1990-01-01"
                emp.date_of_joining = "2020-01-01"
                emp.department = dept_name
                emp.employee_number = "TEST-EMP-001"
                emp.user_id = "test.employee@example.com"
                emp.company = frappe.defaults.get_defaults().company or "_Test Company"
                emp.reports_to = ""  # Set to empty string if no reporting manager
                emp.leave_approver = ""  # Set to empty string if no leave approver
                emp.expense_approver = ""  # Set to empty string if no expense approver
                emp.insert()

            # Create test task
            if not frappe.db.exists("Task", "TEST-TASK-001"):
                task = frappe.new_doc("Task")
                task.name = "TEST-TASK-001"
                task.subject = "Test Task"
                task.status = "Open"
                task.priority = "Medium"
                task.department = dept_name
                task._assign = frappe.as_json(["test.employee@example.com"])
                task.exp_start_date = "2023-12-01"
                task.exp_end_date = "2023-12-02"
                task.expected_time = 16
                task.insert()

            frappe.db.commit()

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error creating test data: {str(e)}")
            raise

    def test_task_crud_operations(self):
        """Test critical task operations"""
        try:
            # Get task
            tasks = TaskService.get_all_tasks(department="Test Department")
            self.assertTrue(len(tasks) > 0, "No tasks found")
            task = tasks[0]
            self.assertEqual(task["title"], "Test Task")

            # Update task
            # Reload the task document to avoid TimestampMismatchError
            task_doc = frappe.get_doc("Task", task["id"])
            task_doc.status = "Working"
            task_doc.priority = "High"
            task_doc.save()

            # Reload task to verify update
            updated_task_doc = frappe.get_doc("Task", task["id"])
            self.assertEqual(updated_task_doc.status, "Working")
            self.assertEqual(updated_task_doc.priority, "High")

            # Move task
            move_result = TaskService.move_task(
                task["id"],
                "test.employee@example.com",
                "2023-12-03",
                "2023-12-04"
            )
            self.assertTrue(move_result["success"])
            # Compare date objects for startDate
            from datetime import datetime, date
            start_date = move_result["task"]["startDate"]
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            self.assertEqual(start_date, date(2023, 12, 3))

        except Exception as e:
            frappe.log_error(f"Error in test_task_crud_operations: {str(e)}")
            raise

    def test_workload_operations(self):
        """Test critical workload operations"""
        try:
            # Get workload data
            workload_data = WorkloadService.get_workload_data(
                department="Test Department",
                start_date="2023-12-01",
                end_date="2023-12-31"
            )

            # Verify assignees
            self.assertTrue(len(workload_data["assignees"]) > 0)
            assignee = next(
                (a for a in workload_data["assignees"] 
                 if a["email"] == "test.employee@example.com"),
                None
            )
            self.assertIsNotNone(assignee, "Test employee not found in assignees")

            # Verify tasks
            self.assertTrue(len(workload_data["tasks"]) > 0)
            task = next(
                (t for t in workload_data["tasks"] 
                 if t["assignee"] == "test.employee@example.com"),
                None
            )
            self.assertIsNotNone(task, "Test task not found")

            # Test capacity calculation
            capacity = WorkloadService.calculate_employee_capacity(
                "test.employee@example.com",
                "2023-12-01",
                "2023-12-31"
            )
            self.assertGreater(capacity["total_capacity"], 0)
            self.assertGreater(capacity["available_capacity"], 0)

        except Exception as e:
            frappe.log_error(f"Error in test_workload_operations: {str(e)}")
            raise

    def test_error_handling(self):
        """Test critical error scenarios"""
        from planner.api import handle_api_error

        # Test invalid task update
        with self.assertRaises(frappe.ValidationError):
            TaskService.update_task(
                "INVALID-TASK",
                {"status": "Working"}
            )

        # Test invalid task move
        with self.assertRaises(frappe.ValidationError):
            TaskService.move_task(
                "INVALID-TASK",
                "invalid.user@example.com",
                "2023-12-01",
                "2023-12-02"
            )

        # Test invalid department
        workload_data = WorkloadService.get_workload_data(
            department="Invalid Department"
        )
        self.assertEqual(len(workload_data["assignees"]), 0)
        self.assertEqual(len(workload_data["tasks"]), 0)

        # Test error response format
        try:
            raise frappe.ValidationError("Test validation error")
        except Exception as e:
            error_response = handle_api_error(e, "Test Error")
            self.assertEqual(error_response["exc_type"], "ValidationError")
            self.assertEqual(error_response["_error_message"], "Test validation error")
            self.assertTrue("traceback" in error_response)

        # Test attribute error handling
        try:
            raise AttributeError("Test attribute error")
        except Exception as e:
            error_response = handle_api_error(e, "Test Error")
            self.assertEqual(error_response["exc_type"], "AttributeError")
            self.assertEqual(error_response["_error_message"], "Test attribute error")

        # Test generic error handling
        try:
            raise Exception("Test generic error")
        except Exception as e:
            error_response = handle_api_error(e, "Test Error")
            self.assertEqual(error_response["exc_type"], "Exception")
            self.assertEqual(error_response["_error_message"], "Test generic error")

    def test_batch_operations(self):
        """Test batch update operations"""
        try:
            tasks = TaskService.get_all_tasks(department="Test Department")
            self.assertTrue(len(tasks) > 0, "No tasks found")
            task = tasks[0]
            
            # Batch update tasks
            updates = [{
                "task_id": task["id"],
                "changes": {
                    "status": "Working",
                    "priority": "High"
                }
            }]
            
            result = TaskService.batch_update_tasks(updates)
            self.assertTrue(len(result) > 0)
            self.assertEqual(result[0]["status"], "Working")
            self.assertEqual(result[0]["priority"], "High")

        except Exception as e:
            frappe.log_error(f"Error in test_batch_operations: {str(e)}")
            raise

    def tearDown(self):
        """Clean up test data after each test"""
        try:
            self.clear_test_data()
        except Exception as e:
            frappe.log_error(f"Error in tearDown: {str(e)}")
            raise

def run_critical_tests():
    """Run critical path tests"""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPlannerAPICritical)
    runner = unittest.TextTestRunner()
    return runner.run(suite)

if __name__ == '__main__':
    run_critical_tests()
