# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, date_diff, now_datetime
import json
from datetime import datetime, timedelta


class TaskTimeline(Document):
	def validate(self):
		"""Validate task timeline data"""
		self.validate_dates()
		self.validate_hours()
		self.validate_dependencies()
		self.sync_with_task()
	
	def validate_dates(self):
		"""Validate start and end dates"""
		if self.start_date and self.end_date:
			if get_datetime(self.start_date) >= get_datetime(self.end_date):
				frappe.throw("End date must be after start date")
	
	def validate_hours(self):
		"""Validate hour fields"""
		if flt(self.estimated_hours) < 0:
			frappe.throw("Estimated hours cannot be negative")
		
		if flt(self.actual_hours) < 0:
			frappe.throw("Actual hours cannot be negative")
		
		if flt(self.progress_percent) < 0 or flt(self.progress_percent) > 100:
			frappe.throw("Progress percentage must be between 0 and 100")
	
	def validate_dependencies(self):
		"""Validate task dependencies"""
		if self.dependencies:
			try:
				if isinstance(self.dependencies, str):
					dependencies = json.loads(self.dependencies)
				else:
					dependencies = self.dependencies
				
				if isinstance(dependencies, list):
					# Validate that dependent tasks exist
					for dep_task in dependencies:
						if not frappe.db.exists('Task', dep_task):
							frappe.throw(f"Dependent task {dep_task} does not exist")
				
			except (json.JSONDecodeError, TypeError):
				frappe.throw("Dependencies must be a valid JSON array")
	
	def sync_with_task(self):
		"""Sync timeline data with the main Task document"""
		if self.task:
			task_doc = frappe.get_doc('Task', self.task)
			
			# Update task with timeline information
			task_doc.exp_start_date = self.start_date
			task_doc.exp_end_date = self.end_date
			task_doc.expected_time = self.estimated_hours
			
			# Update assignee if changed
			if self.assignee:
				task_doc._assign = json.dumps([self.assignee])
			
			# Save without triggering validation loops
			task_doc.flags.ignore_timeline_sync = True
			task_doc.save()
	
	def before_save(self):
		"""Actions before saving the document"""
		self.calculate_duration()
		self.update_priority_score()
	
	def calculate_duration(self):
		"""Calculate task duration in days"""
		if self.start_date and self.end_date:
			self.duration_days = date_diff(self.end_date, self.start_date) + 1
	
	def update_priority_score(self):
		"""Update priority score based on task priority"""
		if self.task:
			task_doc = frappe.get_doc('Task', self.task)
			priority_mapping = {
				'Low': 25,
				'Medium': 50,
				'High': 75,
				'Urgent': 100
			}
			self.priority_score = priority_mapping.get(task_doc.priority, 50)
	
	def after_insert(self):
		"""Actions after inserting new timeline"""
		self.update_capacity_allocation()
		self.emit_timeline_event('timeline_created')
	
	def on_update(self):
		"""Actions after updating timeline"""
		self.update_capacity_allocation()
		self.emit_timeline_event('timeline_updated')
	
	def on_trash(self):
		"""Actions before deleting timeline"""
		self.clear_capacity_allocation()
		self.emit_timeline_event('timeline_deleted')
	
	def update_capacity_allocation(self):
		"""Update capacity allocation for the assignee"""
		if not self.assignee or not self.start_date or not self.end_date:
			return
		
		try:
			# Calculate daily allocation
			total_days = date_diff(self.end_date, self.start_date) + 1
			daily_hours = flt(self.estimated_hours) / total_days if total_days > 0 else 0
			
			# Update capacity for each day in the range
			current_date = get_datetime(self.start_date).date()
			end_date = get_datetime(self.end_date).date()
			
			while current_date <= end_date:
				# Get or create capacity record
				capacity_name = frappe.db.exists('Workload Capacity', {
					'employee': self.assignee,
					'date': current_date
				})
				
				if capacity_name:
					capacity_doc = frappe.get_doc('Workload Capacity', capacity_name)
				else:
					# Create new capacity record
					capacity_doc = frappe.get_doc({
						'doctype': 'Workload Capacity',
						'employee': self.assignee,
						'date': current_date,
						'available_hours': 8.0,  # Default 8 hours
						'allocated_hours': 0.0
					})
					capacity_doc.insert()
				
				# Update allocated hours (this is simplified - in production you'd need to handle overlapping tasks)
				capacity_doc.allocated_hours = flt(capacity_doc.allocated_hours) + daily_hours
				capacity_doc.save()
				
				current_date += timedelta(days=1)
				
		except Exception as e:
			frappe.log_error(f"Failed to update capacity allocation: {str(e)}")
	
	def clear_capacity_allocation(self):
		"""Clear capacity allocation when timeline is deleted"""
		if not self.assignee or not self.start_date or not self.end_date:
			return
		
		try:
			# Calculate daily allocation to remove
			total_days = date_diff(self.end_date, self.start_date) + 1
			daily_hours = flt(self.estimated_hours) / total_days if total_days > 0 else 0
			
			# Remove allocation for each day in the range
			current_date = get_datetime(self.start_date).date()
			end_date = get_datetime(self.end_date).date()
			
			while current_date <= end_date:
				capacity_name = frappe.db.exists('Workload Capacity', {
					'employee': self.assignee,
					'date': current_date
				})
				
				if capacity_name:
					capacity_doc = frappe.get_doc('Workload Capacity', capacity_name)
					capacity_doc.allocated_hours = max(0, flt(capacity_doc.allocated_hours) - daily_hours)
					capacity_doc.save()
				
				current_date += timedelta(days=1)
				
		except Exception as e:
			frappe.log_error(f"Failed to clear capacity allocation: {str(e)}")
	
	def emit_timeline_event(self, event_type):
		"""Emit real-time event for timeline changes"""
		try:
			from planner.realtime_v2 import emit_task_update_v2
			
			if self.task:
				task_doc = frappe.get_doc('Task', self.task)
				emit_task_update_v2(task_doc, self, event_type)
				
		except Exception as e:
			frappe.log_error(f"Failed to emit timeline event: {str(e)}")


