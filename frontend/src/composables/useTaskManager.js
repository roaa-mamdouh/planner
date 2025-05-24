import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'

export function useTaskManager(department) {
  const tasks = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdate = ref(null)

  // Cache key for local storage
  const CACHE_KEY = `planner_tasks_${department}`
  const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

  // Task statistics
  const taskStats = computed(() => {
    return {
      total: tasks.value.length,
      completed: tasks.value.filter(t => t.status === 'Completed').length,
      inProgress: tasks.value.filter(t => t.status === 'Working').length,
      overdue: tasks.value.filter(t => {
        const endDate = new Date(t.exp_end_date)
        return endDate < new Date() && t.status !== 'Completed'
      }).length
    }
  })

  // Load tasks from cache or API
  const loadTasks = async (forceRefresh = false) => {
    if (!forceRefresh) {
      const cached = loadFromCache()
      if (cached) {
        tasks.value = cached.tasks
        lastUpdate.value = cached.timestamp
        return
      }
    }

    loading.value = true
    error.value = null

    try {
      const resource = createResource({
        url: 'planner.api.get_planner_tasks',
        params: { department },
        onSuccess: (data) => {
          tasks.value = processTaskData(data)
          lastUpdate.value = new Date()
          saveToCache()
        },
        onError: (err) => {
          error.value = err
          console.error('Error loading tasks:', err)
        }
      })

      await resource.submit()
    } finally {
      loading.value = false
    }
  }

  // Process and normalize task data
  const processTaskData = (data) => {
    return data.map(task => ({
      ...task,
      exp_start_date: new Date(task.exp_start_date),
      exp_end_date: new Date(task.exp_end_date),
      color: getTaskColor(task.status),
      assigned_to: task.assigned_to || 'Unassigned'
    }))
  }

  // Update task
  const updateTask = async (taskId, updates) => {
    loading.value = true
    error.value = null

    try {
      const resource = createResource({
        url: 'planner.api.update_task',
        params: {
          task_id: taskId,
          updates
        },
        onSuccess: (data) => {
          const index = tasks.value.findIndex(t => t.name === taskId)
          if (index !== -1) {
            tasks.value[index] = {
              ...tasks.value[index],
              ...updates
            }
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

  // Batch update tasks
  const batchUpdateTasks = async (updates) => {
    loading.value = true
    error.value = null

    try {
      const resource = createResource({
        url: 'planner.api.batch_update_tasks',
        params: { updates },
        onSuccess: (data) => {
          updates.forEach(update => {
            const index = tasks.value.findIndex(t => t.name === update.task_id)
            if (index !== -1) {
              tasks.value[index] = {
                ...tasks.value[index],
                ...update.changes
              }
            }
          })
          saveToCache()
        },
        onError: (err) => {
          error.value = err
          console.error('Error batch updating tasks:', err)
        }
      })

      await resource.submit()
    } finally {
      loading.value = false
    }
  }

  // Cache management
  const saveToCache = () => {
    const cacheData = {
      tasks: tasks.value,
      timestamp: new Date().getTime()
    }
    localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData))
  }

  const loadFromCache = () => {
    const cached = localStorage.getItem(CACHE_KEY)
    if (!cached) return null

    const { tasks: cachedTasks, timestamp } = JSON.parse(cached)
    const now = new Date().getTime()

    if (now - timestamp > CACHE_DURATION) {
      localStorage.removeItem(CACHE_KEY)
      return null
    }

    return { tasks: cachedTasks, timestamp }
  }

  // Utility functions
  const getTaskColor = (status) => {
    const colors = {
      'Completed': '#10B981', // green
      'Working': '#3B82F6',   // blue
      'Overdue': '#EF4444',   // red
      'Not Started': '#6B7280' // gray
    }
    return colors[status] || colors['Not Started']
  }

  // Filter and search
  const filterTasks = (filters) => {
    return tasks.value.filter(task => {
      let matches = true
      
      if (filters.status && filters.status.length > 0) {
        matches = matches && filters.status.includes(task.status)
      }
      
      if (filters.search) {
        const search = filters.search.toLowerCase()
        matches = matches && (
          task.subject.toLowerCase().includes(search) ||
          task.project?.toLowerCase().includes(search) ||
          task.assigned_to.toLowerCase().includes(search)
        )
      }
      
      if (filters.dateRange) {
        const start = new Date(filters.dateRange.start)
        const end = new Date(filters.dateRange.end)
        const taskStart = new Date(task.exp_start_date)
        matches = matches && (taskStart >= start && taskStart <= end)
      }
      
      return matches
    })
  }

  // Initialize
  loadTasks()

  return {
    tasks,
    loading,
    error,
    lastUpdate,
    taskStats,
    loadTasks,
    updateTask,
    batchUpdateTasks,
    filterTasks
  }
}
