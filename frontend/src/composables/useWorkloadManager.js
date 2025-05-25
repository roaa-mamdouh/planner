import { ref, computed, watch, nextTick } from 'vue'
import { createResource } from 'frappe-ui'

export function useWorkloadManager(initialDepartment) {
  const department = ref(initialDepartment)
  const assignees = ref([])
  const tasks = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdate = ref(null)
  const capacityAnalysis = ref(null)

  // Cache management
  const CACHE_KEY = computed(() => `workload_data_${department.value || 'default'}`)
  const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

  // Utility function to format date as YYYY-MM-DD
  const formatDateForAPI = (date) => {
    if (!date) return null
    if (typeof date === 'string') {
      // If it's already a string in YYYY-MM-DD format, return as is
      if (/^\d{4}-\d{2}-\d{2}$/.test(date)) {
        return date
      }
      // Otherwise parse it first
      date = new Date(date)
    }
    const d = new Date(date)
    return d.getFullYear() + '-' + 
           String(d.getMonth() + 1).padStart(2, '0') + '-' + 
           String(d.getDate()).padStart(2, '0')
  }

  // Watch for department changes
  watch(() => department.value, (newDepartment, oldDepartment) => {
    if (newDepartment !== oldDepartment) {
      console.log("\nDepartment changed in workload manager:", newDepartment)
      clearCache()
      loadWorkloadData(null, null, true)
    }
  })

  // Computed properties
  const workloadStats = computed(() => {
    console.log("Computing workload stats...");
    
    const totalTasks = tasks.value.length;
    const scheduledTasks = tasks.value.filter(t => t.isScheduled).length;
    const unscheduledTasks = tasks.value.filter(t => !t.isScheduled).length;
    
    console.log(`Total tasks: ${totalTasks}`);
    console.log(`Scheduled tasks: ${scheduledTasks}`);
    console.log(`Unscheduled tasks: ${unscheduledTasks}`);
    
    const overdueTasks = tasks.value.filter(t => t.isOverdue).length;
    
    const totalCapacity = assignees.value.reduce((sum, a) => sum + a.capacity, 0);
    const totalScheduledHours = tasks.value
      .filter(t => t.isScheduled)
      .reduce((sum, t) => sum + (t.duration || 0), 0);
    
    const overallUtilization = totalCapacity > 0 ? (totalScheduledHours / totalCapacity) * 100 : 0;
    
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
    return assignees.value.filter(assignee => {
      const assigneeTasks = tasks.value.filter(t => t.assignee === assignee.id && t.isScheduled)
      const scheduledHours = assigneeTasks.reduce((sum, t) => sum + (t.duration || 0), 0)
      const utilization = assignee.capacity > 0 ? (scheduledHours / assignee.capacity) * 100 : 0
      return utilization > 120 // Over 120% capacity
    })
  })

  const underutilizedAssignees = computed(() => {
    return assignees.value.filter(assignee => {
      const assigneeTasks = tasks.value.filter(t => t.assignee === assignee.id && t.isScheduled)
      const scheduledHours = assigneeTasks.reduce((sum, t) => sum + (t.duration || 0), 0)
      const utilization = assignee.capacity > 0 ? (scheduledHours / assignee.capacity) * 100 : 0
      return utilization < 70 && utilization > 0 // Under 70% but not zero
    })
  })

  // Load workload data
  const loadWorkloadData = async (startDate = null, endDate = null, forceRefresh = false) => {
    console.log("\n=== Loading Workload Data ===");
    console.log("Department:", department.value);
    console.log("Start Date:", startDate);
    console.log("End Date:", endDate);
    console.log("Force Refresh:", forceRefresh);

    if (!forceRefresh) {
      const cached = loadFromCache();
      if (cached) {
        const now = new Date().getTime();
        const cacheAge = now - cached.timestamp;
        
        // Only use cache if it's fresh (less than CACHE_DURATION old)
        if (cacheAge < CACHE_DURATION) {
          console.log("Using cached data from:", new Date(cached.timestamp));
          console.log("Cache age:", Math.round(cacheAge / 1000), "seconds");
          assignees.value = cached.assignees;
          tasks.value = cached.tasks;
          lastUpdate.value = cached.timestamp;
          return;
        } else {
          console.log("Cache expired, fetching fresh data");
          clearCache();
        }
      }
    }

    loading.value = true;
    error.value = null;

    try {
      console.log("Fetching workload data from API...");
      const resource = createResource({
        url: 'planner.api.get_workload_data',
        params: { 
          department: department.value,
          start_date: startDate,
          end_date: endDate
        },
        onSuccess: (data) => {
          console.log("API Response received");
          console.log("Raw API data:", JSON.stringify(data));
          console.log("Assignees:", data.assignees?.length || 0);
          console.log("Tasks:", data.tasks?.length || 0);
          
          if (!data.tasks || data.tasks.length === 0) {
            console.log("WARNING: No tasks received from API");
          }
          
          if (!data.assignees || data.assignees.length === 0) {
            console.log("WARNING: No assignees received from API");
          }
          
          // Process data in correct order
          tasks.value = processTaskData(data.tasks || []);
          assignees.value = processAssigneeData(data.assignees || []);
          
          // Extra validation
          console.log("Processed tasks count:", tasks.value.length);
          console.log("Unscheduled tasks:", tasks.value.filter(t => !t.isScheduled).length);
          
          lastUpdate.value = new Date();
          saveToCache();
          
          console.log("Data processing completed");
        },
        onError: (err) => {
          error.value = err;
          console.error('Error loading workload data:', err);
          console.error('Error details:', err.message);
        }
      });

      await resource.submit();
    } finally {
      loading.value = false;
    }
  };

  // Process assignee data
  const processAssigneeData = (data) => {
    return data.map(assignee => {
      const processed = {
        ...assignee,
        id: assignee.id || assignee.employee_id,
        name: assignee.name || "Unknown",
        capacity: parseFloat(assignee.capacity || 0)
      }

      // Calculate utilization after tasks are processed
      const assigneeTasks = tasks.value.filter(t => t.assignee === processed.id && t.isScheduled)
      const scheduledHours = assigneeTasks.reduce((sum, t) => sum + (t.duration || 0), 0)
      processed.utilization = processed.capacity > 0 
        ? Math.round((scheduledHours / processed.capacity) * 100)
        : 0

      return processed
    })
  }

  // Process task data
  const processTaskData = (data) => {
    console.log("Processing task data:", data);
    return data.map(task => {
      // Ensure dates are properly converted to Date objects
      const startDate = (task.startDate || task.exp_start_date) ? 
        new Date(task.startDate || task.exp_start_date) : null;
      const endDate = (task.endDate || task.exp_end_date) ? 
        new Date(task.endDate || task.exp_end_date) : null;
      
      // Calculate duration in days for timeline display
      const durationDays = startDate && endDate 
        ? Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1 
        : 0;
      
      // Process assignee data - ensure it's always valid even if empty
      // Convert empty string or empty array to 'unassigned'
      let assignee = task.assignee || null;
      if (task._assign) {
        try {
          // _assign could be a JSON string of an array
          const assignees = typeof task._assign === 'string' ? 
            JSON.parse(task._assign) : task._assign;
          
          if (Array.isArray(assignees) && assignees.length > 0) {
            assignee = assignees[0];
          }
        } catch (e) {
          console.error(`Error parsing _assign for task ${task.name}:`, e);
        }
      }
      
      // Debug
      console.log(`Task ${task.id || task.name}: startDate=${startDate}, endDate=${endDate}, assignee=${assignee}`);

      const processed = {
        ...task,
        id: task.id || task.name,
        title: task.title || task.subject || "Untitled Task",
        startDate,
        endDate,
        assignee: assignee || 'unassigned',  // Ensure assignee is never null/undefined
        duration: parseFloat(task.duration || task.expected_time || 0),
        durationDays,
        isScheduled: !!(startDate && endDate),
        project: task.project || "",
        status: task.status || "Open",
        priority: task.priority || "Medium",
        color: task.color || "#6B7280"
      };
      
      console.log(`Processed task ${processed.id}: isScheduled=${processed.isScheduled}`);
      return processed;
    });
  }

  // Calculate utilization for an assignee
  const calculateUtilization = (assigneeId) => {
    const assignee = assignees.value.find(a => a.id === assigneeId)
    if (!assignee || assignee.capacity === 0) return 0

    const assigneeTasks = tasks.value.filter(t => t.assignee === assigneeId && t.isScheduled)
    const scheduledHours = assigneeTasks.reduce((sum, t) => {
      // If task has duration, use it directly
      if (t.duration) return sum + t.duration
      
      // Otherwise calculate based on duration days
      if (t.durationDays) return sum + (t.durationDays * 8) // Assume 8 hours per day
      
      return sum
    }, 0)
    
    return Math.round((scheduledHours / assignee.capacity) * 100)
  }

  // Move task to different assignee or schedule
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
        onSuccess: (data) => {
          // Update local task data
          const taskIndex = tasks.value.findIndex(t => t.id === taskId)
          if (taskIndex !== -1) {
            tasks.value[taskIndex] = {
              ...tasks.value[taskIndex],
              assignee: assigneeId,
              startDate: startDate ? new Date(startDate) : null,
              endDate: endDate ? new Date(endDate) : null,
              isScheduled: !!(startDate && endDate)
            }
          }
          
          // Update assignee utilizations
          assignees.value = processAssigneeData(assignees.value)
          
          saveToCache()
        },
        onError: (err) => {
          error.value = err
          console.error('Error moving task:', err)
        }
      })

      await resource.submit()
      return resource.data
    } finally {
      loading.value = false
    }
  }

  // Update task details
  const updateTask = async (taskId, updates) => {
    loading.value = true
    error.value = null

    try {
      // Format date fields if they exist in updates
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
        onSuccess: (data) => {
          const taskIndex = tasks.value.findIndex(t => t.id === taskId)
          if (taskIndex !== -1) {
            tasks.value[taskIndex] = {
              ...tasks.value[taskIndex],
              ...updates
            }
          }
          
          // Update assignee utilizations if task duration changed
          if (updates.duration !== undefined || updates.startDate !== undefined || updates.endDate !== undefined) {
            assignees.value = processAssigneeData(assignees.value)
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

  // Get capacity analysis
  const getCapacityAnalysis = async (startDate = null, endDate = null) => {
    loading.value = true
    error.value = null

    try {
      const resource = createResource({
        url: 'planner.api.get_capacity_analysis',
        params: {
          department: department.value,
          start_date: startDate,
          end_date: endDate
        },
        onSuccess: (data) => {
          capacityAnalysis.value = data
        },
        onError: (err) => {
          error.value = err
          console.error('Error getting capacity analysis:', err)
        }
      })

      await resource.submit()
      return resource.data
    } finally {
      loading.value = false
    }
  }

  // Filter functions
  const filterTasks = (filters) => {
    return tasks.value.filter(task => {
      let matches = true

      if (filters.status && filters.status.length > 0) {
        matches = matches && filters.status.includes(task.status)
      }

      if (filters.priority && filters.priority.length > 0) {
        matches = matches && filters.priority.includes(task.priority)
      }

      if (filters.assignee) {
        matches = matches && task.assignee === filters.assignee
      }

      if (filters.project) {
        matches = matches && task.project?.toLowerCase().includes(filters.project.toLowerCase())
      }

      if (filters.scheduled !== undefined) {
        matches = matches && task.isScheduled === filters.scheduled
      }

      if (filters.dateRange) {
        const { start, end } = filters.dateRange
        if (task.startDate && task.endDate) {
          matches = matches && (
            (task.startDate >= start && task.startDate <= end) ||
            (task.endDate >= start && task.endDate <= end) ||
            (task.startDate <= start && task.endDate >= end)
          )
        }
      }

      return matches
    })
  }

  const filterAssignees = (filters) => {
    return assignees.value.filter(assignee => {
      let matches = true

      if (filters.department) {
        matches = matches && assignee.department === filters.department
      }

      if (filters.role) {
        matches = matches && assignee.role?.toLowerCase().includes(filters.role.toLowerCase())
      }

      if (filters.utilizationRange) {
        const utilization = calculateUtilization(assignee.id)
        matches = matches && (
          utilization >= filters.utilizationRange.min &&
          utilization <= filters.utilizationRange.max
        )
      }

      return matches
    })
  }

  // Cache management
  const saveToCache = () => {
    const cacheData = {
      assignees: assignees.value,
      tasks: tasks.value,
      timestamp: new Date().getTime()
    }
    localStorage.setItem(CACHE_KEY.value, JSON.stringify(cacheData))
  }

  const loadFromCache = () => {
    const cached = localStorage.getItem(CACHE_KEY.value)
    if (!cached) return null

    const { assignees: cachedAssignees, tasks: cachedTasks, timestamp } = JSON.parse(cached)
    const now = new Date().getTime()

    if (now - timestamp > CACHE_DURATION) {
      localStorage.removeItem(CACHE_KEY.value)
      return null
    }

    return { 
      assignees: cachedAssignees, 
      tasks: cachedTasks, 
      timestamp 
    }
  }

  const clearCache = () => {
    localStorage.removeItem(CACHE_KEY.value)
  }

  // Utility functions
  const getTasksForAssignee = (assigneeId, filters = {}) => {
    const assigneeTasks = tasks.value.filter(t => t.assignee === assigneeId)
    return filters ? filterTasks({ ...filters, assignee: assigneeId }) : assigneeTasks
  }

  const getUnscheduledTasksForAssignee = (assigneeId) => {
    return tasks.value.filter(t => t.assignee === assigneeId && !t.isScheduled)
  }

  const getScheduledTasksForAssignee = (assigneeId) => {
    return tasks.value.filter(t => t.assignee === assigneeId && t.isScheduled)
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

  // Auto-scheduling suggestions
  const getSuggestedScheduling = (taskId) => {
    const task = tasks.value.find(t => t.id === taskId)
    if (!task || !task.duration) return []

    const suggestions = []
    
    // Find assignees with available capacity
    const availableAssignees = assignees.value.filter(assignee => {
      const utilization = calculateUtilization(assignee.id)
      return utilization < 100 // Has available capacity
    })

    availableAssignees.forEach(assignee => {
      const availableHours = assignee.capacity - getScheduledTasksForAssignee(assignee.id)
        .reduce((sum, t) => sum + (t.duration || 0), 0)
      
      if (availableHours >= task.duration) {
        suggestions.push({
          assigneeId: assignee.id,
          assigneeName: assignee.name,
          availableHours,
          utilization: calculateUtilization(assignee.id),
          suggestedStartDate: new Date(), // Could be more sophisticated
          confidence: Math.max(0, 100 - calculateUtilization(assignee.id))
        })
      }
    })

    // Sort by confidence/availability
    return suggestions.sort((a, b) => b.confidence - a.confidence)
  }

  // Initialize data loading with force refresh to ensure fresh data
  nextTick(() => {
    console.log("Initial data loading for department:", department.value)
    loadWorkloadData(null, null, true)
  })

  return {
    // State
    department,
    assignees,
    tasks,
    loading,
    error,
    lastUpdate,
    capacityAnalysis,
    
    // Computed
    workloadStats,
    overallocatedAssignees,
    underutilizedAssignees,
    
    // Methods
    loadWorkloadData,
    moveTask,
    updateTask,
    getCapacityAnalysis,
    filterTasks,
    filterAssignees,
    clearCache,
    
    // Utility methods
    getTasksForAssignee,
    getUnscheduledTasksForAssignee,
    getScheduledTasksForAssignee,
    getTasksInDateRange,
    getSuggestedScheduling,
    calculateUtilization,
    formatDateForAPI
  }
}