@frappe.whitelist()
def get_task_timeline(task_id):
	"""Get timeline data for a specific task"""
	
	timeline = frappe.db.get_value(
		'Task Timeline',
		{'task': task_id},
		[
			'name', 'assignee', 'start_date', 'end_date',
			'estimated_hours', 'actual_hours', 'progress_percent',
			'priority_score', 'complexity_rating', 'dependencies',
			'skill_requirements', 'notes'
		],
		as_dict=True
	)
	
	if timeline and timeline.dependencies:
		try:
			timeline.dependencies = json.loads(timeline.dependencies) if isinstance(timeline.dependencies, str) else timeline.dependencies
		except:
			timeline.dependencies = []
	
	if timeline and timeline.skill_requirements:
		try:
			timeline.skill_requirements = json.loads(timeline.skill_requirements) if isinstance(timeline.skill_requirements, str) else timeline.skill_requirements
		except:
			timeline.skill_requirements = []
	
	return timeline


@frappe.whitelist()
def create_or_update_timeline(task_id, timeline_data):
	"""Create or update timeline for a task"""
	
	if isinstance(timeline_data, str):
		timeline_data = json.loads(timeline_data)
	
	# Check if timeline already exists
	existing_timeline = frappe.db.exists('Task Timeline', {'task': task_id})
	
	if existing_timeline:
		# Update existing timeline
		timeline_doc = frappe.get_doc('Task Timeline', existing_timeline)
	else:
		# Create new timeline
		timeline_doc = frappe.get_doc({
			'doctype': 'Task Timeline',
			'task': task_id
		})
	
	# Update fields
	for field, value in timeline_data.items():
		if hasattr(timeline_doc, field):
			setattr(timeline_doc, field, value)
	
	timeline_doc.save()
	
	return timeline_doc.as_dict()


