<template>
  <div class="timeline-v2 h-full flex flex-col bg-white dark:bg-gray-900">
    <!-- Header with controls and metrics -->
    <TimelineHeader
      :loading="loading"
      :metrics="capacityMetrics"
      :filters="filters"
      :view-settings="viewSettings"
      :active-users="activeUsers"
      :realtime-connected="realtimeConnected"
      @update-filters="updateFilters"
      @update-view-settings="updateViewSettings"
      @refresh="refreshData"
      @export="exportData"
    />
    
    <!-- Alerts and notifications -->
    <AlertPanel
      v-if="hasAlerts"
      :alerts="alerts"
      :recommendations="recommendations"
      @dismiss-alert="dismissAlert"
      @dismiss-recommendation="dismissRecommendation"
      @apply-recommendation="applyRecommendation"
    />
    
    <!-- Main timeline content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Assignee sidebar -->
      <AssigneeSidebar
        :assignees="filteredAssignees"
        :selected-assignee="selectedAssignee"
        :show-metrics="viewSettings.showMetrics"
        @select-assignee="selectAssignee"
        @assignee-action="handleAssigneeAction"
      />
      
      <!-- Timeline grid -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Time scale header -->
        <TimeScale
          :start-date="timelineRange.start"
          :end-date="timelineRange.end"
          :view-mode="viewSettings.timelineView"
          :zoom-level="viewSettings.zoomLevel"
          @date-click="handleDateClick"
        />
        
        <!-- Scrollable timeline content -->
        <div 
          ref="timelineContainer"
          class="flex-1 overflow-auto relative"
          @scroll="handleScroll"
        >
          <!-- Timeline grid background -->
          <TimelineGrid
            :start-date="timelineRange.start"
            :end-date="timelineRange.end"
            :view-mode="viewSettings.timelineView"
            :zoom-level="viewSettings.zoomLevel"
            :assignees="filteredAssignees"
          />
          
          <!-- Task blocks -->
          <div class="absolute inset-0 pointer-events-none">
            <TaskBlock
              v-for="task in visibleTasks"
              :key="task.id"
              :task="task"
              :assignee="getAssigneeById(task.assignee)"
              :timeline-range="timelineRange"
              :view-mode="viewSettings.timelineView"
              :zoom-level="viewSettings.zoomLevel"
              :selected="selectedTasks.includes(task.id)"
              :conflicted="conflictedTasks.includes(task.id)"
              :user-activity="getUserActivity(task.id)"
              class="pointer-events-auto"
              @select="selectTask"
              @move="moveTask"
              @resize="resizeTask"
              @edit="editTask"
              @context-menu="showTaskContextMenu"
            />
          </div>
          
          <!-- Drag overlay -->
          <DragOverlay
            v-if="dragState.active"
            :drag-state="dragState"
            :timeline-range="timelineRange"
            :view-mode="viewSettings.timelineView"
            :zoom-level="viewSettings.zoomLevel"
          />
          
          <!-- Selection overlay -->
          <SelectionOverlay
            v-if="selectionState.active"
            :selection-state="selectionState"
            @selection-complete="handleSelectionComplete"
          />
        </div>
      </div>
      
      <!-- Backlog panel -->
      <BacklogPanel
        v-if="viewSettings.showBacklog"
        :tasks="unscheduledTasks"
        :loading="loading"
        @task-drop="scheduleTask"
        @task-edit="editTask"
      />
    </div>
    
    <!-- Bottom status bar -->
    <StatusBar
      :selected-count="selectedTasks.length"
      :total-tasks="filteredTasks.length"
      :loading="loading"
      :last-updated="lastUpdated"
      :connection-status="connectionStatus"
      @bulk-action="handleBulkAction"
    />
    
    <!-- Modals and dialogs -->
    <TaskEditDialog
      v-if="editingTask"
      :task="editingTask"
      :assignees="filteredAssignees"
      @save="saveTask"
      @close="closeTaskDialog"
    />
    
    <ConflictResolutionDialog
      v-if="conflictDialog.show"
      :conflict="conflictDialog.data"
      @resolve="resolveConflict"
      @close="closeConflictDialog"
    />
    
    <BulkActionDialog
      v-if="bulkActionDialog.show"
      :action="bulkActionDialog.action"
      :tasks="selectedTaskObjects"
      :assignees="filteredAssignees"
      @execute="executeBulkAction"
      @close="closeBulkActionDialog"
    />
    
    <!-- Context menu -->
    <ContextMenu
      v-if="contextMenu.show"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :items="contextMenu.items"
      @select="handleContextMenuAction"
      @close="closeContextMenu"
    />
    
    <!-- Loading overlay -->
    <LoadingOverlay v-if="loading && !workloadData.tasks.length" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useWorkloadStore } from '../../stores/workloadStore'
