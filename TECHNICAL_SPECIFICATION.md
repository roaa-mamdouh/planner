# 📋 WORKLOAD MANAGEMENT SYSTEM - TECHNICAL SPECIFICATION

## Executive Summary

This document provides a comprehensive technical specification for transforming your current planner application into a world-class workload management system. The redesign addresses critical performance bottlenecks, introduces AI-powered features, and implements real-time collaboration capabilities that surpass ClickUp's functionality.

---

## 🔍 Current System Analysis

### Architecture Assessment

**Current Tech Stack:**
- **Backend**: Python (Frappe Framework), MariaDB
- **Frontend**: Vue 3 + Composition API, Vite, TailwindCSS
- **UI Library**: frappe-ui components
- **Timeline**: vis-timeline library
- **Real-time**: Basic WebSocket via frappe.publish_realtime

### Critical Issues Identified

#### 1. Backend Performance Problems

**API Response Times:**
- Current: 2-5 seconds for 100+ tasks
- Target: <500ms for 1000+ tasks

**Database Query Issues:**
```python
# CURRENT PROBLEM in planner/api.py
def get_all_tasks(department=None, start_date=None, end_date=None):
    # Issues:
    # 1. Multiple separate queries (N+1 problem)
    # 2. No query optimization or indexing
    # 3. JSON parsing in Python loops
    # 4. No caching mechanism
    # 5. Inefficient data processing
```

#### 2. Frontend Memory Issues

**Performance Bottlenecks:**
- Memory leaks in timeline components
- No virtualization for large datasets
- Inefficient state management
- Poor mobile performance

#### 3. Real-time Limitations

**Current Limitations:**
- Basic event emission without targeting
- No conflict resolution
- No connection state management
- Limited scalability

---

## 🏗️ Proposed Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Vue 3 + Composition API + Pinia State Management          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Desktop   │ │   Tablet    │ │   Mobile    │          │
│  │  Workload   │ │  Workload   │ │  Workload   │          │
│  │    View     │ │    View     │ │    View     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │           Real-time Collaboration Layer                ││
│  │  WebSocket + Socket.IO + Conflict Resolution           ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     API LAYER                               │
├─────────────────────────────────────────────────────────────┤
│  High-Performance REST APIs + GraphQL (Optional)           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Workload   │ │     AI      │ │  Real-time  │          │
│  │   Manager   │ │   Engine    │ │   Manager   │          │
│  │     V2      │ │             │ │     V2      │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Caching Layer (Redis)                     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Enhanced MariaDB Schema with Optimized Indexes            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │    Task     │ │  Workload   │ │ Analytics   │          │
│  │  Timeline   │ │  Capacity   │ │   Events    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema Design

### Enhanced Schema Architecture

#### 1. Workload Capacity Table
```sql
CREATE TABLE `tabWorkload_Capacity` (
    `name` varchar(140) PRIMARY KEY,
    `employee` varchar(140) NOT NULL,
    `date` date NOT NULL,
    `available_hours` decimal(8,2) DEFAULT 8.00,
    `allocated_hours` decimal(8,2) DEFAULT 0.00,
    `utilization_percent` decimal(5,2) DEFAULT 0.00,
    `is_holiday` tinyint(1) DEFAULT 0,
    `is_leave` tinyint(1) DEFAULT 0,
    `overtime_hours` decimal(8,2) DEFAULT 0.00,
    `efficiency_rating` decimal(3,2) DEFAULT 1.00,
    `created` datetime DEFAULT CURRENT_TIMESTAMP,
    `modified` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Performance Indexes
    INDEX `idx_employee_date` (`employee`, `date`),
    INDEX `idx_date_utilization` (`date`, `utilization_percent`),
    INDEX `idx_capacity_lookup` (`employee`, `date`, `available_hours`),
    UNIQUE KEY `unique_employee_date` (`employee`, `date`)
);
```

