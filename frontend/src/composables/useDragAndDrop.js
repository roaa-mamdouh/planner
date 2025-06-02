import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { useErrorHandler } from '@/services/errorHandler'

export function useDragAndDrop() {
  const { handleApiError } = useErrorHandler()
  const isDragging = ref(false)
  const draggedTask = ref(null)
  const dropTarget = ref(null)

  // Resource for updating task position
  const moveTaskResource = createResource({
    url: 'planner.api.move_task',
    onError: (error) => {
      handleApiError(error)
    }
  })

  // Start dragging
  const onDragStart = (task, event) => {
    isDragging.value = true
    draggedTask.value = task
    
    // Add dragging class for visual feedback
    if (event.item) {
      event.item.classList.add('dragging')
    }
  }

  // End dragging
  const onDragEnd = (event) => {
    isDragging.value = false
    draggedTask.value = null
    dropTarget.value = null

    // Remove dragging class
    if (event.item) {
      event.item.classList.remove('dragging')
    }
  }

  // Handle dropping task
  const onDrop = async (target) => {
    if (!draggedTask.value || !target) return

    try {
      const updates = {
        task_id: draggedTask.value.id,
        assignee_id: target.assigneeId,
        start_date: target.date,
        end_date: target.date // Will be adjusted based on task duration
      }

      // If dropping in timeline, calculate end date based on task duration
      if (target.date && draggedTask.value.duration) {
        const startDate = new Date(target.date)
        const endDate = new Date(startDate)
        endDate.setHours(endDate.getHours() + draggedTask.value.duration)
        updates.end_date = endDate.toISOString().split('T')[0]
      }

      await moveTaskResource.submit(updates)

    } catch (error) {
      console.error('Error moving task:', error)
    }
  }

  // Handle dragging over a drop zone
  const onDragOver = (target, event) => {
    event.preventDefault()
    dropTarget.value = target

    // Add visual feedback for valid drop targets
    const dropZone = event.currentTarget
    if (dropZone) {
      dropZone.classList.add('drop-target')
    }
  }

  // Handle dragging out of a drop zone
  const onDragLeave = (event) => {
    const dropZone = event.currentTarget
    if (dropZone) {
      dropZone.classList.remove('drop-target')
    }
  }

  // Computed properties for drag state
  const isDraggingTask = computed(() => isDragging.value && draggedTask.value !== null)
  const currentDropTarget = computed(() => dropTarget.value)

  // Drag options for Vue.Draggable
  const dragOptions = {
    animation: 150,
    ghostClass: 'ghost',
    dragClass: 'dragging',
    group: 'tasks',
    handle: '.draggable-handle'
  }

  return {
    // State
    isDragging,
    draggedTask,
    dropTarget,
    isDraggingTask,
    currentDropTarget,

    // Methods
    onDragStart,
    onDragEnd,
    onDrop,
    onDragOver,
    onDragLeave,

    // Configuration
    dragOptions,

    // Resources
    moveTaskResource
  }
}
