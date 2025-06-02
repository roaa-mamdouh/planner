import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class Task(Document):
    def validate(self):
        """Validate task fields"""
        if not self.subject:
            frappe.throw("Task title is required")
            
        if self.exp_start_date and self.exp_end_date:
            if getdate(self.exp_end_date) < getdate(self.exp_start_date):
                frappe.throw("End date cannot be before start date")
                
        if self.expected_time and not isinstance(self.expected_time, (int, float)):
            frappe.throw("Expected time must be a number")
            
        if self.status not in ["Open", "Working", "Completed", "Overdue"]:
            frappe.throw("Invalid task status")
            
        if self.priority not in ["Low", "Medium", "High"]:
            frappe.throw("Invalid task priority")