import { useRealtimeV2 } from '../../composables/useRealtimeV2'
import { useDragAndDrop } from '../../composables/useDragAndDrop'
import { useKeyboardShortcuts } from '../../composables/useKeyboardShortcuts'
import { useVirtualization } from '../../composables/useVirtualization'

// Components
import TimelineHeader from './TimelineHeader.vue'
import AlertPanel from './AlertPanel.vue'
import AssigneeSidebar from './AssigneeSidebar.vue'
import TimeScale from './TimeScale.vue'
import TimelineGrid from './TimelineGrid.vue'
import TaskBlock from './TaskBlock.vue'
import BacklogPanel from './BacklogPanel.vue'
import StatusBar from './StatusBar.vue'
import DragOverlay from './DragOverlay.vue'
import SelectionOverlay from './SelectionOverlay.vue'
import TaskEditDialog from './TaskEditDialog.vue'
import ConflictResolutionDialog from './ConflictResolutionDialog.vue'
import BulkActionDialog from './BulkActionDialog.vue'
import ContextMenu from './ContextMenu.vue'
import LoadingOverlay from './LoadingOverlay.vue'

// Store and composables
const workloadStore = useWorkloadStore()
const realtime = useRealtimeV2()
const { setupDragAndDrop, dragState } = useDragAndDrop()
const { setupKeyboardShortcuts } = useKeyboardShortcuts()
const { visibleItems: visibleTasks, setupVirtualization } = useVirtualization()

// Refs
const timelineContainer = ref(null)

// Store state
const {
  workloadData,
  loading,
  error,
  lastUpdated,
  filters,
  viewSettings,
  filteredTasks,
  filteredAssignees,
  capacityMetrics,
  getTaskById,
  getAssigneeById,
  getUnscheduledTasks
} = workloadStore

// Realtime state
const {
  connected: realtimeConnected,
  activeUsers,
  userActivity,
  currentRoom,
  getConnectionStatus
} = realtime

// Local state
const selectedTasks = ref([])
const selectedAssignee = ref(null)
const conflictedTasks = ref([])
const editingTask = ref(null)
const selectionState = ref({ active: false, start: null, end: null })

// Dialog states
const conflictDialog = ref({ show: false, data: null })
const bulkActionDialog = ref({ show: false, action: null })
const contextMenu = ref({ show: false, x: 0, y: 0, items: [] })

// Computed properties
const timelineRange = computed(() => {
  const now = new Date()
  const start = filters.start_date ? new Date(filters.start_date) : new Date(now.getFullYear(), now.getMonth(), 1)
  const end = filters.end_date ? new Date(filters.end_date) : new Date(now.getFullYear(), now.getMonth() + 3, 0)
  
  return { start, end }
})

const unscheduledTasks = computed(() => {
  return getUnscheduledTasks()
})

const selectedTaskObjects = computed(() => {
  return selectedTasks.value.map(id => getTaskById(id)).filter(Boolean)
})

const hasAlerts = computed(() => {
  return alerts.value.length > 0 || recommendations.value.length > 0
})

const alerts = computed(() => {
  return workloadData.real_time_metrics?.alerts || []
})

const recommendations = computed(() => {
  return workloadData.ai_insights?.recommendations || []
})

const connectionStatus = computed(() => {
  return getConnectionStatus()
})

// Methods
const refreshData = async (forceRefresh = false) => {
  await workloadStore.loadWorkloadData(forceRefresh)
}

const updateFilters = (newFilters) => {
  workloadStore.updateFilters(newFilters)
  refreshData()
}

const updateViewSettings = (newSettings) => {
  workloadStore.updateViewSettings(newSettings)
}

const selectTask = (taskId, multiSelect = false) => {
  if (multiSelect) {
    const index = selectedTasks.value.indexOf(taskId)
    if (index >= 0) {
      selectedTasks.value.splice(index, 1)
    } else {
      selectedTasks.value.push(taskId)
    }
  } else {
    selectedTasks.value = [taskId]
  }
  
  // Broadcast activity
  realtime.broadcastActivity('task_selected', { taskId, multiSelect })
}

const selectAssignee = (assigneeId) => {
  selectedAssignee.value = assigneeId
  
  // Filter tasks for selected assignee
  if (assigneeId) {
    updateFilters({ assignee: assigneeId })
  }
}

const moveTask = async (taskId, newAssignee, startDate, endDate) => {
  try {
    await workloadStore.moveTask(taskId, newAssignee, startDate, endDate)
    
    // Remove from selection after successful move
    const index = selectedTasks.value.indexOf(taskId)
    if (index >= 0) {
      selectedTasks.value.splice(index, 1)
    }
    
  } catch (error) {
    console.error('Failed to move task:', error)
    // Show error notification
    showNotification('Move Failed', error.message, 'error')
  }
}

