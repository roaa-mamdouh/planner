# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_days
from datetime import datetime, timedelta


class WorkloadCapacity(Document):
	def validate(self):
		"""Validate workload capacity data"""
		self.validate_date()
		self.calculate_utilization()
		self.validate_capacity_limits()
	
	def validate_date(self):
		"""Ensure date is not in the past (optional validation)"""
		if self.date and getdate(self.date) < getdate():
			# Allow past dates for historical data
			pass
	
	def calculate_utilization(self):
		"""Calculate utilization percentage"""
		if self.available_hours and self.available_hours > 0:
			self.utilization_percent = (flt(self.allocated_hours) / flt(self.available_hours)) * 100
		else:
			self.utilization_percent = 0
	
	def validate_capacity_limits(self):
		"""Validate capacity constraints"""
		if flt(self.allocated_hours) < 0:
			frappe.throw("Allocated hours cannot be negative")
		
		if flt(self.available_hours) < 0:
			frappe.throw("Available hours cannot be negative")
		
		if flt(self.overtime_hours) < 0:
			frappe.throw("Overtime hours cannot be negative")
		
		if flt(self.efficiency_rating) <= 0:
			frappe.throw("Efficiency rating must be greater than 0")
	
	def before_save(self):
		"""Actions before saving the document"""
		self.calculate_utilization()
	
	def after_insert(self):
		"""Actions after inserting new capacity record"""
		self.update_employee_workload_cache()
	
	def on_update(self):
		"""Actions after updating capacity record"""
		self.update_employee_workload_cache()
		self.emit_capacity_change_event()
	
	def update_employee_workload_cache(self):
		"""Update cached workload data for the employee"""
		try:
			# Clear relevant cache entries
			cache_keys = [
				f"workload_data_{self.employee}",
				f"employee_capacity_{self.employee}_{self.date}",
				"workload_data_global"
			]
			
			for key in cache_keys:
				frappe.cache().delete_value(key)
				
		except Exception as e:
			frappe.log_error(f"Failed to update workload cache: {str(e)}")
	
	def emit_capacity_change_event(self):
		"""Emit real-time event for capacity changes"""
		try:
			from planner.realtime_v2 import emit_capacity_change
			
			capacity_data = {
				'employee': self.employee,
				'date': str(self.date),
				'available_hours': self.available_hours,
				'allocated_hours': self.allocated_hours,
				'utilization_percent': self.utilization_percent,
				'is_holiday': self.is_holiday,
				'is_leave': self.is_leave
			}
			
			emit_capacity_change(self.employee, capacity_data)
			
		except Exception as e:
			frappe.log_error(f"Failed to emit capacity change event: {str(e)}")


@frappe.whitelist()
def get_employee_capacity(employee, start_date, end_date):
	"""Get employee capacity for a date range"""
	
	capacity_data = frappe.get_all(
		'Workload Capacity',
		filters={
			'employee': employee,
			'date': ['between', [start_date, end_date]]
		},
		fields=[
			'date', 'available_hours', 'allocated_hours', 
			'utilization_percent', 'is_holiday', 'is_leave',
			'overtime_hours', 'efficiency_rating'
		],
		order_by='date'
	)
	
	return capacity_data


@frappe.whitelist()
def initialize_employee_capacity(employee, start_date, end_date, available_hours=8.0):
	"""Initialize capacity records for an employee over a date range"""
	
	if not employee or not start_date or not end_date:
		frappe.throw("Employee, start date, and end date are required")
	
	current_date = getdate(start_date)
	end_date = getdate(end_date)
	created_records = []
	
	while current_date <= end_date:
		# Check if record already exists
		existing = frappe.db.exists('Workload Capacity', {
			'employee': employee,
			'date': current_date
		})
		
		if not existing:
			# Check if it's a weekend (Saturday = 5, Sunday = 6)
			is_weekend = current_date.weekday() >= 5
			
			# Check if it's a holiday
			is_holiday = is_company_holiday(current_date)
			
			capacity_doc = frappe.get_doc({
				'doctype': 'Workload Capacity',
				'employee': employee,
				'date': current_date,
				'available_hours': 0 if (is_weekend or is_holiday) else available_hours,
				'allocated_hours': 0,
				'is_holiday': is_holiday,
				'is_leave': False,
				'efficiency_rating': 1.0
			})
			
			capacity_doc.insert()
			created_records.append(capacity_doc.name)
		
		current_date = add_days(current_date, 1)
	
	return {
		'message': f'Created {len(created_records)} capacity records',
		'records': created_records
	}


