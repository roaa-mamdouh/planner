from frappe.model.document import Document

class Task(Document):
    """
    Task DocType model with field definitions and validation.
    """
    def validate(self):
        # Add custom validation logic here
        if not self.subject:
            frappe.throw("Task title is required")
        if self.exp_start_date and self.exp_end_date:
            if self.exp_end_date < self.exp_start_date:
                frappe.throw("End date must be after start date")