const resizeTask = async (taskId, newStartDate, newEndDate) => {
  try {
    const task = getTaskById(taskId)
    if (!task) return
    
    await workloadStore.moveTask(taskId, task.assignee, newStartDate, newEndDate)
    
  } catch (error) {
    console.error('Failed to resize task:', error)
    showNotification('Resize Failed', error.message, 'error')
  }
}

const editTask = (taskId) => {
  const task = getTaskById(taskId)
  if (task) {
    editingTask.value = { ...task }
  }
}

const saveTask = async (taskData) => {
  try {
    // Update task via API
    await workloadStore.bulkUpdateTasks([{
      task_id: taskData.id,
      changes: {
        subject: taskData.title,
        status: taskData.status,
        priority: taskData.priority,
        description: taskData.description
      },
      timeline_changes: {
        assignee: taskData.assignee,
        start_date: taskData.startDate,
        end_date: taskData.endDate,
        estimated_hours: taskData.duration,
        progress_percent: taskData.progress
      }
    }])
    
    editingTask.value = null
    showNotification('Task Updated', 'Task has been updated successfully', 'success')
    
  } catch (error) {
    console.error('Failed to save task:', error)
    showNotification('Save Failed', error.message, 'error')
  }
}

const closeTaskDialog = () => {
  editingTask.value = null
}

const scheduleTask = async (task, assigneeId, startDate, endDate) => {
  try {
    await moveTask(task.id, assigneeId, startDate, endDate)
    showNotification('Task Scheduled', `${task.title} has been scheduled`, 'success')
    
  } catch (error) {
    console.error('Failed to schedule task:', error)
    showNotification('Schedule Failed', error.message, 'error')
  }
}

const handleDateClick = (date) => {
  // Handle date click for creating new tasks or filtering
  console.log('Date clicked:', date)
}

const handleScroll = (event) => {
  // Handle timeline scroll for virtualization
  setupVirtualization(event.target, filteredTasks.value)
}

const handleSelectionComplete = (selection) => {
  // Handle area selection
  const tasksInSelection = filteredTasks.value.filter(task => {
    // Check if task intersects with selection area
    return isTaskInSelection(task, selection)
  })
  
  selectedTasks.value = tasksInSelection.map(t => t.id)
  selectionState.value.active = false
}

const isTaskInSelection = (task, selection) => {
  // Implementation for checking if task is within selection bounds
  // This would involve coordinate calculations based on task position
  return false // Placeholder
}

const showTaskContextMenu = (event, taskId) => {
  event.preventDefault()
  
  const task = getTaskById(taskId)
  if (!task) return
  
  contextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    items: [
      { label: 'Edit Task', action: 'edit', icon: 'edit' },
      { label: 'Duplicate', action: 'duplicate', icon: 'copy' },
      { label: 'Move to...', action: 'move', icon: 'move' },
      { type: 'separator' },
      { label: 'Mark Complete', action: 'complete', icon: 'check' },
      { label: 'Delete', action: 'delete', icon: 'trash', danger: true }
    ],
    taskId
  }
}

const handleContextMenuAction = (action, taskId) => {
  switch (action) {
    case 'edit':
      editTask(taskId)
      break
    case 'duplicate':
      duplicateTask(taskId)
      break
    case 'move':
      showMoveDialog(taskId)
      break
    case 'complete':
      markTaskComplete(taskId)
      break
    case 'delete':
      deleteTask(taskId)
      break
  }
  
  closeContextMenu()
}

const closeContextMenu = () => {
  contextMenu.value.show = false
}

const handleBulkAction = (action) => {
  if (selectedTasks.value.length === 0) return
  
  bulkActionDialog.value = {
    show: true,
    action
  }
}

const executeBulkAction = async (action, data) => {
  try {
    const updates = selectedTasks.value.map(taskId => ({
      task_id: taskId,
      changes: data.changes || {},
      timeline_changes: data.timeline_changes || {}
    }))
    
    await workloadStore.bulkUpdateTasks(updates)
    
    selectedTasks.value = []
    bulkActionDialog.value.show = false
    
    showNotification('Bulk Action Complete', `${updates.length} tasks updated`, 'success')
    
  } catch (error) {
    console.error('Bulk action failed:', error)
    showNotification('Bulk Action Failed', error.message, 'error')
  }
}

const closeBulkActionDialog = () => {
  bulkActionDialog.value.show = false
}

const handleAssigneeAction = (action, assigneeId) => {
  switch (action) {
    case 'view_capacity':
      showCapacityDialog(assigneeId)
      break
    case 'assign_task':
      showAssignTaskDialog(assigneeId)
      break
    case 'view_workload':
      selectAssignee(assigneeId)
      break
  }
}