@frappe.whitelist()
def bulk_update_capacity(updates):
	"""Bulk update capacity records"""
	
	if isinstance(updates, str):
		import json
		updates = json.loads(updates)
	
	updated_records = []
	
	try:
		for update in updates:
			capacity_name = update.get('name')
			changes = update.get('changes', {})
			
			if not capacity_name:
				continue
			
			capacity_doc = frappe.get_doc('Workload Capacity', capacity_name)
			
			for field, value in changes.items():
				if hasattr(capacity_doc, field):
					setattr(capacity_doc, field, value)
			
			capacity_doc.save()
			updated_records.append(capacity_doc.as_dict())
		
		return {
			'updated_count': len(updated_records),
			'records': updated_records
		}
		
	except Exception as e:
		frappe.log_error(f"Bulk capacity update error: {str(e)}")
		frappe.throw(f"Failed to update capacity records: {str(e)}")


def is_company_holiday(date):
	"""Check if a date is a company holiday"""
	try:
		# Get default company
		company = frappe.defaults.get_user_default("Company")
		
		if not company:
			return False
		
		# Check holiday list
		holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")
		
		if not holiday_list:
			return False
		
		holiday = frappe.db.exists("Holiday", {
			"parent": holiday_list,
			"holiday_date": date
		})
		
		return bool(holiday)
		
	except Exception:
		return False


@frappe.whitelist()
def get_capacity_analytics(department=None, start_date=None, end_date=None):
	"""Get capacity analytics for dashboard"""
	
	filters = {}
	
	if start_date and end_date:
		filters['date'] = ['between', [start_date, end_date]]
	
	# Build query with employee filter if department specified
	if department:
		employees = frappe.get_all(
			'Employee',
			filters={'department': department, 'status': 'Active'},
			fields=['user_id']
		)
		employee_ids = [emp.user_id for emp in employees if emp.user_id]
		
		if employee_ids:
			filters['employee'] = ['in', employee_ids]
		else:
			return {'message': 'No active employees found in department'}
	
	# Get capacity data
	capacity_data = frappe.get_all(
		'Workload Capacity',
		filters=filters,
		fields=[
			'employee', 'date', 'available_hours', 'allocated_hours',
			'utilization_percent', 'is_holiday', 'is_leave'
		]
	)
	
	# Calculate analytics
	total_available = sum(c['available_hours'] for c in capacity_data)
	total_allocated = sum(c['allocated_hours'] for c in capacity_data)
	
	# Group by employee
	employee_stats = {}
	for record in capacity_data:
		emp = record['employee']
		if emp not in employee_stats:
			employee_stats[emp] = {
				'available_hours': 0,
				'allocated_hours': 0,
				'working_days': 0,
				'holiday_days': 0,
				'leave_days': 0
			}
		
		employee_stats[emp]['available_hours'] += record['available_hours']
		employee_stats[emp]['allocated_hours'] += record['allocated_hours']
		
		if record['is_holiday']:
			employee_stats[emp]['holiday_days'] += 1
		elif record['is_leave']:
			employee_stats[emp]['leave_days'] += 1
		else:
			employee_stats[emp]['working_days'] += 1
	
	# Calculate utilization for each employee
	for emp_id, stats in employee_stats.items():
		if stats['available_hours'] > 0:
			stats['utilization'] = (stats['allocated_hours'] / stats['available_hours']) * 100
		else:
			stats['utilization'] = 0
	
	return {
		'summary': {
			'total_available_hours': total_available,
			'total_allocated_hours': total_allocated,
			'overall_utilization': (total_allocated / total_available * 100) if total_available > 0 else 0,
			'total_employees': len(employee_stats)
		},
		'employee_stats': employee_stats,
		'overallocated_employees': [
			emp for emp, stats in employee_stats.items() 
			if stats['utilization'] > 100
		],
		'underutilized_employees': [
			emp for emp, stats in employee_stats.items() 
			if stats['utilization'] < 70 and stats['utilization'] > 0
		]
	}
