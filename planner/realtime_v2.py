# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.realtime import emit_via_redis
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from collections import defaultdict


class RealtimeManagerV2:
    """Enhanced real-time system with room management and conflict resolution"""
    
    def __init__(self):
        self.active_sessions = {}
        self.room_subscriptions = defaultdict(set)
        self.event_queue = []
        self.batch_size = 10
        self.batch_timeout = 1.0  # seconds
        
    def emit_task_update_v2(self, task_doc, timeline_doc=None, event_type="task_update"):
        """Enhanced task update with targeted emission and conflict resolution"""
        
        # Prepare comprehensive task data
        task_data = {
            'id': task_doc.name,
            'title': task_doc.subject,
            'status': task_doc.status,
            'priority': task_doc.priority,
            'project': task_doc.project,
            'assignee': self._get_primary_assignee(task_doc._assign),
            'department': getattr(task_doc, 'department', None),
            'timestamp': datetime.now().isoformat(),
            'user': frappe.session.user,
            'session_id': frappe.session.sid
        }
        
        # Add timeline data if available
        if timeline_doc:
            task_data.update({
                'startDate': timeline_doc.start_date.isoformat() if timeline_doc.start_date else None,
                'endDate': timeline_doc.end_date.isoformat() if timeline_doc.end_date else None,
                'estimatedHours': timeline_doc.estimated_hours,
                'actualHours': timeline_doc.actual_hours,
                'progress': timeline_doc.progress_percent,
                'complexityRating': timeline_doc.complexity_rating,
                'priorityScore': timeline_doc.priority_score
            })
        
        # Determine target rooms
        target_rooms = self._get_target_rooms(task_data)
        
        # Check for conflicts
        conflict_info = self._check_for_conflicts(task_data)
        if conflict_info:
            task_data['conflict'] = conflict_info
            event_type = "task_conflict"
        
        # Emit to specific rooms with batching
        self._emit_to_rooms(target_rooms, event_type, task_data)
        
        # Log event for audit trail
        self._log_realtime_event(event_type, task_data)
    
    def emit_batch_update_v2(self, tasks_data: List[Dict], event_type="batch_task_update"):
        """Optimized batch updates with compression and smart routing"""
        
        if not tasks_data:
            return
        
        # Group by department for targeted emission
        dept_groups = defaultdict(list)
        user_groups = defaultdict(list)
        
        for task in tasks_data:
            # Group by department
            dept = task.get('department', 'general')
            dept_groups[dept].append(task)
            
            # Group by assignee for personal notifications
            assignee = task.get('assignee')
            if assignee:
                user_groups[assignee].append(task)
        
        # Emit department-level updates
        for dept, tasks in dept_groups.items():
            compressed_data = {
                'tasks': tasks,
                'count': len(tasks),
                'timestamp': datetime.now().isoformat(),
                'user': frappe.session.user,
                'batch_id': self._generate_batch_id()
            }
            
            frappe.publish_realtime(
                event=event_type,
                message=compressed_data,
                room=f"workload_{dept}",
                after_commit=True
            )
        
        # Emit user-specific updates
        for user, tasks in user_groups.items():
            user_data = {
                'tasks': tasks,
                'count': len(tasks),
                'timestamp': datetime.now().isoformat(),
                'notification_type': 'assignment_update'
            }
            
            frappe.publish_realtime(
                event="user_task_update",
                message=user_data,
                room=f"user_{user}",
                after_commit=True
            )
    
    def emit_capacity_change(self, assignee_id: str, capacity_data: Dict):
        """Emit capacity changes for real-time utilization updates"""
        
        event_data = {
            'assignee_id': assignee_id,
            'capacity_data': capacity_data,
            'timestamp': datetime.now().isoformat(),
            'user': frappe.session.user,
            'event_id': self._generate_event_id()
        }
        
        # Calculate utilization impact
        utilization_impact = self._calculate_utilization_impact(assignee_id, capacity_data)
        if utilization_impact:
            event_data['utilization_impact'] = utilization_impact
        
        # Emit to relevant rooms
        target_rooms = [
            f"user_{assignee_id}",
            "workload_global"
        ]
        
        # Add department room if available
        try:
            employee = frappe.get_doc('Employee', {'user_id': assignee_id})
            if employee and employee.department:
                target_rooms.append(f"workload_{employee.department}")
        except:
            pass
        
        for room in target_rooms:
            frappe.publish_realtime(
                event="capacity_change",
                message=event_data,
                room=room,
                after_commit=True
            )
    
    def emit_workload_alert(self, alert_type: str, alert_data: Dict, severity="medium"):
        """Emit workload alerts (overallocation, bottlenecks, etc.)"""
        
        alert_message = {
            'type': alert_type,
            'severity': severity,
            'data': alert_data,
            'timestamp': datetime.now().isoformat(),
            'alert_id': self._generate_alert_id(),
            'requires_action': severity in ['high', 'critical']
        }
        
        # Determine target audience based on alert type
        if alert_type == 'overallocation':
            # Send to managers and affected users
            target_rooms = ['workload_managers']
            if 'affected_users' in alert_data:
                for user in alert_data['affected_users']:
                    target_rooms.append(f"user_{user}")
        
        elif alert_type == 'bottleneck':
            # Send to project managers and department heads
            target_rooms = ['workload_managers', 'project_managers']
            if 'department' in alert_data:
                target_rooms.append(f"workload_{alert_data['department']}")
        
        else:
            # General alert - send to global room
            target_rooms = ['workload_global']
        
        for room in target_rooms:
            frappe.publish_realtime(
                event="workload_alert",
                message=alert_message,
                room=room,
                after_commit=True
            )
    
    def emit_ai_recommendation(self, recommendation: Dict, target_users: List[str] = None):
        """Emit AI-generated recommendations"""
        
        recommendation_data = {
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat(),
            'recommendation_id': self._generate_recommendation_id(),
            'expires_at': self._calculate_expiry_time(recommendation.get('urgency', 'medium'))
        }
        
        # Send to specific users or broadcast
        if target_users:
            for user in target_users:
                frappe.publish_realtime(
                    event="ai_recommendation",
                    message=recommendation_data,
                    room=f"user_{user}",
                    after_commit=True
                )
        else:
            # Broadcast to all workload users
            frappe.publish_realtime(
                event="ai_recommendation",
                message=recommendation_data,
                room="workload_global",
                after_commit=True
            )
    
    def join_room(self, user_id: str, room: str):
        """Handle user joining a room"""
        
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = {
                'rooms': set(),
                'last_activity': datetime.now(),
                'session_id': frappe.session.sid
            }
        
        self.active_sessions[user_id]['rooms'].add(room)
        self.room_subscriptions[room].add(user_id)
        
        # Send room join confirmation
        frappe.publish_realtime(
            event="room_joined",
            message={
                'room': room,
                'user_count': len(self.room_subscriptions[room]),
                'timestamp': datetime.now().isoformat()
            },
            room=f"user_{user_id}",
            after_commit=True
        )
    
    def leave_room(self, user_id: str, room: str):
        """Handle user leaving a room"""
        
        if user_id in self.active_sessions:
            self.active_sessions[user_id]['rooms'].discard(room)
            
        self.room_subscriptions[room].discard(user_id)
        
        # Clean up empty rooms
        if not self.room_subscriptions[room]:
            del self.room_subscriptions[room]
    
    def get_active_users(self, room: str = None) -> List[Dict]:
        """Get list of active users in a room or globally"""
        
        if room:
            users = self.room_subscriptions.get(room, set())
        else:
            users = set()
            for room_users in self.room_subscriptions.values():
                users.update(room_users)
        
        # Get user details
        active_users = []
        for user_id in users:
            if user_id in self.active_sessions:
                session = self.active_sessions[user_id]
                user_info = frappe.db.get_value(
                    'User', user_id, 
                    ['full_name', 'user_image'], 
                    as_dict=True
                )
                
                active_users.append({
                    'user_id': user_id,
                    'name': user_info.get('full_name', user_id),
                    'image': user_info.get('user_image'),
                    'last_activity': session['last_activity'].isoformat(),
                    'rooms': list(session['rooms'])
                })
        
        return active_users
    
    def _get_target_rooms(self, task_data: Dict) -> List[str]:
        """Determine which rooms should receive the update"""
        
        rooms = ['workload_global']  # Global room for all updates
        
        # Department-specific room
        if task_data.get('department'):
            rooms.append(f"workload_{task_data['department']}")
        
        # Assignee-specific room
        if task_data.get('assignee'):
            rooms.append(f"user_{task_data['assignee']}")
        
        # Project-specific room
        if task_data.get('project'):
            rooms.append(f"project_{task_data['project']}")
        
        return rooms
    
    def _get_primary_assignee(self, assign_json):
        """Extract primary assignee from assignment JSON"""
        
        if not assign_json:
            return None
        
        try:
            if isinstance(assign_json, str):
                assignees = json.loads(assign_json)
            else:
                assignees = assign_json
            
            return assignees[0] if assignees else None
            
        except (json.JSONDecodeError, TypeError, IndexError):
            return None
    
    def _check_for_conflicts(self, task_data: Dict) -> Optional[Dict]:
        """Check for potential conflicts (concurrent edits, scheduling conflicts)"""
        
        conflicts = {}
        
        # Check for concurrent edits
        if task_data.get('id'):
            recent_updates = self._get_recent_task_updates(task_data['id'])
            if len(recent_updates) > 1:
                conflicts['concurrent_edits'] = {
                    'count': len(recent_updates),
                    'users': [u['user'] for u in recent_updates],
                    'last_update': recent_updates[0]['timestamp']
                }
        
        # Check for scheduling conflicts
        if task_data.get('assignee') and task_data.get('startDate') and task_data.get('endDate'):
            scheduling_conflicts = self._check_scheduling_conflicts(
                task_data['assignee'],
                task_data['startDate'],
                task_data['endDate']
            )
            if scheduling_conflicts:
                conflicts['scheduling'] = scheduling_conflicts
        
        return conflicts if conflicts else None
    
    def _emit_to_rooms(self, rooms: List[str], event_type: str, data: Dict):
        """Emit event to multiple rooms efficiently"""
        
        for room in rooms:
            frappe.publish_realtime(
                event=event_type,
                message=data,
                room=room,
                after_commit=True
            )
    
    def _log_realtime_event(self, event_type: str, data: Dict):
        """Log real-time events for debugging and analytics"""
        
        try:
            # Create event log entry
            event_doc = frappe.get_doc({
                'doctype': 'Workload Events',
                'event_type': event_type,
                'entity_type': 'Task',
                'entity_id': data.get('id'),
                'user': frappe.session.user,
                'session_id': frappe.session.sid,
                'data': json.dumps(data, default=str)
            })
            event_doc.insert(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Failed to log realtime event: {str(e)}")
    
    def _calculate_utilization_impact(self, assignee_id: str, capacity_data: Dict) -> Optional[Dict]:
        """Calculate the impact of capacity changes on utilization"""
        
        try:
            # Get current tasks for the assignee
            current_tasks = frappe.get_all(
                'Task Timeline',
                filters={'assignee': assignee_id},
                fields=['estimated_hours', 'start_date', 'end_date']
            )
            
            total_task_hours = sum(t.estimated_hours or 0 for t in current_tasks)
            new_available_hours = capacity_data.get('available_hours', 0)
            
            if new_available_hours > 0:
                new_utilization = (total_task_hours / new_available_hours) * 100
                
                return {
                    'new_utilization': new_utilization,
                    'utilization_change': new_utilization - capacity_data.get('previous_utilization', 0),
                    'is_overallocated': new_utilization > 100,
                    'available_capacity': max(0, new_available_hours - total_task_hours)
                }
            
        except Exception as e:
            frappe.log_error(f"Failed to calculate utilization impact: {str(e)}")
        
        return None
    
    def _get_recent_task_updates(self, task_id: str, minutes: int = 5) -> List[Dict]:
        """Get recent updates for a task"""
        
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            recent_events = frappe.get_all(
                'Workload Events',
                filters={
                    'entity_id': task_id,
                    'timestamp': ['>=', cutoff_time]
                },
                fields=['user', 'timestamp', 'event_type'],
                order_by='timestamp desc'
            )
            
            return recent_events
            
        except Exception:
            return []
    
    def _check_scheduling_conflicts(self, assignee: str, start_date: str, end_date: str) -> Optional[Dict]:
        """Check for scheduling conflicts with existing tasks"""
        
        try:
            # Get overlapping tasks
            overlapping_tasks = frappe.get_all(
                'Task Timeline',
                filters={
                    'assignee': assignee,
                    'start_date': ['<=', end_date],
                    'end_date': ['>=', start_date]
                },
                fields=['task', 'start_date', 'end_date', 'estimated_hours']
            )
            
            if overlapping_tasks:
                return {
                    'conflicting_tasks': len(overlapping_tasks),
                    'tasks': [
                        {
                            'task_id': t.task,
                            'start_date': t.start_date,
                            'end_date': t.end_date,
                            'hours': t.estimated_hours
                        }
                        for t in overlapping_tasks
                    ]
                }
            
        except Exception as e:
            frappe.log_error(f"Failed to check scheduling conflicts: {str(e)}")
        
        return None
    
    def _generate_batch_id(self) -> str:
        """Generate unique batch ID"""
        return f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{frappe.generate_hash(length=6)}"
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{frappe.generate_hash(length=8)}"
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        return f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{frappe.generate_hash(length=6)}"
    
    def _generate_recommendation_id(self) -> str:
        """Generate unique recommendation ID"""
        return f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{frappe.generate_hash(length=8)}"
    
    def _calculate_expiry_time(self, urgency: str) -> str:
        """Calculate expiry time for recommendations based on urgency"""
        
        expiry_hours = {
            'low': 24,
            'medium': 8,
            'high': 4,
            'critical': 1
        }
        
        hours = expiry_hours.get(urgency, 8)
        expiry_time = datetime.now() + timedelta(hours=hours)
        
        return expiry_time.isoformat()


# Global instance
realtime_manager = RealtimeManagerV2()


# Global functions for easy access
def emit_task_update_v2(task_doc, timeline_doc=None, event_type="task_update"):
    """Global function for task updates"""
    realtime_manager.emit_task_update_v2(task_doc, timeline_doc, event_type)


def emit_batch_update_v2(tasks_data, event_type="batch_task_update"):
    """Global function for batch updates"""
    realtime_manager.emit_batch_update_v2(tasks_data, event_type)


def emit_capacity_change(assignee_id, capacity_data):
    """Global function for capacity changes"""
    realtime_manager.emit_capacity_change(assignee_id, capacity_data)


def emit_workload_alert(alert_type, alert_data, severity="medium"):
    """Global function for workload alerts"""
    realtime_manager.emit_workload_alert(alert_type, alert_data, severity)


def emit_ai_recommendation(recommendation, target_users=None):
    """Global function for AI recommendations"""
    realtime_manager.emit_ai_recommendation(recommendation, target_users)


# WebSocket event handlers
@frappe.whitelist()
def join_workload_room(room):
    """Handle user joining a workload room"""
    user_id = frappe.session.user
    realtime_manager.join_room(user_id, room)
    
    return {
        'success': True,
        'room': room,
        'active_users': realtime_manager.get_active_users(room)
    }


@frappe.whitelist()
def leave_workload_room(room):
    """Handle user leaving a workload room"""
    user_id = frappe.session.user
    realtime_manager.leave_room(user_id, room)
    
    return {'success': True, 'room': room}


@frappe.whitelist()
def get_active_users_in_room(room):
    """Get active users in a specific room"""
    return realtime_manager.get_active_users(room)


@frappe.whitelist()
def broadcast_user_activity(activity_type, activity_data=None):
    """Broadcast user activity (typing, viewing, etc.)"""
    
    user_id = frappe.session.user
    
    activity_message = {
        'user_id': user_id,
        'activity_type': activity_type,
        'activity_data': activity_data or {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Broadcast to relevant rooms
    if user_id in realtime_manager.active_sessions:
        user_rooms = realtime_manager.active_sessions[user_id]['rooms']
        
        for room in user_rooms:
            frappe.publish_realtime(
                event="user_activity",
                message=activity_message,
                room=room,
                after_commit=True
            )
    
    return {'success': True}


# Cleanup function for session management
def cleanup_inactive_sessions():
    """Clean up inactive sessions (called periodically)"""
    
    cutoff_time = datetime.now() - timedelta(minutes=30)
    inactive_users = []
    
    for user_id, session in realtime_manager.active_sessions.items():
        if session['last_activity'] < cutoff_time:
            inactive_users.append(user_id)
    
    # Remove inactive users
    for user_id in inactive_users:
        user_rooms = realtime_manager.active_sessions[user_id]['rooms'].copy()
        
        for room in user_rooms:
            realtime_manager.leave_room(user_id, room)
        
        del realtime_manager.active_sessions[user_id]
    
    return len(inactive_users)
