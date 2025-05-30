# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta


class WorkloadEvents(Document):
	def validate(self):
		"""Validate event data"""
		self.validate_event_type()
		self.validate_entity()
		self.validate_data()
	
	def validate_event_type(self):
		"""Validate event type"""
		valid_event_types = [
			'task_update', 'task_created', 'task_deleted', 'task_moved',
			'capacity_change', 'batch_task_update', 'workload_alert',
			'ai_recommendation', 'user_activity', 'timeline_created',
			'timeline_updated', 'timeline_deleted'
		]
		
		if self.event_type not in valid_event_types:
			frappe.msgprint(f"Warning: Unknown event type '{self.event_type}'")
	
	def validate_entity(self):
		"""Validate entity reference"""
		if self.entity_type and self.entity_id:
			# Check if entity exists (optional validation)
			if self.entity_type in ['Task', 'Task Timeline', 'Workload Capacity']:
				if not frappe.db.exists(self.entity_type, self.entity_id):
					frappe.msgprint(f"Warning: {self.entity_type} '{self.entity_id}' does not exist")
	
	def validate_data(self):
		"""Validate JSON data"""
		if self.data:
			try:
				if isinstance(self.data, str):
					json.loads(self.data)
			except json.JSONDecodeError:
				frappe.throw("Invalid JSON data format")
	
	def before_insert(self):
		"""Actions before inserting event"""
		if not self.timestamp:
			self.timestamp = datetime.now()
		
		if not self.user:
			self.user = frappe.session.user
		
		if not self.session_id:
			self.session_id = frappe.session.sid


@frappe.whitelist()
def get_recent_events(entity_type=None, entity_id=None, event_type=None, hours=24, limit=100):
	"""Get recent events with filtering"""
	
	filters = {}
	
	if entity_type:
		filters['entity_type'] = entity_type
	
	if entity_id:
		filters['entity_id'] = entity_id
	
	if event_type:
		filters['event_type'] = event_type
	
	# Filter by time
	cutoff_time = datetime.now() - timedelta(hours=hours)
	filters['timestamp'] = ['>=', cutoff_time]
	
	events = frappe.get_all(
		'Workload Events',
		filters=filters,
		fields=[
			'name', 'event_type', 'entity_type', 'entity_id',
			'user', 'timestamp', 'data', 'processed'
		],
		order_by='timestamp desc',
		limit=limit
	)
	
	# Parse JSON data
	for event in events:
		if event.data:
			try:
				event.data = json.loads(event.data) if isinstance(event.data, str) else event.data
			except:
				event.data = {}
	
	return events


@frappe.whitelist()
def get_event_analytics(start_date=None, end_date=None, event_type=None):
	"""Get event analytics for dashboard"""
	
	filters = {}
	
	if start_date and end_date:
		filters['timestamp'] = ['between', [start_date, end_date]]
	
	if event_type:
		filters['event_type'] = event_type
	
	# Get event data
	events = frappe.get_all(
		'Workload Events',
		filters=filters,
		fields=['event_type', 'user', 'timestamp', 'entity_type']
	)
	
	# Calculate analytics
	total_events = len(events)
	
	# Event type distribution
	event_type_dist = {}
	for event in events:
		event_type = event['event_type']
		event_type_dist[event_type] = event_type_dist.get(event_type, 0) + 1
	
	# User activity
	user_activity = {}
	for event in events:
		user = event['user']
		user_activity[user] = user_activity.get(user, 0) + 1
	
	# Entity type distribution
	entity_type_dist = {}
	for event in events:
		entity_type = event['entity_type']
		entity_type_dist[entity_type] = entity_type_dist.get(entity_type, 0) + 1
	
	# Hourly distribution
	hourly_dist = {}
	for event in events:
		hour = event['timestamp'].hour
		hourly_dist[hour] = hourly_dist.get(hour, 0) + 1
	
	return {
		'summary': {
			'total_events': total_events,
			'unique_users': len(user_activity),
			'event_types': len(event_type_dist)
		},
		'distributions': {
			'event_types': event_type_dist,
			'user_activity': user_activity,
			'entity_types': entity_type_dist,
			'hourly_activity': hourly_dist
		}
	}


@frappe.whitelist()
def mark_events_processed(event_names):
	"""Mark events as processed"""
	
	if isinstance(event_names, str):
		event_names = json.loads(event_names)
	
	processed_count = 0
	
	for event_name in event_names:
		try:
			event_doc = frappe.get_doc('Workload Events', event_name)
			event_doc.processed = 1
			event_doc.processing_notes = f"Processed at {datetime.now()}"
			event_doc.save()
			processed_count += 1
		except Exception as e:
			frappe.log_error(f"Failed to mark event {event_name} as processed: {str(e)}")
	
	return {
		'processed_count': processed_count,
		'total_requested': len(event_names)
	}


@frappe.whitelist()
def cleanup_old_events(days=30):
	"""Clean up old events (called periodically)"""
	
	cutoff_date = datetime.now() - timedelta(days=days)
	
	# Get old events
	old_events = frappe.get_all(
		'Workload Events',
		filters={
			'timestamp': ['<', cutoff_date],
			'processed': 1
		},
		fields=['name']
	)
	
	deleted_count = 0
	
	for event in old_events:
		try:
			frappe.delete_doc('Workload Events', event.name)
			deleted_count += 1
		except Exception as e:
			frappe.log_error(f"Failed to delete old event {event.name}: {str(e)}")
	
	return {
		'deleted_count': deleted_count,
		'cutoff_date': cutoff_date.isoformat()
	}


def create_event(event_type, entity_type, entity_id, data=None, user=None):
	"""Helper function to create events programmatically"""
	
	try:
		event_doc = frappe.get_doc({
			'doctype': 'Workload Events',
			'event_type': event_type,
			'entity_type': entity_type,
			'entity_id': entity_id,
			'user': user or frappe.session.user,
			'session_id': frappe.session.sid,
			'data': json.dumps(data, default=str) if data else None,
			'timestamp': datetime.now()
		})
		
		event_doc.insert(ignore_permissions=True)
		return event_doc.name
		
	except Exception as e:
		frappe.log_error(f"Failed to create event: {str(e)}")
		return None


# Scheduled function to clean up old events
def daily_cleanup():
	"""Daily cleanup of old events"""
	try:
		result = cleanup_old_events(days=30)
		frappe.logger().info(f"Cleaned up {result['deleted_count']} old workload events")
	except Exception as e:
		frappe.log_error(f"Failed to cleanup old events: {str(e)}")