@frappe.whitelist()
def get_assignee_timeline(assignee, start_date, end_date):
	"""Get timeline data for a specific assignee"""
	
	timelines = frappe.get_all(
		'Task Timeline',
		filters={
			'assignee': assignee,
			'start_date': ['>=', start_date],
			'end_date': ['<=', end_date]
		},
		fields=[
			'name', 'task', 'start_date', 'end_date',
			'estimated_hours', 'actual_hours', 'progress_percent',
			'priority_score', 'complexity_rating'
		],
		order_by='start_date'
	)
	
	# Get task details
	for timeline in timelines:
		if timeline.task:
			task_data = frappe.db.get_value(
				'Task',
				timeline.task,
				['subject', 'status', 'priority', 'project'],
				as_dict=True
			)
			timeline.update(task_data)
	
	return timelines


@frappe.whitelist()
def check_dependencies(task_id):
	"""Check if task dependencies are satisfied"""
	
	timeline = frappe.db.get_value('Task Timeline', {'task': task_id}, 'dependencies')
	
	if not timeline:
		return {'can_start': True, 'blocking_tasks': []}
	
	try:
		dependencies = json.loads(timeline) if isinstance(timeline, str) else timeline
		
		if not dependencies:
			return {'can_start': True, 'blocking_tasks': []}
		
		blocking_tasks = []
		
		for dep_task in dependencies:
			task_status = frappe.db.get_value('Task', dep_task, 'status')
			if task_status not in ['Completed', 'Cancelled']:
				task_subject = frappe.db.get_value('Task', dep_task, 'subject')
				blocking_tasks.append({
					'task_id': dep_task,
					'subject': task_subject,
					'status': task_status
				})
		
		return {
			'can_start': len(blocking_tasks) == 0,
			'blocking_tasks': blocking_tasks
		}
		
	except Exception as e:
		frappe.log_error(f"Error checking dependencies: {str(e)}")
		return {'can_start': True, 'blocking_tasks': []}


@frappe.whitelist()
def get_timeline_analytics(assignee=None, start_date=None, end_date=None):
	"""Get timeline analytics"""
	
	filters = {}
	
	if assignee:
		filters['assignee'] = assignee
	
	if start_date and end_date:
		filters['start_date'] = ['between', [start_date, end_date]]
	
	timelines = frappe.get_all(
		'Task Timeline',
		filters=filters,
		fields=[
			'task', 'assignee', 'estimated_hours', 'actual_hours',
			'progress_percent', 'complexity_rating', 'start_date', 'end_date'
		]
	)
	
	# Calculate analytics
	total_estimated = sum(flt(t.estimated_hours) for t in timelines)
	total_actual = sum(flt(t.actual_hours) for t in timelines)
	
	completed_tasks = [t for t in timelines if flt(t.progress_percent) == 100]
	in_progress_tasks = [t for t in timelines if 0 < flt(t.progress_percent) < 100]
	not_started_tasks = [t for t in timelines if flt(t.progress_percent) == 0]
	
	# Complexity distribution
	complexity_dist = {}
	for timeline in timelines:
		complexity = timeline.complexity_rating or 'Medium'
		complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1
	
	return {
		'summary': {
			'total_tasks': len(timelines),
			'total_estimated_hours': total_estimated,
			'total_actual_hours': total_actual,
			'efficiency_ratio': (total_estimated / total_actual) if total_actual > 0 else 0
		},
		'task_status': {
			'completed': len(completed_tasks),
			'in_progress': len(in_progress_tasks),
			'not_started': len(not_started_tasks)
		},
		'complexity_distribution': complexity_dist,
		'overdue_tasks': [
			t for t in timelines 
			if t.end_date and get_datetime(t.end_date) < now_datetime() and flt(t.progress_percent) < 100
		]
	}
