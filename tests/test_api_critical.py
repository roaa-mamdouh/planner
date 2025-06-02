import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from planner.services.task_service import TaskService
from planner.services.workload_service import WorkloadService

class TestPlannerAPICritical(FrappeTestCase):
    def setUp(self):
        # Create test data
        self.create_test_data()

    def create_test_data(self):
        # Create test department
        if not frappe.db.exists("Department", "Test Department"):
            frappe.get_doc({
                "doctype": "Department",
                "department_name": "Test Department",
                "company": frappe.defaults.get_defaults().company
            }).insert()

        # Create test employee
        if not frappe.db.exists("Employee", "TEST-EMP-001"):
            frappe.get_doc({
                "doctype": "Employee",
                "employee_name": "Test Employee",
                "first_name": "Test",
                "last_name": "Employee",
                "email": "test.employee@example.com",
                "status": "Active",
                "department": "Test Department",
                "employee_number": "TEST-EMP-001",
                "date_of_birth": "1990-01-01",
                "date_of_joining": "2020-01-01",
                "company": frappe.defaults.get_defaults().company
            }).insert()

        # Create test task
        if not frappe.db.exists("Task", "TEST-TASK-001"):
            frappe.get_doc({
                "doctype": "Task",
                "subject": "Test Task",
                "status": "Open",
                "priority": "Medium",
                "department": "Test Department",
                "_assign": frappe.as_json(["test.employee@example.com"]),
                "exp_start_date": "2023-12-01",
                "exp_end_date": "2023-12-02",
                "expected_time": 16
            }).insert()

    def test_task_crud_operations(self):
        """Test critical task operations"""
        # Get task
        task = TaskService.get_all_tasks(department="Test Department")[0]
        self.assertEqual(task["title"], "Test Task")

        # Update task
        updated_task = TaskService.update_task(
            task["id"],
            {
                "status": "Working",
                "priority": "High"
            }
        )
        self.assertEqual(updated_task["status"], "Working")
        self.assertEqual(updated_task["priority"], "High")

        # Move task
        move_result = TaskService.move_task(
            task["id"],
            "test.employee@example.com",
            "2023-12-03",
            "2023-12-04"
        )
        self.assertTrue(move_result["success"])
        self.assertEqual(move_result["task"]["startDate"], "2023-12-03")

    def test_workload_operations(self):
        """Test critical workload operations"""
        # Get workload data
        workload_data = WorkloadService.get_workload_data(
            department="Test Department",
            start_date="2023-12-01",
            end_date="2023-12-31"
        )

        # Verify assignees
        self.assertTrue(len(workload_data["assignees"]) > 0)
        assignee = next(a for a in workload_data["assignees"] 
                       if a["email"] == "test.employee@example.com")
        self.assertIsNotNone(assignee)

        # Verify tasks
        self.assertTrue(len(workload_data["tasks"]) > 0)
        task = next(t for t in workload_data["tasks"] 
                   if t["assignee"] == "test.employee@example.com")
        self.assertIsNotNone(task)

        # Test capacity calculation
        capacity = WorkloadService.calculate_employee_capacity(
            "test.employee@example.com",
            "2023-12-01",
            "2023-12-31"
        )
        self.assertGreater(capacity["total_capacity"], 0)
        self.assertGreater(capacity["available_capacity"], 0)

    def test_error_handling(self):
        """Test critical error scenarios"""
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

    def test_batch_operations(self):
        """Test batch update operations"""
        task = TaskService.get_all_tasks(department="Test Department")[0]
        
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

    def tearDown(self):
        # Clean up test data
        try:
            frappe.delete_doc("Task", "TEST-TASK-001")
            frappe.delete_doc("Employee", "TEST-EMP-001")
            frappe.delete_doc("Department", "Test Department")
        except Exception:
            pass
        frappe.db.commit()

def run_critical_tests():
    """Run critical path tests"""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPlannerAPICritical)
    runner = unittest.TextTestRunner()
    return runner.run(suite)

if __name__ == '__main__':
    run_critical_tests()