#### 2. Enhanced Task Timeline
```sql
CREATE TABLE `tabTask_Timeline` (
    `name` varchar(140) PRIMARY KEY,
    `task` varchar(140) NOT NULL,
    `assignee` varchar(140),
    `start_date` datetime,
    `end_date` datetime,
    `estimated_hours` decimal(8,2),
    `actual_hours` decimal(8,2) DEFAULT 0.00,
    `progress_percent` decimal(5,2) DEFAULT 0.00,
    `dependencies` json,
    `priority_score` int DEFAULT 50,
    `complexity_rating` enum('Low','Medium','High','Critical') DEFAULT 'Medium',
    `skill_requirements` json,
    `created` datetime DEFAULT CURRENT_TIMESTAMP,
    `modified` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Optimized Indexes
    INDEX `idx_task_assignee` (`task`, `assignee`),
    INDEX `idx_assignee_dates` (`assignee`, `start_date`, `end_date`),
    INDEX `idx_timeline_lookup` (`start_date`, `end_date`, `assignee`),
    INDEX `idx_priority_complexity` (`priority_score`, `complexity_rating`)
);
```

#### 3. Real-time Events Tracking
```sql
CREATE TABLE `tabWorkload_Events` (
    `name` varchar(140) PRIMARY KEY,
    `event_type` varchar(50) NOT NULL,
    `entity_type` varchar(50) NOT NULL,
    `entity_id` varchar(140) NOT NULL,
    `user` varchar(140),
    `session_id` varchar(140),
    `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
    `data` json,
    `processed` tinyint(1) DEFAULT 0,
    
    -- Event Processing Indexes
    INDEX `idx_timestamp` (`timestamp`),
    INDEX `idx_entity` (`entity_type`, `entity_id`),
    INDEX `idx_user_session` (`user`, `session_id`),
    INDEX `idx_event_processing` (`processed`, `timestamp`)
);
```

#### 4. Analytics Storage
```sql
CREATE TABLE `tabWorkload_Analytics` (
    `name` varchar(140) PRIMARY KEY,
    `department` varchar(140),
    `date` date NOT NULL,
    `metric_type` varchar(50) NOT NULL,
    `metric_value` decimal(10,4),
    `metadata` json,
    `created` datetime DEFAULT CURRENT_TIMESTAMP,
    
    INDEX `idx_dept_date_metric` (`department`, `date`, `metric_type`),
    INDEX `idx_analytics_lookup` (`date`, `metric_type`, `metric_value`)
);
```

---

## 🚀 Backend API Specification

### High-Performance API Architecture

#### 1. Workload Manager V2

**File: planner/api_v2.py**

```python
import frappe
from frappe.query_builder import DocType
from frappe.cache_manager import redis_cache
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from datetime import datetime, timedelta

@dataclass
class WorkloadMetrics:
    total_capacity: float
    allocated_hours: float
    utilization_percent: float
    overallocation_hours: float
    available_hours: float
    efficiency_score: float

class WorkloadManagerV2:
    """High-performance workload management with intelligent caching"""
    
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
    
    if isinstance(updates, str):
        updates = json.loads(updates)
    
    updated_tasks = []
    
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
                updated_tasks.append(task_doc.as_dict())
        
        # Emit real-time updates
        from planner.realtime_v2 import emit_batch_update_v2
        emit_batch_update_v2(updated_tasks)
        
        # Clear cache
        clear_workload_cache()
        
        return {'updated_count': len(updated_tasks), 'tasks': updated_tasks}
        
    except Exception as e:
        frappe.log_error(f"Bulk update error: {str(e)}")
        frappe.throw(f"Failed to update tasks: {str(e)}")
