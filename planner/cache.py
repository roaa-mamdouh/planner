import frappe
from frappe.utils import cint
from datetime import datetime, timedelta

CACHE_KEYS = {
    'PLANNER_TASKS': 'planner_tasks_{department}',
    'TASK_STATS': 'task_stats_{department}',
    'USER_PREFERENCES': 'planner_preferences_{user}'
}

CACHE_EXPIRY = {
    'PLANNER_TASKS': 300,  # 5 minutes
    'TASK_STATS': 600,     # 10 minutes
    'USER_PREFERENCES': 3600  # 1 hour
}

def get_cached_tasks(department=None):
    """Get tasks from cache or fetch from database"""
    cache_key = CACHE_KEYS['PLANNER_TASKS'].format(department=department or 'all')
    tasks = frappe.cache().get_value(cache_key)
    
    if tasks is None:
        # Cache miss - fetch from database
        tasks = fetch_and_cache_tasks(department)
    
    return tasks

def fetch_and_cache_tasks(department=None):
    """Fetch tasks from database and update cache"""
    from .api import get_planner_tasks
    
    tasks = get_planner_tasks(department)
    cache_key = CACHE_KEYS['PLANNER_TASKS'].format(department=department or 'all')
    
    frappe.cache().set_value(
        cache_key,
        tasks,
        expires_in_sec=CACHE_EXPIRY['PLANNER_TASKS']
    )
    
    return tasks

def get_cached_stats(department=None):
    """Get task statistics from cache or compute"""
    cache_key = CACHE_KEYS['TASK_STATS'].format(department=department or 'all')
    stats = frappe.cache().get_value(cache_key)
    
    if stats is None:
        # Cache miss - compute stats
        stats = compute_and_cache_stats(department)
    
    return stats

def compute_and_cache_stats(department=None):
    """Compute task statistics and update cache"""
    tasks = get_cached_tasks(department)
    now = datetime.now()
    
    stats = {
        'total': len(tasks),
        'completed': sum(1 for task in tasks if task.status == 'Completed'),
        'in_progress': sum(1 for task in tasks if task.status == 'Working'),
        'overdue': sum(1 for task in tasks if (
            task.status != 'Completed' and 
            task.exp_end_date and 
            datetime.strptime(str(task.exp_end_date), '%Y-%m-%d') < now
        )),
        'by_priority': {
            'high': sum(1 for task in tasks if task.priority == 'High'),
            'medium': sum(1 for task in tasks if task.priority == 'Medium'),
            'low': sum(1 for task in tasks if task.priority == 'Low')
        },
        'last_updated': str(now)
    }
    
    cache_key = CACHE_KEYS['TASK_STATS'].format(department=department or 'all')
    frappe.cache().set_value(
        cache_key,
        stats,
        expires_in_sec=CACHE_EXPIRY['TASK_STATS']
    )
    
    return stats

def get_user_preferences(user=None):
    """Get user preferences from cache"""
    if not user:
        user = frappe.session.user
    
    cache_key = CACHE_KEYS['USER_PREFERENCES'].format(user=user)
    prefs = frappe.cache().get_value(cache_key)
    
    if prefs is None:
        # Cache miss - fetch preferences
        prefs = fetch_and_cache_preferences(user)
    
    return prefs

def fetch_and_cache_preferences(user):
    """Fetch user preferences and update cache"""
    default_prefs = {
        'view_mode': 'week',
        'show_completed': True,
        'color_scheme': 'default',
        'task_grouping': 'status',
        'notifications_enabled': True
    }
    
    # Try to get saved preferences from DocType
    try:
        saved_prefs = frappe.get_doc(
            'Planner Settings',
            {'user': user}
        )
        if saved_prefs:
            prefs = {
                'view_mode': saved_prefs.get('default_view') or default_prefs['view_mode'],
                'show_completed': cint(saved_prefs.get('show_completed')),
                'color_scheme': saved_prefs.get('color_scheme') or default_prefs['color_scheme'],
                'task_grouping': saved_prefs.get('task_grouping') or default_prefs['task_grouping'],
                'notifications_enabled': cint(saved_prefs.get('notifications_enabled'))
            }
        else:
            prefs = default_prefs
    except frappe.DoesNotExistError:
        prefs = default_prefs
    
    cache_key = CACHE_KEYS['USER_PREFERENCES'].format(user=user)
    frappe.cache().set_value(
        cache_key,
        prefs,
        expires_in_sec=CACHE_EXPIRY['USER_PREFERENCES']
    )
    
    return prefs

def clear_task_cache(department=None):
    """Clear task-related caches"""
    cache_key = CACHE_KEYS['PLANNER_TASKS'].format(department=department or 'all')
    stats_key = CACHE_KEYS['TASK_STATS'].format(department=department or 'all')
    
    frappe.cache().delete_value(cache_key)
    frappe.cache().delete_value(stats_key)

def clear_user_cache(user=None):
    """Clear user-specific cache"""
    if not user:
        user = frappe.session.user
    
    cache_key = CACHE_KEYS['USER_PREFERENCES'].format(user=user)
    frappe.cache().delete_value(cache_key)

def invalidate_all_caches():
    """Invalidate all planner-related caches"""
    departments = frappe.get_all('Department', pluck='name')
    
    # Clear task caches for all departments
    for dept in departments:
        clear_task_cache(dept)
    
    # Clear global task cache
    clear_task_cache()
    
    # Clear user preference caches
    users = frappe.get_all('User', pluck='name')
    for user in users:
        clear_user_cache(user)
