import { ref, onMounted, onUnmounted, watch } from 'vue'
import { io } from 'socket.io-client'
import { useWorkloadStore } from '../stores/workloadStore'
import { call } from 'frappe-ui'

export function useRealtimeV2() {
  const workloadStore = useWorkloadStore()
  
  // State
  const socket = ref(null)
  const connected = ref(false)
  const reconnecting = ref(false)
  const connectionError = ref(null)
  const currentRoom = ref(null)
  const activeUsers = ref([])
  const userActivity = ref({})
  
  // Connection management
  const connect = () => {
    if (socket.value?.connected) return
    
    try {
      // Initialize socket connection
      socket.value = io(window.location.origin, {
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        timeout: 20000,
        forceNew: false,
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        maxReconnectionAttempts: 5
      })
      
      setupEventListeners()
      
    } catch (error) {
      console.error('Failed to initialize socket connection:', error)
      connectionError.value = error.message
    }
  }
  
  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
    }
    connected.value = false
    workloadStore.setRealtimeConnection(false)
  }
  
  const setupEventListeners = () => {
    if (!socket.value) return
    
    // Connection events
    socket.value.on('connect', () => {
      console.log('Socket connected')
      connected.value = true
      reconnecting.value = false
      connectionError.value = null
      workloadStore.setRealtimeConnection(true)
      
      // Rejoin room if we were in one
      if (currentRoom.value) {
        joinRoom(currentRoom.value)
      }
    })
    
    socket.value.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason)
      connected.value = false
      workloadStore.setRealtimeConnection(false)
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, reconnect manually
        setTimeout(() => connect(), 1000)
      }
    })
    
    socket.value.on('connect_error', (error) => {
      console.error('Socket connection error:', error)
      connectionError.value = error.message
      reconnecting.value = false
    })
    
    socket.value.on('reconnect', (attemptNumber) => {
      console.log('Socket reconnected after', attemptNumber, 'attempts')
      reconnecting.value = false
    })
    
    socket.value.on('reconnect_attempt', (attemptNumber) => {
      console.log('Socket reconnection attempt:', attemptNumber)
      reconnecting.value = true
    })
    
    socket.value.on('reconnect_error', (error) => {
      console.error('Socket reconnection error:', error)
      connectionError.value = error.message
    })
    
    socket.value.on('reconnect_failed', () => {
      console.error('Socket reconnection failed')
      reconnecting.value = false
      connectionError.value = 'Failed to reconnect to server'
    })
    
    // Workload-specific events
    setupWorkloadEventListeners()
  }
  
  const setupWorkloadEventListeners = () => {
    if (!socket.value) return
    
    // Task events
    socket.value.on('task_update', (data) => {
      console.log('Task update received:', data)
      workloadStore.handleRealtimeUpdate('task_update', data)
      showNotification('Task Updated', `${data.title} has been updated`, 'info')
    })
    
    socket.value.on('task_moved', (data) => {
      console.log('Task moved:', data)
      workloadStore.handleRealtimeUpdate('task_moved', data)
      showNotification('Task Moved', `${data.title} has been moved`, 'info')
    })
    
    socket.value.on('batch_task_update', (data) => {
      console.log('Batch task update:', data)
      workloadStore.handleRealtimeUpdate('batch_task_update', data)
      showNotification('Tasks Updated', `${data.count} tasks have been updated`, 'info')
    })
    
    socket.value.on('task_created', (data) => {
      console.log('Task created:', data)
      workloadStore.handleRealtimeUpdate('task_created', data)
      showNotification('New Task', `${data.task.title} has been created`, 'success')
    })
    
    socket.value.on('task_deleted', (data) => {
      console.log('Task deleted:', data)
      workloadStore.handleRealtimeUpdate('task_deleted', data)
      showNotification('Task Deleted', 'A task has been deleted', 'warning')
    })
    
    // Capacity events
    socket.value.on('capacity_change', (data) => {
      console.log('Capacity change:', data)
      workloadStore.handleRealtimeUpdate('capacity_change', data)
      
      if (data.utilization_impact?.is_overallocated) {
        showNotification(
          'Overallocation Alert', 
          `${data.assignee_id} is now overallocated`, 
          'warning'
        )
      }
    })
    
    // Alert events
    socket.value.on('workload_alert', (data) => {
      console.log('Workload alert:', data)
      workloadStore.handleRealtimeUpdate('workload_alert', data)
      
      const severity = data.severity || 'medium'
      const notificationType = severity === 'high' || severity === 'critical' ? 'error' : 'warning'
      
      showNotification(
        'Workload Alert', 
        data.data.message || 'Workload issue detected', 
        notificationType
      )
    })
    
    // AI recommendation events
    socket.value.on('ai_recommendation', (data) => {
      console.log('AI recommendation:', data)
      workloadStore.handleRealtimeUpdate('ai_recommendation', data)
      showNotification(
        'AI Recommendation', 
        data.recommendation.message || 'New recommendation available', 
        'info'
      )
    })
    
    // User activity events
    socket.value.on('user_activity', (data) => {
      handleUserActivity(data)
    })
    
    socket.value.on('user_joined', (data) => {
      console.log('User joined room:', data)
      updateActiveUsers()
    })
    
    socket.value.on('user_left', (data) => {
      console.log('User left room:', data)
      updateActiveUsers()
    })
    
    // Room events
    socket.value.on('room_joined', (data) => {
      console.log('Joined room:', data)
      currentRoom.value = data.room
      updateActiveUsers()
    })
    
    socket.value.on('room_left', (data) => {
      console.log('Left room:', data)
      if (currentRoom.value === data.room) {
        currentRoom.value = null
      }
    })
    
    // Conflict resolution events
    socket.value.on('task_conflict', (data) => {
      console.log('Task conflict detected:', data)
      handleTaskConflict(data)
    })
  }
  
  // Room management
  const joinRoom = async (room) => {
    if (!socket.value?.connected) {
      console.warn('Cannot join room: socket not connected')
      return false
    }
    
    try {
      const response = await call('planner.realtime_v2.join_workload_room', { room })
      
      if (response.success) {
        currentRoom.value = room
        activeUsers.value = response.active_users || []
        workloadStore.updateActiveUsers(activeUsers.value)
        return true
      }
      
      return false
      
    } catch (error) {
      console.error('Failed to join room:', error)
      return false
    }
  }
  
  const leaveRoom = async (room) => {
    if (!socket.value?.connected) return false
    
    try {
      const response = await call('planner.realtime_v2.leave_workload_room', { room })
      
      if (response.success && currentRoom.value === room) {
        currentRoom.value = null
        activeUsers.value = []
        workloadStore.updateActiveUsers([])
      }
      
      return response.success
      
    } catch (error) {
      console.error('Failed to leave room:', error)
      return false
    }
  }
  
  // User activity
  const broadcastActivity = async (activityType, activityData = {}) => {
    if (!socket.value?.connected) return
    
    try {
      await call('planner.realtime_v2.broadcast_user_activity', {
        activity_type: activityType,
        activity_data: activityData
      })
    } catch (error) {
      console.error('Failed to broadcast activity:', error)
    }
  }
  
  const handleUserActivity = (data) => {
    const { user_id, activity_type, activity_data, timestamp } = data
    
    // Update user activity state
    userActivity.value[user_id] = {
      type: activity_type,
      data: activity_data,
      timestamp: new Date(timestamp),
      expires: new Date(Date.now() + 30000) // 30 seconds
    }
    
    // Clean up expired activities
    cleanupExpiredActivities()
  }
  
  const cleanupExpiredActivities = () => {
    const now = new Date()
    
    Object.keys(userActivity.value).forEach(userId => {
      if (userActivity.value[userId].expires < now) {
        delete userActivity.value[userId]
      }
    })
  }
  
  // Conflict resolution
  const handleTaskConflict = (data) => {
    const { conflict, task } = data
    
    // Show conflict resolution dialog
    showConflictDialog({
      title: 'Task Conflict Detected',
      message: `Multiple users are editing "${task.title}" simultaneously.`,
      conflicts: conflict,
      onResolve: (resolution) => {
        resolveTaskConflict(task.id, resolution)
      }
    })
  }
  
  const resolveTaskConflict = async (taskId, resolution) => {
    try {
      await call('planner.api_v2.resolve_task_conflict', {
        task_id: taskId,
        resolution: resolution
      })
      
      // Refresh workload data to get latest state
      await workloadStore.loadWorkloadData(true)
      
    } catch (error) {
      console.error('Failed to resolve task conflict:', error)
      showNotification('Conflict Resolution Failed', error.message, 'error')
    }
  }
  
  // Utility functions
  const updateActiveUsers = async () => {
    if (!currentRoom.value) return
    
    try {
      const users = await call('planner.realtime_v2.get_active_users_in_room', {
        room: currentRoom.value
      })
      
      activeUsers.value = users
      workloadStore.updateActiveUsers(users)
      
    } catch (error) {
      console.error('Failed to update active users:', error)
    }
  }
  
  const showNotification = (title, message, type = 'info') => {
    // Emit custom event for notification system
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('workload-notification', {
        detail: { title, message, type }
      }))
    }
  }
  
  const showConflictDialog = (conflictData) => {
    // Emit custom event for conflict dialog
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('workload-conflict', {
        detail: conflictData
      }))
    }
  }
  
  // Auto-reconnection with exponential backoff
  const reconnectWithBackoff = () => {
    let attempts = 0
    const maxAttempts = 5
    const baseDelay = 1000
    
    const attemptReconnect = () => {
      if (attempts >= maxAttempts) {
        console.error('Max reconnection attempts reached')
        connectionError.value = 'Unable to reconnect to server'
        return
      }
      
      attempts++
      const delay = baseDelay * Math.pow(2, attempts - 1)
      
      console.log(`Reconnection attempt ${attempts} in ${delay}ms`)
      
      setTimeout(() => {
        if (!connected.value) {
          connect()
          
          // Check if connection succeeded after a short delay
          setTimeout(() => {
            if (!connected.value) {
              attemptReconnect()
            } else {
              attempts = 0 // Reset on successful connection
            }
          }, 2000)
        }
      }, delay)
    }
    
    attemptReconnect()
  }
  
  // Lifecycle
  onMounted(() => {
    connect()
    
    // Set up periodic cleanup
    const cleanupInterval = setInterval(cleanupExpiredActivities, 30000)
    
    onUnmounted(() => {
      clearInterval(cleanupInterval)
      disconnect()
    })
  })
  
  // Watch for connection changes
  watch(connected, (newValue) => {
    if (!newValue && !reconnecting.value) {
      // Connection lost, attempt to reconnect
      setTimeout(() => {
        if (!connected.value) {
          reconnectWithBackoff()
        }
      }, 1000)
    }
  })
  
  return {
    // State
    connected,
    reconnecting,
    connectionError,
    currentRoom,
    activeUsers,
    userActivity,
    
    // Methods
    connect,
    disconnect,
    joinRoom,
    leaveRoom,
    broadcastActivity,
    updateActiveUsers,
    
    // Utilities
    isUserActive: (userId) => {
      const activity = userActivity.value[userId]
      return activity && activity.expires > new Date()
    },
    
    getUserActivity: (userId) => {
      return userActivity.value[userId] || null
    },
    
    getConnectionStatus: () => ({
      connected: connected.value,
      reconnecting: reconnecting.value,
      error: connectionError.value,
      room: currentRoom.value
    })
  }
}
