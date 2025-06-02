import { ref, computed, watch, nextTick } from 'vue'
import { createResource } from 'frappe-ui'
import { useErrorHandler } from '@/services/errorHandler'

export function useWorkloadManager(initialDepartment) {
  // Core state
  const department = ref(initialDepartment)
  const assignees = ref([])
  const tasks = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdate = ref(null)

  const { addError } = useErrorHandler()

  // Cache configuration
  const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
  const getCacheKey = (dept) => `workload_data_${dept || 'default'}`

  // Utility functions
  const formatDateForAPI = (date) => {
    if (!date) return null
    if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return date
    }
    const d = new Date(date)
    return d.getFullYear() + '-' + 
           String(d.getMonth() + 1).padStart(2, '0') + '-' + 
           String(d.getDate()).padStart(2, '0')
  }

  const parseDate = (dateStr) => {
    if (!dateStr) return null
    return new Date(dateStr)
  }

  // Watch department changes
  watch(() => department.value, (newDept, oldDept) => {
    if (newDept !== oldDept) {
      console.log("Department changed:", newDept)
      clearCache()
      loadWorkloadData(null, null, true)
    }
  })

  // Computed properties
  const workloadStats = computed(() => {
    const totalTasks = tasks.value.length
    const scheduledTasks = tasks.value.filter(t => t.isScheduled).length
    const unscheduledTasks = totalTasks - scheduledTasks
    const overdueTasks = tasks.value.filter(t => t.isOverdue).length
    
    const totalCapacity = assignees.value.reduce((sum, a) => sum + (a.capacity || 0), 0)
    const totalScheduledHours = tasks.value
      .filter(t => t.isScheduled)
      .reduce((sum, t) => sum + (t.duration || 0), 0)
    
    const overallUtilization = totalCapacity > 0 ? (totalScheduledHours / totalCapacity) * 100 : 0
    
    return {
      totalAssignees: assignees.value.length,
      totalTasks,
      scheduledTasks,
      unscheduledTasks,
      overdueTasks,
      totalCapacity,
      totalScheduledHours,
      overallUtilization: Math.round(overallUtilization),
      averageUtilization: assignees.value.length > 0 
        ? Math.round(assignees.value.reduce((sum, a) => sum + (a.utilization || 0), 0) / assignees.value.length)
        : 0
    }
  })

  const overallocatedAssignees = computed(() => {
    return assignees.value.filter(assignee => (assignee.utilization || 0) > 120)
  })

  const underutilizedAssignees = computed(() => {
    return assignees.value.filter(assignee => {
      const util = assignee.utilization || 0
      return util < 70 && util > 0
    })
  })

  // Data processing functions
const processTaskData = (rawTasks) => {
  if (!Array.isArray(rawTasks)) {
    console.error("Invalid tasks data received:", rawTasks)
    return []
  }
  return rawTasks.map(task => {
      const startDate = parseDate(task.startDate || task.exp_start_date)
      const endDate = parseDate(task.endDate || task.exp_end_date)
      
      // Calculate duration in days
      const durationDays = startDate && endDate 
        ? Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1 
        : 0

      // Handle assignee from _assign field
      let assignee = task.assignee || 'unassigned'
      if (task._assign) {
        try {
          const assignees = typeof task._assign === 'string' ? 
            JSON.parse(task._assign) : task._assign
          
          if (Array.isArray(assignees) && assignees.length > 0) {
            assignee = assignees[0]
          }
        } catch (e) {
          console.error(`Error parsing _assign for task ${task.name}:`, e)
        }
      }

      // Check if task is overdue
      const now = new Date()
      const isOverdue = endDate && endDate < now && task.status !== 'Completed'

      return {
        id: task.id || task.name,
        name: task.name,
        title: task.title || task.subject || "Untitled Task",
        startDate,
        endDate,
        assignee: assignee || 'unassigned',
        duration: parseFloat(task.duration || task.expected_time || 0),
        durationDays,
        isScheduled: !!(startDate && endDate),
        isOverdue,
        project: task.project || "",
        status: task.status || "Open",
        priority: task.priority || "Medium",
        color: task.color || "#6B7280",
        description: task.description || ""
      }
    })
  }