const dismissAlert = (alertId) => {
  workloadStore.dismissAlert(alertId)
}

const dismissRecommendation = (recommendationId) => {
  workloadStore.dismissRecommendation(recommendationId)
}

const applyRecommendation = async (recommendation) => {
  try {
    // Apply AI recommendation
    console.log('Applying recommendation:', recommendation)
    
    // Implementation would depend on recommendation type
    switch (recommendation.type) {
      case 'redistribute_tasks':
        await redistributeTasks(recommendation.data)
        break
      case 'adjust_deadlines':
        await adjustDeadlines(recommendation.data)
        break
      case 'add_resources':
        showAddResourcesDialog(recommendation.data)
        break
    }
    
    dismissRecommendation(recommendation.id)
    showNotification('Recommendation Applied', 'Changes have been applied', 'success')
    
  } catch (error) {
    console.error('Failed to apply recommendation:', error)
    showNotification('Application Failed', error.message, 'error')
  }
}

const resolveConflict = async (resolution) => {
  try {
    // Handle conflict resolution
    await realtime.resolveTaskConflict(conflictDialog.value.data.task.id, resolution)
    conflictDialog.value.show = false
    
  } catch (error) {
    console.error('Failed to resolve conflict:', error)
    showNotification('Resolution Failed', error.message, 'error')
  }
}

const closeConflictDialog = () => {
  conflictDialog.value.show = false
}

const getUserActivity = (taskId) => {
  // Get user activity for a specific task
  return Object.values(userActivity).find(activity => 
    activity.data?.taskId === taskId
  )
}

const exportData = () => {
  // Export timeline data
  const data = {
    tasks: filteredTasks.value,
    assignees: filteredAssignees.value,
    metrics: capacityMetrics.value,
    filters: filters,
    exported_at: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workload-timeline-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const showNotification = (title, message, type) => {
  // Emit notification event
  window.dispatchEvent(new CustomEvent('workload-notification', {
    detail: { title, message, type }
  }))
}

// Lifecycle
onMounted(async () => {
  // Initialize timeline
  await refreshData()
  
  // Join realtime room
  const room = filters.department ? `workload_${filters.department}` : 'workload_global'
  await realtime.joinRoom(room)
  
  // Setup interactions
  setupDragAndDrop(timelineContainer.value)
  setupKeyboardShortcuts({
    onSelectAll: () => selectedTasks.value = filteredTasks.value.map(t => t.id),
    onDelete: () => selectedTasks.value.length > 0 && handleBulkAction('delete'),
    onEscape: () => {
      selectedTasks.value = []
      closeContextMenu()
      closeTaskDialog()
    }
  })
  
  // Setup virtualization
  nextTick(() => {
    if (timelineContainer.value) {
      setupVirtualization(timelineContainer.value, filteredTasks.value)
    }
  })
  
  // Listen for conflict events
  window.addEventListener('workload-conflict', (event) => {
    conflictDialog.value = {
      show: true,
      data: event.detail
    }
  })
})

onUnmounted(() => {
  // Leave realtime room
  if (currentRoom.value) {
    realtime.leaveRoom(currentRoom.value)
  }
  
  // Cleanup event listeners
  window.removeEventListener('workload-conflict', () => {})
})

// Watch for filter changes
watch(() => filters.department, async (newDept, oldDept) => {
  if (newDept !== oldDept) {
    // Switch realtime rooms
    if (oldDept) {
      await realtime.leaveRoom(`workload_${oldDept}`)
    }
    
    const room = newDept ? `workload_${newDept}` : 'workload_global'
    await realtime.joinRoom(room)
  }
})

// Watch for realtime updates
watch(() => workloadData.tasks, () => {
  // Update virtualization when tasks change
  if (timelineContainer.value) {
    setupVirtualization(timelineContainer.value, filteredTasks.value)
  }
}, { deep: true })
</script>

<style scoped>
.timeline-v2 {
  --timeline-header-height: 120px;
  --timeline-sidebar-width: 280px;
  --timeline-row-height: 60px;
  --timeline-scale-height: 40px;
}

.timeline-grid {
  background-image: 
    linear-gradient(to right, rgba(0,0,0,0.1) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0,0,0,0.1) 1px, transparent 1px);
  background-size: var(--timeline-column-width) var(--timeline-row-height);
}

.dark .timeline-grid {
  background-image: 
    linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px);
}

/* Scrollbar styling */
.timeline-v2 ::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.timeline-v2 ::-webkit-scrollbar-track {
  background: rgba(0,0,0,0.1);
}

.timeline-v2 ::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.3);
  border-radius: 4px;
}

.timeline-v2 ::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.5);
}

.dark .timeline-v2 ::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.1);
}

.dark .timeline-v2 ::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.3);
}

.dark .timeline-v2 ::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.5);
}
</style>