```

#### 2. AI Analytics Engine

**File: planner/ai_engine.py**

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import frappe
from datetime import datetime, timedelta
import json

class WorkloadAIEngine:
    """AI engine for intelligent workload management and predictions"""
    
    def __init__(self):
        self.capacity_model = None
        self.productivity_model = None
        self.completion_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def generate_capacity_recommendations(self, department: str = None) -> List[Dict]:
        """Generate AI-powered capacity recommendations"""
        
        workload_data = self._get_current_workload_data(department)
        patterns = self._analyze_workload_patterns(workload_data)
        
        recommendations = []
        
        # 1. Overallocation Detection
        overallocated = self._detect_overallocation(patterns)
        if overallocated:
            recommendations.append({
                'id': 'overallocation_warning',
                'type': 'capacity_warning',
                'severity': 'high',
                'title': 'Team Members Overallocated',
                'message': f'{len(overallocated)} team members are overallocated (>100% capacity)',
                'impact': 'High risk of burnout and missed deadlines',
                'suggested_actions': [
                    {
                        'action': 'redistribute_tasks',
                        'description': 'Redistribute tasks to available team members',
                        'effort': 'medium',
                        'impact': 'high'
                    },
                    {
                        'action': 'extend_deadlines',
                        'description': 'Negotiate deadline extensions for non-critical tasks',
                        'effort': 'low',
                        'impact': 'medium'
                    }
                ],
                'affected_employees': [emp['name'] for emp in overallocated],
                'priority': 1
            })
        
        # 2. Capacity Optimization
        underutilized = self._detect_underutilization(patterns)
        if underutilized:
            available_hours = sum(emp['available_capacity'] for emp in underutilized)
            recommendations.append({
                'id': 'capacity_optimization',
                'type': 'optimization',
                'severity': 'medium',
                'title': 'Available Capacity Detected',
                'message': f'{available_hours:.1f} hours of available capacity',
                'suggested_actions': [
                    {
                        'action': 'assign_tasks',
                        'description': 'Assign additional tasks to optimize utilization',
                        'effort': 'low',
                        'impact': 'medium'
                    }
                ],
                'priority': 3
            })
        
        # 3. Bottleneck Analysis
        bottlenecks = self._identify_bottlenecks(patterns)
        if bottlenecks:
            recommendations.append({
                'id': 'bottleneck_detection',
                'type': 'bottleneck',
                'severity': 'high',
                'title': 'Workflow Bottlenecks Detected',
                'message': f'{len(bottlenecks)} potential bottlenecks identified',
                'bottlenecks': bottlenecks,
                'priority': 2
            })
        
        return sorted(recommendations, key=lambda x: x.get('priority', 5))
    
    def predict_task_completion(self, task_data: Dict) -> Dict:
        """Predict task completion time using ML"""
        
        if not self.is_trained:
            self._train_models()
        
        features = self._extract_task_features(task_data)
        
        if self.completion_model:
            predicted_hours = self.completion_model.predict([features])[0]
            confidence = self._calculate_prediction_confidence(features)
            
            return {
                'predicted_hours': round(predicted_hours, 2),
                'confidence': round(confidence * 100, 1),
                'original_estimate': task_data.get('estimated_hours', 0),
                'variance': round(abs(predicted_hours - task_data.get('estimated_hours', 0)), 2),
                'factors': self._get_feature_importance(features),
                'recommendation': self._get_estimation_recommendation(predicted_hours, task_data.get('estimated_hours', 0))
            }
        
        return {'error': 'Prediction model not available'}

# API Endpoints
@frappe.whitelist()
def get_ai_recommendations(department=None):
    """API endpoint for AI recommendations"""
    try:
        ai_engine = WorkloadAIEngine()
        return ai_engine.generate_capacity_recommendations(department)
    except Exception as e:
        frappe.log_error(f"AI recommendations error: {str(e)}")
        return {'error': str(e)}

@frappe.whitelist()
def predict_task_completion_time(task_id):
    """API endpoint for task completion prediction"""
    try:
        task_doc = frappe.get_doc('Task', task_id)
        
        task_data = {
            'estimated_hours': task_doc.expected_time,
            'priority': task_doc.priority,
            'assignee': task_doc._assign,
            'project': task_doc.project
        }
        
        ai_engine = WorkloadAIEngine()
        return ai_engine.predict_task_completion(task_data)
        
    except Exception as e:
        frappe.log_error(f"Task prediction error: {str(e)}")
        return {'error': str(e)}
```