const processAssigneeData = (rawAssignees) => {
  if (!Array.isArray(rawAssignees)) {
    console.error("Invalid assignees data received:", rawAssignees)
    return []
  }
  return rawAssignees.map(assignee => {
      const processed = {
        id: assignee.id || assignee.employee_id,
        employee_id: assignee.employee_id,
        name: assignee.name || "Unknown",
        email: assignee.email || "",
        image: assignee.image,
        role: assignee.role || "Employee",
        department: assignee.department,
        company: assignee.company,
        capacity: parseFloat(assignee.capacity || 0),
        total_capacity: parseFloat(assignee.total_capacity || assignee.capacity || 0),
        working_hours: assignee.working_hours || {
          hours_per_day: 8,
          days_per_week: 5,
          start_time: "09:00",
          end_time: "17:00"
        },
        availability: parseFloat(assignee.availability || 0)
      }

      // Calculate utilization
      processed.utilization = calculateUtilization(processed.id)
      
      return processed
    })
  }

  // Main data loading function
  const loadWorkloadData = async (startDate = null, endDate = null, forceRefresh = false) => {
    console.log("Loading workload data for department:", department.value)

    // Check cache first
    if (!forceRefresh) {
      const cached = loadFromCache()
      if (cached) {
        console.log("Using cached data")
        assignees.value = cached.assignees
        tasks.value = cached.tasks
        lastUpdate.value = cached.timestamp
        return
      }
    }

    loading.value = true
    error.value = null

    try {
      const resource = createResource({
        url: 'planner.api.get_workload_data',
        params: { 
          department: department.value,
          start_date: formatDateForAPI(startDate),
          end_date: formatDateForAPI(endDate)
        },
        onSuccess: (data) => {
          console.log("API Response received:", data)
          
          // Process data
          tasks.value = processTaskData(data.tasks || [])
          assignees.value = processAssigneeData(data.assignees || [])
          
          lastUpdate.value = new Date()
          saveToCache()
          
          console.log(`Processed ${tasks.value.length} tasks and ${assignees.value.length} assignees`)
        },
        onError: (err) => {
          console.error('Error loading workload data:', err)
          error.value = err
          
          // Set empty data
          tasks.value = []
          assignees.value = []
          
          // Add error to error handler
          addError({
            title: 'Workload Data Error',
            message: err.message || 'Failed to load workload data',
            type: 'error'
          })
        }
      })

      await resource.submit()
    } finally {
      loading.value = false
    }
  }

  // Task operations
  const moveTask = async (taskId, assigneeId, startDate = null, endDate = null) => {
    loading.value = true
    error.value = null

    try {
      const resource = createResource({
        url: 'planner.api.move_task',
        params: {
          task_id: taskId,
          assignee_id: assigneeId,
          start_date: formatDateForAPI(startDate),
          end_date: formatDateForAPI(endDate)
        },
        onSuccess: () => {
          // Update local task data
          const taskIndex = tasks.value.findIndex(t => t.id === taskId)
          if (taskIndex !== -1) {
            tasks.value[taskIndex] = {
              ...tasks.value[taskIndex],
              assignee: assigneeId,
              startDate: parseDate(startDate),
              endDate: parseDate(endDate),
              isScheduled: !!(startDate && endDate)
            }
          }
          
          // Recalculate utilizations
          assignees.value = assignees.value.map(a => ({
            ...a,
            utilization: calculateUtilization(a.id)
          }))
          
          saveToCache()
        },
        onError: (err) => {
          error.value = err
          console.error('Error moving task:', err)
        }
      })

      await resource.submit()
    } finally {
      loading.value = false
    }
  }

  const updateTask = async (taskId, updates) => {
    loading.value = true
    error.value = null

    try {
      const formattedUpdates = { ...updates }
      if (formattedUpdates.exp_start_date) {
        formattedUpdates.exp_start_date = formatDateForAPI(formattedUpdates.exp_start_date)
      }
      if (formattedUpdates.exp_end_date) {
        formattedUpdates.exp_end_date = formatDateForAPI(formattedUpdates.exp_end_date)
      }

      const resource = createResource({
        url: 'planner.api.update_task',
        params: {
          task_id: taskId,
          updates: formattedUpdates
        },
        onSuccess: () => {
          const taskIndex = tasks.value.findIndex(t => t.id === taskId)
          if (taskIndex !== -1) {
            tasks.value[taskIndex] = {
              ...tasks.value[taskIndex],
              ...updates
            }
          }
          
          // Recalculate utilizations if needed
          if (updates.duration !== undefined || updates.startDate !== undefined || updates.endDate !== undefined) {
            assignees.value = assignees.value.map(a => ({
              ...a,
              utilization: calculateUtilization(a.id)
            }))
          }
          
          saveToCache()
        },
        onError: (err) => {
          error.value = err
          console.error('Error updating task:', err)
        }
      })

      await resource.submit()
    } finally {
      loading.value = false
    }
  }

  // Utility functions
  const calculateUtilization = (assigneeId) => {
    const assignee = assignees.value.find(a => a.id === assigneeId)
    if (!assignee || assignee.capacity === 0) return 0

    const assigneeTasks = tasks.value.filter(t => t.assignee === assigneeId && t.isScheduled)
    const scheduledHours = assigneeTasks.reduce((sum, t) => sum + (t.duration || 0), 0)
    
    return Math.round((scheduledHours / assignee.capacity) * 100)
  }

  const getTasksForAssignee = (assigneeId, filters = {}) => {
    let assigneeTasks = tasks.value.filter(t => t.assignee === assigneeId)
    
    if (filters.scheduled !== undefined) {
      assigneeTasks = assigneeTasks.filter(t => t.isScheduled === filters.scheduled)
    }
    
    if (filters.status) {
      assigneeTasks = assigneeTasks.filter(t => filters.status.includes(t.status))
    }
    
    return assigneeTasks
  }

  const getTasksInDateRange = (startDate, endDate) => {
    return tasks.value.filter(task => {
      if (!task.startDate || !task.endDate) return false
      
      return (
        (task.startDate >= startDate && task.startDate <= endDate) ||
        (task.endDate >= startDate && task.endDate <= endDate) ||
        (task.startDate <= startDate && task.endDate >= endDate)
      )
    })
  }

  // Cache management
  const saveToCache = () => {
    const cacheData = {
      assignees: assignees.value,
      tasks: tasks.value,
      timestamp: new Date().getTime()
    }
    try {
      localStorage.setItem(getCacheKey(department.value), JSON.stringify(cacheData))
    } catch (e) {
      console.warn('Failed to save to cache:', e)
    }
  }

  const loadFromCache = () => {
    try {
      const cached = localStorage.getItem(getCacheKey(department.value))
      if (!cached) return null

      const { assignees: cachedAssignees, tasks: cachedTasks, timestamp } = JSON.parse(cached)
      const now = new Date().getTime()

      if (now - timestamp > CACHE_DURATION) {
        clearCache()
        return null
      }

      return { 
        assignees: cachedAssignees, 
        tasks: cachedTasks, 
        timestamp 
      }
    } catch (e) {
      console.warn('Failed to load from cache:', e)
      return null
    }
  }

  const clearCache = () => {
    try {
      localStorage.removeItem(getCacheKey(department.value))
    } catch (e) {
      console.warn('Failed to clear cache:', e)
    }
  }

  // Initialize data loading
  const init = async () => {
    console.log("Initializing workload manager for department:", department.value)
    if (department.value) {
      await loadWorkloadData(null, null, true)
    }
  }

  // Call init on creation
  init()

  // Watch department changes
  watch(department, (newDept, oldDept) => {
    if (newDept && newDept !== oldDept) {
      console.log("Department changed, reloading data:", newDept)
      clearCache()
      loadWorkloadData(null, null, true)
    }
  }, { immediate: true })

  return {
    // State
    department,
    assignees,
    tasks,
    loading,
    error,
    lastUpdate,
    
    // Computed
    workloadStats,
    overallocatedAssignees,
    underutilizedAssignees,
    
    // Methods
    loadWorkloadData,
    moveTask,
    updateTask,
    clearCache,
    
    // Utility methods
    getTasksForAssignee,
    getTasksInDateRange,
    calculateUtilization,
    formatDateForAPI
  }
}