# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint, flt, get_datetime, add_days, date_diff, now_datetime
from frappe.query_builder import DocType, Field
from frappe.cache_manager import redis_cache
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor


@dataclass
class WorkloadMetrics:
    total_capacity: float
    allocated_hours: float
    utilization_percent: float
    overallocation_hours: float
    available_hours: float
    efficiency_score: float


class WorkloadManagerV2:
    """High-performance workload management with intelligent caching and optimization"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes
        self.Task = DocType('Task')
        self.Employee = DocType('Employee')
        self.TaskTimeline = DocType('Task Timeline')
        self.WorkloadCapacity = DocType('Workload Capacity')
        
    @redis_cache(ttl=300, key_prefix="workload_data")
    def get_workload_data_optimized(self, department: str = None, 
                                  start_date: str = None, 
                                  end_date: str = None,
                                  force_refresh: bool = False) -> Dict:
        """Optimized workload data retrieval with single-query approach"""
        
        if force_refresh:
            self._clear_workload_cache(department)
        
        # Build optimized query with proper joins
        query = self._build_optimized_query(department, start_date, end_date)
        
        # Execute single optimized query
        raw_data = query.run(as_dict=True)
        
        # Process data using vectorized operations
        processed_data = self._process_workload_data_vectorized(raw_data, start_date, end_date)
        
        # Add real-time metrics
        processed_data['real_time_metrics'] = self._calculate_real_time_metrics(processed_data)
        
        # Add AI insights
        processed_data['ai_insights'] = self._generate_ai_insights(processed_data)
        
        return processed_data
    
    def _build_optimized_query(self, department: str, start_date: str, end_date: str):
        """Build single optimized query with all necessary joins"""
        
        query = (
            frappe.qb.from_(self.TaskTimeline)
            .left_join(self.Task).on(self.TaskTimeline.task == self.Task.name)
            .left_join(self.Employee).on(self.TaskTimeline.assignee == self.Employee.user_id)
            .left_join(self.WorkloadCapacity).on(
                (self.WorkloadCapacity.employee == self.TaskTimeline.assignee) &
                (self.WorkloadCapacity.date.between(start_date or '2024-01-01', end_date or '2024-12-31'))
            )
            .select(
                # Task fields
                self.Task.name.as_('task_id'),
                self.Task.subject.as_('task_title'),
                self.Task.status,
                self.Task.priority,
                self.Task.project,
                self.Task.description,
                
                # Timeline fields
                self.TaskTimeline.assignee,
                self.TaskTimeline.start_date,
                self.TaskTimeline.end_date,
                self.TaskTimeline.estimated_hours,
                self.TaskTimeline.actual_hours,
                self.TaskTimeline.progress_percent,
                self.TaskTimeline.priority_score,
                self.TaskTimeline.complexity_rating,
                
                # Employee fields
                self.Employee.employee_name,
                self.Employee.department,
                self.Employee.designation,
                self.Employee.image,
                
                # Capacity fields
                self.WorkloadCapacity.available_hours,
                self.WorkloadCapacity.allocated_hours,
                self.WorkloadCapacity.utilization_percent,
                self.WorkloadCapacity.date.as_('capacity_date')
            )
        )
        
        # Apply filters efficiently
        conditions = []
        
        if department:
            conditions.append(self.Employee.department == department)
            
        if start_date and end_date:
            conditions.append(
                (self.TaskTimeline.start_date.between(start_date, end_date)) |
                (self.TaskTimeline.end_date.between(start_date, end_date)) |
                ((self.TaskTimeline.start_date <= start_date) & (self.TaskTimeline.end_date >= end_date))
            )
        
        # Apply active task filter
        conditions.append(self.Task.status.isin(['Open', 'Working', 'Pending Review']))
        
        if conditions:
            query = query.where(frappe.qb.And(*conditions))
            
        return query.orderby(self.TaskTimeline.start_date, self.TaskTimeline.priority_score.desc())
    
    def _process_workload_data_vectorized(self, raw_data: List[Dict], 
                                        start_date: str, end_date: str) -> Dict:
        """Process workload data using vectorized operations for performance"""
        
        # Group data efficiently
        assignees_map = {}
        tasks_list = []
        capacity_map = {}
        
        # Single pass processing
        for row in raw_data:
            assignee_id = row.get('assignee') or 'unassigned'
            
            # Process assignee data
            if assignee_id not in assignees_map:
                assignees_map[assignee_id] = {
                    'id': assignee_id,
                    'name': row.get('employee_name') or 'Unassigned',
                    'department': row.get('department'),
                    'role': row.get('designation'),
                    'image': row.get('image'),
                    'tasks': [],
                    'total_hours': 0,
                    'capacity': 0,
                    'utilization': 0,
                    'efficiency_score': 1.0
                }
            
            # Process task data
            if row.get('task_id'):
                task = {
                    'id': row['task_id'],
                    'title': row['task_title'],
                    'assignee': assignee_id,
                    'startDate': row.get('start_date'),
                    'endDate': row.get('end_date'),
                    'duration': flt(row.get('estimated_hours', 0)),
                    'actualHours': flt(row.get('actual_hours', 0)),
                    'progress': flt(row.get('progress_percent', 0)),
                    'status': row['status'],
                    'priority': row['priority'],
                    'project': row.get('project', ''),
                    'description': row.get('description', ''),
                    'complexityRating': row.get('complexity_rating', 'Medium'),
                    'priorityScore': cint(row.get('priority_score', 50)),
                    'isScheduled': bool(row.get('start_date') and row.get('end_date')),
                    'isOverdue': self._is_task_overdue(row.get('end_date'), row['status']),
                    'color': self._get_task_color(row['status'], row['priority'])
                }
                
                tasks_list.append(task)
                assignees_map[assignee_id]['tasks'].append(task)
                assignees_map[assignee_id]['total_hours'] += task['duration']
            
            # Process capacity data
            if row.get('capacity_date') and row.get('available_hours'):
                capacity_key = f"{assignee_id}_{row['capacity_date']}"
                if capacity_key not in capacity_map:
                    capacity_map[capacity_key] = {
                        'assignee': assignee_id,
                        'date': row['capacity_date'],
                        'available_hours': flt(row['available_hours']),
                        'allocated_hours': flt(row.get('allocated_hours', 0)),
                        'utilization': flt(row.get('utilization_percent', 0))
                    }
        
        # Calculate aggregated capacity and utilization
        for assignee_id, assignee in assignees_map.items():
            assignee_capacity = [c for c in capacity_map.values() if c['assignee'] == assignee_id]
            
            if assignee_capacity:
                assignee['capacity'] = sum(c['available_hours'] for c in assignee_capacity)
                avg_utilization = sum(c['utilization'] for c in assignee_capacity) / len(assignee_capacity)
                assignee['utilization'] = avg_utilization
            else:
                # Fallback calculation
                days = self._calculate_working_days(start_date, end_date)
                assignee['capacity'] = days * 8  # 8 hours per day default
                assignee['utilization'] = (assignee['total_hours'] / assignee['capacity']) * 100 if assignee['capacity'] > 0 else 0
        
        return {
            'assignees': list(assignees_map.values()),
            'tasks': tasks_list,
            'capacity_data': list(capacity_map.values()),
            'metrics': self._calculate_aggregated_metrics(assignees_map),
            'cache_timestamp': datetime.now().isoformat(),
            'data_freshness': 'real_time'
        }
    
    def _calculate_real_time_metrics(self, data: Dict) -> Dict:
        """Calculate real-time performance metrics"""
        
        assignees = data['assignees']
        tasks = data['tasks']
        
        # Calculate key metrics
        total_capacity = sum(a['capacity'] for a in assignees)
        total_allocated = sum(t['duration'] for t in tasks if t['isScheduled'])
        
        overallocated_count = len([a for a in assignees if a['utilization'] > 100])
        underutilized_count = len([a for a in assignees if a['utilization'] < 70])
        
        # Task status distribution
        status_distribution = {}
        for task in tasks:
            status = task['status']
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # Priority distribution
        priority_distribution = {}
        for task in tasks:
            priority = task['priority']
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        return {
            'total_capacity': total_capacity,
            'total_allocated': total_allocated,
            'overall_utilization': (total_allocated / total_capacity) * 100 if total_capacity > 0 else 0,
            'overallocated_count': overallocated_count,
            'underutilized_count': underutilized_count,
            'available_capacity': max(0, total_capacity - total_allocated),
            'status_distribution': status_distribution,
            'priority_distribution': priority_distribution,
            'completion_rate': len([t for t in tasks if t['status'] == 'Completed']) / len(tasks) * 100 if tasks else 0,
            'overdue_count': len([t for t in tasks if t['isOverdue']])
        }
    
    def _generate_ai_insights(self, data: Dict) -> Dict:
        """Generate AI-powered insights and recommendations"""
        
        insights = {
            'recommendations': [],
            'alerts': [],
            'predictions': {},
            'optimization_suggestions': []
        }
        
        assignees = data['assignees']
        metrics = data.get('real_time_metrics', {})
        
        # Overallocation alerts
        overallocated = [a for a in assignees if a['utilization'] > 120]
        if overallocated:
            insights['alerts'].append({
                'type': 'overallocation',
                'severity': 'high',
                'message': f'{len(overallocated)} team members are severely overallocated (>120%)',
                'affected_assignees': [a['name'] for a in overallocated],
                'suggested_action': 'Redistribute tasks or extend deadlines'
            })
        
        # Underutilization opportunities
        underutilized = [a for a in assignees if a['utilization'] < 60 and a['utilization'] > 0]
        if underutilized:
            available_hours = sum(a['capacity'] - a['total_hours'] for a in underutilized)
            insights['recommendations'].append({
                'type': 'capacity_optimization',
                'message': f'{available_hours:.1f} hours of available capacity detected',
                'assignees': [a['name'] for a in underutilized],
                'suggested_action': 'Assign additional tasks to optimize utilization'
            })
        
        # Bottleneck detection
        high_priority_unscheduled = [t for t in data['tasks'] if t['priority'] == 'High' and not t['isScheduled']]
        if high_priority_unscheduled:
            insights['alerts'].append({
                'type': 'bottleneck',
                'severity': 'medium',
                'message': f'{len(high_priority_unscheduled)} high-priority tasks are unscheduled',
                'suggested_action': 'Schedule high-priority tasks immediately'
            })
        
        # Workload balance suggestions
        utilization_variance = self._calculate_utilization_variance(assignees)
        if utilization_variance > 30:  # High variance indicates imbalance
            insights['optimization_suggestions'].append({
                'type': 'workload_balance',
                'message': 'Workload distribution is uneven across team members',
                'variance': utilization_variance,
                'suggested_action': 'Redistribute tasks for better balance'
            })
        
        return insights
    
    def _is_task_overdue(self, end_date, status):
        """Check if task is overdue"""
        if not end_date or status in ['Completed', 'Cancelled']:
            return False
        return get_datetime(end_date) < now_datetime()
    
    def _get_task_color(self, status, priority):
        """Get task color based on status and priority"""
        color_map = {
            'Open': '#3b82f6',      # Blue
            'Working': '#f59e0b',   # Amber
            'Pending Review': '#8b5cf6',  # Purple
            'Completed': '#10b981', # Green
            'Cancelled': '#6b7280'  # Gray
        }
        
        # Override with priority colors for high priority tasks
        if priority == 'High':
            return '#ef4444'  # Red
        elif priority == 'Urgent':
            return '#dc2626'  # Dark Red
        
        return color_map.get(status, '#6b7280')
    
    def _calculate_working_days(self, start_date, end_date):
        """Calculate working days between two dates"""
        if not start_date or not end_date:
            return 30  # Default fallback
        
        try:
            start = get_datetime(start_date).date()
            end = get_datetime(end_date).date()
            
            # Simple calculation - exclude weekends
            total_days = (end - start).days + 1
            weeks = total_days // 7
            remaining_days = total_days % 7
            
            # Approximate working days (5 days per week)
            working_days = weeks * 5
            
            # Add remaining weekdays
            for i in range(remaining_days):
                day = start + timedelta(days=weeks * 7 + i)
                if day.weekday() < 5:  # Monday = 0, Friday = 4
                    working_days += 1
            
            return max(1, working_days)
            
        except:
            return 30  # Fallback
    
    def _calculate_aggregated_metrics(self, assignees_map):
        """Calculate aggregated metrics across all assignees"""
        
        total_assignees = len(assignees_map)
        total_capacity = sum(a['capacity'] for a in assignees_map.values())
        total_allocated = sum(a['total_hours'] for a in assignees_map.values())
        
        overallocated = [a for a in assignees_map.values() if a['utilization'] > 100]
        underutilized = [a for a in assignees_map.values() if a['utilization'] < 70]
        
        return {
            'total_assignees': total_assignees,
            'total_capacity': total_capacity,
            'total_allocated': total_allocated,
            'overall_utilization': (total_allocated / total_capacity) * 100 if total_capacity > 0 else 0,
            'overallocated_count': len(overallocated),
            'underutilized_count': len(underutilized),
            'balanced_count': total_assignees - len(overallocated) - len(underutilized)
        }
    
    def _calculate_utilization_variance(self, assignees):
        """Calculate variance in utilization across assignees"""
        if not assignees:
            return 0
        
        utilizations = [a['utilization'] for a in assignees if a['utilization'] > 0]
        if not utilizations:
            return 0
        
        mean_util = sum(utilizations) / len(utilizations)
        variance = sum((u - mean_util) ** 2 for u in utilizations) / len(utilizations)
        
        return variance ** 0.5  # Standard deviation
    
    def _clear_workload_cache(self, department=None):
        """Clear workload-related cache entries"""
        try:
            cache_keys = [
                "workload_data_global",
                f"workload_data_{department}" if department else None,
                "workload_metrics",
                "ai_insights"
            ]
            
            for key in cache_keys:
                if key:
                    frappe.cache().delete_value(key)
                    
        except Exception as e:
            frappe.log_error(f"Failed to clear workload cache: {str(e)}")


# API Endpoints
@frappe.whitelist()
def get_workload_data_v2(department=None, start_date=None, end_date=None, force_refresh=False):
    """High-performance workload API endpoint"""
    try:
        manager = WorkloadManagerV2()
        return manager.get_workload_data_optimized(department, start_date, end_date, force_refresh)
    except Exception as e:
        frappe.log_error(f"Workload API Error: {str(e)}")
        frappe.throw(f"Failed to load workload data: {str(e)}")


@frappe.whitelist()
def bulk_update_tasks_v2(updates):
    """Optimized bulk task updates with transaction management"""
    
    if not updates:
        frappe.throw("No updates provided")
    
    # Parse updates if string
    if isinstance(updates, str):
        updates = json.loads(updates)
    
    updated_tasks = []
    
    # Use database transaction for consistency
    try:
        with frappe.db.transaction():
            for update in updates:
                task_id = update.get('task_id')
                changes = update.get('changes', {})
                
                if not task_id:
                    continue
                
                # Update task
                task_doc = frappe.get_doc('Task', task_id)
                for field, value in changes.items():
                    if hasattr(task_doc, field):
                        setattr(task_doc, field, value)
                
                task_doc.save()
                
                # Update timeline if needed
                timeline_changes = update.get('timeline_changes', {})
                if timeline_changes:
                    timeline_name = frappe.db.exists('Task Timeline', {'task': task_id})
                    if timeline_name:
                        timeline_doc = frappe.get_doc('Task Timeline', timeline_name)
                        for field, value in timeline_changes.items():
                            if hasattr(timeline_doc, field):
                                setattr(timeline_doc, field, value)
                        timeline_doc.save()
                
                updated_tasks.append(task_doc.as_dict())
        
        # Emit batch real-time update
        from planner.realtime_v2 import emit_batch_update_v2
        emit_batch_update_v2(updated_tasks)
        
        # Clear relevant caches
        clear_workload_cache()
        
        return {'updated_count': len(updated_tasks), 'tasks': updated_tasks}
        
    except Exception as e:
        frappe.log_error(f"Bulk update error: {str(e)}")
        frappe.throw(f"Failed to update tasks: {str(e)}")


@frappe.whitelist()
def move_task_v2(task_id, assignee_id=None, start_date=None, end_date=None):
    """Enhanced task movement with validation and optimization"""
    
    if not task_id:
        frappe.throw("Task ID is required")
    
    try:
        # Get task and timeline
        task_doc = frappe.get_doc('Task', task_id)
        
        timeline_name = frappe.db.exists('Task Timeline', {'task': task_id})
        if timeline_name:
            timeline_doc = frappe.get_doc('Task Timeline', timeline_name)
        else:
            # Create new timeline
            timeline_doc = frappe.get_doc({
                'doctype': 'Task Timeline',
                'task': task_id,
                'estimated_hours': task_doc.expected_time or 8.0
            })
        
        # Validate capacity if moving to new assignee
        if assignee_id and assignee_id != 'unassigned':
            if not validate_assignee_capacity(assignee_id, start_date, end_date, timeline_doc.estimated_hours):
                frappe.throw("Assignee does not have sufficient capacity for this task")
        
        # Update task assignment
        if assignee_id:
            if assignee_id == 'unassigned':
                task_doc._assign = None
            else:
                task_doc._assign = json.dumps([assignee_id])
        
        # Update timeline
        if start_date:
            timeline_doc.start_date = get_datetime(start_date)
        if end_date:
            timeline_doc.end_date = get_datetime(end_date)
        if assignee_id:
            timeline_doc.assignee = assignee_id if assignee_id != 'unassigned' else None
        
        # Save changes
        task_doc.save()
        timeline_doc.save()
        
        # Emit real-time update
        from planner.realtime_v2 import emit_task_update_v2
        emit_task_update_v2(task_doc, timeline_doc)
        
        # Clear cache
        clear_workload_cache()
        
        return {
            'success': True,
            'task': task_doc.as_dict(),
            'timeline': timeline_doc.as_dict(),
            'message': 'Task moved successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Task move error: {str(e)}")
        frappe.throw(f"Failed to move task: {str(e)}")


def validate_assignee_capacity(assignee_id, start_date, end_date, required_hours):
    """Validate if assignee has capacity for the task"""
    
    if not start_date or not end_date:
        return True  # Can't validate without dates
    
    # Get capacity data for date range
    capacity_data = frappe.get_all(
        'Workload Capacity',
        filters={
            'employee': assignee_id,
            'date': ['between', [start_date, end_date]]
        },
        fields=['available_hours', 'allocated_hours']
    )
    
    total_available = sum(c['available_hours'] for c in capacity_data)
    total_allocated = sum(c['allocated_hours'] for c in capacity_data)
    
    return (total_available - total_allocated) >= required_hours


def clear_workload_cache():
    """Clear all workload-related cache entries"""
    try:
        cache_keys = [
            "workload_data_global",
            "workload_metrics",
            "ai_insights"
        ]
        
        for key in cache_keys:
            frappe.cache().delete_value(key)
            
    except Exception as e:
        frappe.log_error(f"Failed to clear workload cache: {str(e)}")


@frappe.whitelist()
def get_workload_metrics(department=None):
    """Get workload metrics for dashboard"""
    
    try:
        manager = WorkloadManagerV2()
        data = manager.get_workload_data_optimized(department)
        return data.get('real_time_metrics', {})
        
    except Exception as e:
        frappe.log_error(f"Workload metrics error: {str(e)}")
        return {}


@frappe.whitelist()
def get_ai_insights(department=None):
    """Get AI insights and recommendations"""
    
    try:
        manager = WorkloadManagerV2()
        data = manager.get_workload_data_optimized(department)
        return data.get('ai_insights', {})
        
    except Exception as e:
        frappe.log_error(f"AI insights error: {str(e)}")
        return {}