---

## 🎯 Frontend Architecture Specification

### State Management with Pinia

**File: stores/workloadStore.js**

```javascript
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { WorkloadAPI } from '@/api/workload'
import { useToast } from 'vue-toastification'

export const useWorkloadStore = defineStore('workload', () => {
  // Core State
  const assignees = ref([])
  const tasks = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdate = ref(null)
  const aiInsights = ref(null)
  
  // Filters
  const filters = ref({
    department: null,
    dateRange: {
      start: new Date(),
      end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
    },
    status: ['Open', 'Working', 'Pending Review'],
    priority: ['High', 'Medium', 'Low'],
    assignees: [],
    projects: []
  })
  
  // Real-time State
  const socket = ref(null)
  const isConnected = ref(false)
  const activeUsers = ref([])
  const recentChanges = ref([])
  
  // Performance Metrics
  const performanceMetrics = ref({
    loadTime: 0,
    renderTime: 0,
    memoryUsage: 0,
    cacheHitRate: 0
  })
  
  // Computed Properties
  const workloadMetrics = computed(() => {
    const totalCapacity = assignees.value.reduce((sum, a) => sum + (a.capacity || 0), 0)
    const totalAllocated = tasks.value
      .filter(t => t.isScheduled)
      .reduce((sum, t) => sum + (t.duration || 0), 0)
    
    const overallocatedCount = assignees.value.filter(a => (a.utilization || 0) > 100).length
    const underutilizedCount = assignees.value.filter(a => (a.utilization || 0) < 70 && (a.utilization || 0) > 0).length
    
    return {
      totalCapacity,
      totalAllocated,
      utilization: totalCapacity > 0 ? (totalAllocated / totalCapacity) * 100 : 0,
      availableCapacity: Math.max(0, totalCapacity - totalAllocated),
      overallocatedCount,
      underutilizedCount,
      totalTasks: tasks.value.length,
      scheduledTasks: tasks.value.filter(t => t.isScheduled).length,
      unscheduledTasks: tasks.value.filter(t => !t.isScheduled).length,
      completedTasks: tasks.value.filter(t => t.status === 'Completed').length,
      overdueTasks: tasks.value.filter(t => t.isOverdue).length
    }
  })
  
  // Actions
  const loadWorkloadData = async (forceRefresh = false) => {
    const startTime = performance.now()
    
    if (loading.value && !forceRefresh) return
    
    loading.value = true
    error.value = null
    
    try {
      const data = await WorkloadAPI.getWorkloadDataV2({
        department: filters.value.department,
        start_date: filters.value.dateRange.start?.toISOString().split('T')[0],
        end_date: filters.value.dateRange.end?.toISOString().split('T')[0],
        force_refresh: forceRefresh
      })
      
      // Update state
      assignees.value = data.assignees || []
      tasks.value = data.tasks || []
      aiInsights.value = data.ai_insights || null
      lastUpdate.value = new Date(data.cache_timestamp)
      
      // Track performance
      const loadTime = performance.now() - startTime
      performanceMetrics.value.loadTime = loadTime
      
      console.log(`Workload data loaded in ${loadTime.toFixed(2)}ms`)
      
    } catch (err) {
      error.value = err.message
      console.error('Failed to load workload data:', err)
      useToast().error(`Failed to load workload data: ${err.message}`)
    } finally {
      loading.value = false
    }
  }
  
  const moveTask = async (taskId, assigneeId, startDate, endDate) => {
    try {
      // Optimistic update
      const taskIndex = tasks.value.findIndex(t => t.id === taskId)
      if (taskIndex !== -1) {
        const originalTask = { ...tasks.value[taskIndex] }
        
        // Update locally first
        tasks.value[taskIndex] = {
          ...tasks.value[taskIndex],
          assignee: assigneeId,
          startDate,
          endDate,
          isScheduled: !!(startDate && endDate)
        }
        
        try {
          // Send to server
          const result = await WorkloadAPI.moveTaskV2({
            task_id: taskId,
            assignee_id: assigneeId,
            start_date: startDate,
            end_date: endDate
          })
          
          // Update with server response
          tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...result.task }
          
          useToast().success('Task moved successfully')
          return result
          
        } catch (error) {
          // Revert optimistic update on error
          tasks.value[taskIndex] = originalTask
          throw error
        }
      }
    } catch (error) {
      useToast().error(`Failed to move task: ${error.message}`)
      throw error
    }
  }
  
  // Real-time functionality
  const initializeRealtime = () => {
    if (socket.value) return
    
    socket.value = io('/workload', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    })
    
    socket.value.on('connect', () => {
      isConnected.value = true
      console.log('Workload real-time connected')
      
      // Join department room
      if (filters.value.department) {
        socket.value.emit('join_room', `workload_${filters.value.department}`)
      }
    })
    
    socket.value.on('disconnect', () => {
      isConnected.value = false
      console.log('Workload real-time disconnected')
    })
    
    socket.value.on('task_update', handleTaskUpdate)
    socket.value.on('batch_task_update', handleBatchTaskUpdate)
    socket.value.on('capacity_change', handleCapacityChange)
    socket.value.on('user_activity', handleUserActivity)
  }
  
  const handleTaskUpdate = (taskData) => {
    const taskIndex = tasks.value.findIndex(t => t.id === taskData.id)
    if (taskIndex !== -1) {
      tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...taskData }
    } else {
      tasks.value.push(taskData)
    }
    
    // Add to recent changes
    recentChanges.value.unshift({
      type: 'task_update',
      data: taskData,
      timestamp: new Date(),
      user: taskData.user
    })
    
    // Keep only last 10 changes
    if (recentChanges.value.length > 10) {
      recentChanges.value = recentChanges.value.slice(0, 10)
    }
    
    // Recalculate utilization
    recalculateUtilization()
  }
  
  const recalculateUtilization = () => {
    assignees.value.forEach(assignee => {
      const assigneeTasks = tasks.value.filter(t => t.assignee === assignee.id && t.isScheduled)
      const totalHours = assigneeTasks.reduce((sum, t) => sum + (t.duration || 0), 0)
      assignee.totalHours = totalHours
      assignee.utilization = assignee.capacity > 0 ? (totalHours / assignee.capacity) * 100 : 0
    })
  }
  
  return {
    // State
    assignees,
    tasks,
    loading,
    error,
    filters,
    isConnected,
    aiInsights,
    performanceMetrics,
    
    // Computed
    workloadMetrics,
    
    // Actions
    loadWorkloadData,
    moveTask,
    initializeRealtime
  }
})
```

---

## 📱 Mobile-First Design Specification

### Responsive Breakpoints

```css
/* Mobile First Approach */
.workload-view {
  /* Mobile: 320px - 768px */
  @apply flex flex-col;
}

@media (min-width: 768px) {
  /* Tablet: 768px - 1024px */
  .workload-view {
    @apply flex-row;
  }
}

@media (min-width: 1024px) {
  /* Desktop: 1024px+ */
  .workload-view {
    @apply grid grid-cols-12 gap-6;
  }
}
```

### Mobile Component Architecture

**File: components/Mobile/MobileWorkloadView.vue**

```vue
<template>
  <div class="mobile-workload-view">
    <!-- Mobile Header -->
    <div class="mobile-header sticky top-0 z-50 bg-white dark:bg-gray-900 border-b">
      <div class="flex items-center justify-between p-4">
        <h1 class="text-lg font-semibold">Workload</h1>
        <div class="flex items-center gap-2">
          <Button size="sm" @click="showFilters = true">
            <FeatherIcon name="filter" class="w-4 h-4" />
          </Button>
          <Button size="sm" @click="showAI = true">
            <FeatherIcon name="zap" class="
