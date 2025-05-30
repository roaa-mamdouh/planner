import { defineStore } from 'pinia'
import { ref, computed, reactive } from 'vue'
import { call } from 'frappe-ui'

export const useWorkloadStore = defineStore('workload', () => {
  // State
  const workloadData = ref({
    assignees: [],
    tasks: [],
    capacity_data: [],
    metrics: {},
    real_time_metrics: {},
    ai_insights: {},
    cache_timestamp: null,
    data_freshness: 'stale'
  })
  
  const loading = ref(false)
  const error = ref(null)
  const lastUpdated = ref(null)
  
  // Filters and view state
  const filters = reactive({
    department: null,
    start_date: null,
    end_date: null,
    assignee: null,
    status: null,
    priority: null
  })
  
  const viewSettings = reactive({
    timelineView: 'month',
    showUnassigned: true,
    showCompleted: false,
    groupBy: 'assignee',
    sortBy: 'priority',
    zoomLevel: 1.0
  })
  
  // Real-time state
  const activeUsers = ref([])
  const realtimeConnected = ref(false)
  const pendingUpdates = ref([])
  
  // Computed getters
  const filteredTasks = computed(() => {
    let tasks = workloadData.value.tasks || []
    
    // Apply filters
    if (filters.department) {
      const deptAssignees = workloadData.value.assignees
        .filter(a => a.department === filters.department)
        .map(a => a.id)
      tasks = tasks.filter(t => deptAssignees.includes(t.assignee))
    }
    
    if (filters.assignee) {
      tasks = tasks.filter(t => t.assignee === filters.assignee)
    }
    
    if (filters.status) {
      tasks = tasks.filter(t => t.status === filters.status)
    }
    
    if (filters.priority) {
      tasks = tasks.filter(t => t.priority === filters.priority)
    }
    
    if (!viewSettings.showCompleted) {
      tasks = tasks.filter(t => t.status !== 'Completed')
    }
    
    if (!viewSettings.showUnassigned) {
      tasks = tasks.filter(t => t.assignee !== 'unassigned')
    }
    
    return tasks
  })
  
  const filteredAssignees = computed(() => {
    let assignees = workloadData.value.assignees || []
    
    if (filters.department) {
      assignees = assignees.filter(a => a.department === filters.department)
    }
    
    return assignees
  })
  
  const overallocatedAssignees = computed(() => {
    return filteredAssignees.value.filter(a => a.utilization > 100)
  })
  
  const underutilizedAssignees = computed(() => {
    return filteredAssignees.value.filter(a => a.utilization < 70 && a.utilization > 0)
  })
  
  const tasksByStatus = computed(() => {
    const statusGroups = {}
    filteredTasks.value.forEach(task => {
      const status = task.status || 'Unknown'
      if (!statusGroups[status]) {
        statusGroups[status] = []
      }
      statusGroups[status].push(task)
    })
    return statusGroups
  })
  
  const tasksByPriority = computed(() => {
    const priorityGroups = {}
    filteredTasks.value.forEach(task => {
      const priority = task.priority || 'Medium'
      if (!priorityGroups[priority]) {
        priorityGroups[priority] = []
      }
      priorityGroups[priority].push(task)
    })
    return priorityGroups
  })
  
  const capacityMetrics = computed(() => {
    const assignees = filteredAssignees.value
    const totalCapacity = assignees.reduce((sum, a) => sum + (a.capacity || 0), 0)
    const totalAllocated = assignees.reduce((sum, a) => sum + (a.total_hours || 0), 0)
    
    return {
      totalCapacity,
      totalAllocated,
      availableCapacity: Math.max(0, totalCapacity - totalAllocated),
      overallUtilization: totalCapacity > 0 ? (totalAllocated / totalCapacity) * 100 : 0,
      overallocatedCount: overallocatedAssignees.value.length,
      underutilizedCount: underutilizedAssignees.value.length
    }
  })
  
  // Actions
  async function loadWorkloadData(forceRefresh = false) {
    if (loading.value && !forceRefresh) return
    
    loading.value = true
    error.value = null
    
    try {
      const response = await call('planner.api_v2.get_workload_data_v2', {
        department: filters.department,
        start_date: filters.start_date,
        end_date: filters.end_date,
        force_refresh: forceRefresh
      })
      
      workloadData.value = response
      lastUpdated.value = new Date()
      
      // Emit success event
      emitStoreEvent('workload_loaded', { 
        taskCount: response.tasks?.length || 0,
        assigneeCount: response.assignees?.length || 0 
      })
      
    } catch (err) {
      error.value = err.message || 'Failed to load workload data'
      console.error('Workload loading error:', err)
      
      // Emit error event
      emitStoreEvent('workload_error', { error: err.message })
      
    } finally {
      loading.value = false
    }
  }
  
  async function moveTask(taskId, newAssignee, startDate, endDate) {
    try {
      const response = await call('planner.api_v2.move_task_v2', {
        task_id: taskId,
        assignee_id: newAssignee,
        start_date: startDate,
        end_date: endDate
      })
      
      // Update local state optimistically
      updateTaskInStore(response.task, response.timeline)
      
      // Emit success event
      emitStoreEvent('task_moved', { 
        taskId, 
        newAssignee, 
        startDate, 
        endDate 
      })
      
      return response
      
    } catch (err) {
      error.value = err.message || 'Failed to move task'
      throw err
    }
  }
  
  async function bulkUpdateTasks(updates) {
    try {
      const response = await call('planner.api_v2.bulk_update_tasks_v2', {
        updates: updates
      })
      
      // Update local state with returned data
      response.tasks.forEach(task => {
        updateTaskInStore(task)
      })
      
      // Emit success event
      emitStoreEvent('tasks_bulk_updated', { 
        count: response.updated_count 
      })
      
      return response
      
    } catch (err) {
      error.value = err.message || 'Failed to update tasks'
      throw err
    }
  }
  
  function updateTaskInStore(taskData, timelineData = null) {
    const taskIndex = workloadData.value.tasks.findIndex(t => t.id === taskData.name)
    
    if (taskIndex >= 0) {
      // Update existing task
      const updatedTask = {
        ...workloadData.value.tasks[taskIndex],
        title: taskData.subject,
        status: taskData.status,
        priority: taskData.priority,
        project: taskData.project
      }
      
      if (timelineData) {
        updatedTask.assignee = timelineData.assignee || 'unassigned'
        updatedTask.startDate = timelineData.start_date
        updatedTask.endDate = timelineData.end_date
        updatedTask.duration = timelineData.estimated_hours
        updatedTask.progress = timelineData.progress_percent
      }
      
      workloadData.value.tasks[taskIndex] = updatedTask
    }
    
    // Update assignee data if needed
    if (timelineData?.assignee) {
      updateAssigneeInStore(timelineData.assignee)
    }
  }
  
  function updateAssigneeInStore(assigneeId) {
    const assigneeIndex = workloadData.value.assignees.findIndex(a => a.id === assigneeId)
    
    if (assigneeIndex >= 0) {
      // Recalculate assignee metrics
      const assigneeTasks = workloadData.value.tasks.filter(t => t.assignee === assigneeId)
      const totalHours = assigneeTasks.reduce((sum, t) => sum + (t.duration || 0), 0)
      
      workloadData.value.assignees[assigneeIndex].total_hours = totalHours
      
      if (workloadData.value.assignees[assigneeIndex].capacity > 0) {
        workloadData.value.assignees[assigneeIndex].utilization = 
          (totalHours / workloadData.value.assignees[assigneeIndex].capacity) * 100
      }
    }
  }
  
  function addTask(taskData) {
    workloadData.value.tasks.push(taskData)
    
    // Update assignee if specified
    if (taskData.assignee && taskData.assignee !== 'unassigned') {
      updateAssigneeInStore(taskData.assignee)
    }
    
    emitStoreEvent('task_added', { task: taskData })
  }
  
  function removeTask(taskId) {
    const taskIndex = workloadData.value.tasks.findIndex(t => t.id === taskId)
    
    if (taskIndex >= 0) {
      const task = workloadData.value.tasks[taskIndex]
      workloadData.value.tasks.splice(taskIndex, 1)
      
      // Update assignee metrics
      if (task.assignee && task.assignee !== 'unassigned') {
        updateAssigneeInStore(task.assignee)
      }
      
      emitStoreEvent('task_removed', { taskId })
    }
  }
  
  function updateFilters(newFilters) {
    Object.assign(filters, newFilters)
    emitStoreEvent('filters_updated', { filters: { ...filters } })
  }
  
  function updateViewSettings(newSettings) {
    Object.assign(viewSettings, newSettings)
    emitStoreEvent('view_settings_updated', { settings: { ...viewSettings } })
  }
  
  function clearError() {
    error.value = null
  }
  
  function resetStore() {
    workloadData.value = {
      assignees: [],
      tasks: [],
      capacity_data: [],
      metrics: {},
      real_time_metrics: {},
      ai_insights: {},
      cache_timestamp: null,
      data_freshness: 'stale'
    }
    
    Object.assign(filters, {
      department: null,
      start_date: null,
      end_date: null,
      assignee: null,
      status: null,
      priority: null
    })
    
    error.value = null
    lastUpdated.value = null
    activeUsers.value = []
    pendingUpdates.value = []
  }
  
  // Real-time methods
  function handleRealtimeUpdate(eventType, data) {
    switch (eventType) {
      case 'task_update':
      case 'task_moved':
        updateTaskInStore(data.task, data.timeline)
        break
        
      case 'batch_task_update':
        data.tasks.forEach(task => updateTaskInStore(task))
        break
        
      case 'task_created':
        addTask(data.task)
        break
        
      case 'task_deleted':
        removeTask(data.task_id)
        break
        
      case 'capacity_change':
        updateCapacityData(data.assignee_id, data.capacity_data)
        break
        
      case 'workload_alert':
        handleWorkloadAlert(data)
        break
        
      case 'ai_recommendation':
        handleAIRecommendation(data)
        break
        
      default:
        console.log('Unknown realtime event:', eventType, data)
    }
    
    // Add to pending updates for UI notifications
    pendingUpdates.value.push({
      id: Date.now(),
      eventType,
      data,
      timestamp: new Date()
    })
    
    // Limit pending updates
    if (pendingUpdates.value.length > 50) {
      pendingUpdates.value = pendingUpdates.value.slice(-50)
    }
  }
  
  function updateCapacityData(assigneeId, capacityData) {
    const assigneeIndex = workloadData.value.assignees.findIndex(a => a.id === assigneeId)
    
    if (assigneeIndex >= 0) {
      const assignee = workloadData.value.assignees[assigneeIndex]
      
      // Update capacity metrics
      if (capacityData.available_hours !== undefined) {
        assignee.capacity = capacityData.available_hours
      }
      
      if (capacityData.utilization_percent !== undefined) {
        assignee.utilization = capacityData.utilization_percent
      }
      
      workloadData.value.assignees[assigneeIndex] = { ...assignee }
    }
  }
  
  function handleWorkloadAlert(alertData) {
    // Store alerts in real-time metrics
    if (!workloadData.value.real_time_metrics.alerts) {
      workloadData.value.real_time_metrics.alerts = []
    }
    
    workloadData.value.real_time_metrics.alerts.unshift({
      ...alertData,
      id: Date.now(),
      timestamp: new Date()
    })
    
    // Limit alerts
    if (workloadData.value.real_time_metrics.alerts.length > 20) {
      workloadData.value.real_time_metrics.alerts = 
        workloadData.value.real_time_metrics.alerts.slice(0, 20)
    }
    
    emitStoreEvent('workload_alert', alertData)
  }
  
  function handleAIRecommendation(recommendationData) {
    // Store recommendations in AI insights
    if (!workloadData.value.ai_insights.recommendations) {
      workloadData.value.ai_insights.recommendations = []
    }
    
    workloadData.value.ai_insights.recommendations.unshift({
      ...recommendationData.recommendation,
      id: recommendationData.recommendation_id,
      timestamp: new Date(),
      expires_at: recommendationData.expires_at
    })
    
    // Limit recommendations
    if (workloadData.value.ai_insights.recommendations.length > 10) {
      workloadData.value.ai_insights.recommendations = 
        workloadData.value.ai_insights.recommendations.slice(0, 10)
    }
    
    emitStoreEvent('ai_recommendation', recommendationData)
  }
  
  function setRealtimeConnection(connected) {
    realtimeConnected.value = connected
  }
  
  function updateActiveUsers(users) {
    activeUsers.value = users
  }
  
  function clearPendingUpdates() {
    pendingUpdates.value = []
  }
  
  function dismissAlert(alertId) {
    if (workloadData.value.real_time_metrics.alerts) {
      const index = workloadData.value.real_time_metrics.alerts.findIndex(a => a.id === alertId)
      if (index >= 0) {
        workloadData.value.real_time_metrics.alerts.splice(index, 1)
      }
    }
  }
  
  function dismissRecommendation(recommendationId) {
    if (workloadData.value.ai_insights.recommendations) {
      const index = workloadData.value.ai_insights.recommendations.findIndex(r => r.id === recommendationId)
      if (index >= 0) {
        workloadData.value.ai_insights.recommendations.splice(index, 1)
      }
    }
  }
  
  // Event emission helper
  function emitStoreEvent(eventName, data) {
    // Custom event for components to listen to
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(`workload-store:${eventName}`, {
        detail: data
      }))
    }
  }
  
  // Utility methods
  function getTaskById(taskId) {
    return workloadData.value.tasks.find(t => t.id === taskId)
  }
  
  function getAssigneeById(assigneeId) {
    return workloadData.value.assignees.find(a => a.id === assigneeId)
  }
  
  function getTasksForAssignee(assigneeId) {
    return workloadData.value.tasks.filter(t => t.assignee === assigneeId)
  }
  
  function getOverdueTasks() {
    const now = new Date()
    return filteredTasks.value.filter(task => {
      return task.endDate && 
             new Date(task.endDate) < now && 
             task.status !== 'Completed'
    })
  }
  
  function getHighPriorityTasks() {
    return filteredTasks.value.filter(task => 
      task.priority === 'High' || task.priority === 'Urgent'
    )
  }
  
  function getUnscheduledTasks() {
    return filteredTasks.value.filter(task => 
      !task.startDate || !task.endDate
    )
  }
  
  return {
    // State
    workloadData,
    loading,
    error,
    lastUpdated,
    filters,
    viewSettings,
    activeUsers,
    realtimeConnected,
    pendingUpdates,
    
    // Computed
    filteredTasks,
    filteredAssignees,
    overallocatedAssignees,
    underutilizedAssignees,
    tasksByStatus,
    tasksByPriority,
    capacityMetrics,
    
    // Actions
    loadWorkloadData,
    moveTask,
    bulkUpdateTasks,
    updateTaskInStore,
    updateAssigneeInStore,
    addTask,
    removeTask,
    updateFilters,
    updateViewSettings,
    clearError,
    resetStore,
    
    // Real-time
    handleRealtimeUpdate,
    updateCapacityData,
    handleWorkloadAlert,
    handleAIRecommendation,
    setRealtimeConnection,
    updateActiveUsers,
    clearPendingUpdates,
    dismissAlert,
    dismissRecommendation,
    
    // Utilities
    getTaskById,
    getAssigneeById,
    getTasksForAssignee,
    getOverdueTasks,
    getHighPriorityTasks,
    getUnscheduledTasks
  }
})
