import { ref, reactive } from 'vue'

export function useDragAndDrop() {
  // Drag state
  const dragState = reactive({
    active: false,
    type: null, // 'task', 'resize', 'selection'
    taskId: null,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
    originalPosition: null,
    targetAssignee: null,
    targetDate: null,
    preview: null
  })
  
  // Drop zones
  const dropZones = ref([])
  
  // Setup drag and drop functionality
  const setupDragAndDrop = (container) => {
    if (!container) return
    
    // Mouse events
    container.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    
    // Touch events for mobile
    container.addEventListener('touchstart', handleTouchStart, { passive: false })
    document.addEventListener('touchmove', handleTouchMove, { passive: false })
    document.addEventListener('touchend', handleTouchEnd)
    
    // Prevent default drag behavior on images and other elements
    container.addEventListener('dragstart', (e) => e.preventDefault())
  }
  
  const handleMouseDown = (event) => {
    const taskElement = event.target.closest('[data-task-id]')
    if (!taskElement) return
    
    const taskId = taskElement.dataset.taskId
    const resizeHandle = event.target.closest('.resize-handle')
    
    if (resizeHandle) {
      startResize(event, taskId, resizeHandle.dataset.direction)
    } else {
      startDrag(event, taskId, taskElement)
    }
  }
  
  const handleTouchStart = (event) => {
    if (event.touches.length !== 1) return
    
    const touch = event.touches[0]
    const mouseEvent = new MouseEvent('mousedown', {
      clientX: touch.clientX,
      clientY: touch.clientY,
      bubbles: true
    })
    
    handleMouseDown(mouseEvent)
  }
  
  const startDrag = (event, taskId, element) => {
    event.preventDefault()
    
    const rect = element.getBoundingClientRect()
    
    dragState.active = true
    dragState.type = 'task'
    dragState.taskId = taskId
    dragState.startX = event.clientX
    dragState.startY = event.clientY
    dragState.currentX = event.clientX
    dragState.currentY = event.clientY
    dragState.originalPosition = {
      x: rect.left,
      y: rect.top,
      width: rect.width,
      height: rect.height
    }
    
    // Create drag preview
    createDragPreview(element)
    
    // Add dragging class
    element.classList.add('dragging')
    document.body.classList.add('dragging-active')
  }
  
  const startResize = (event, taskId, direction) => {
    event.preventDefault()
    event.stopPropagation()
    
    dragState.active = true
    dragState.type = 'resize'
    dragState.taskId = taskId
    dragState.startX = event.clientX
    dragState.startY = event.clientY
    dragState.currentX = event.clientX
    dragState.currentY = event.clientY
    dragState.resizeDirection = direction
    
    document.body.classList.add('resizing-active')
  }
  
  const handleMouseMove = (event) => {
    if (!dragState.active) return
    
    event.preventDefault()
    
    dragState.currentX = event.clientX
    dragState.currentY = event.clientY
    
    if (dragState.type === 'task') {
      updateDragPreview()
      updateDropTarget(event)
    } else if (dragState.type === 'resize') {
      updateResizePreview()
    }
  }
  
  const handleTouchMove = (event) => {
    if (!dragState.active || event.touches.length !== 1) return
    
    event.preventDefault()
    
    const touch = event.touches[0]
    const mouseEvent = new MouseEvent('mousemove', {
      clientX: touch.clientX,
      clientY: touch.clientY,
      bubbles: true
    })
    
    handleMouseMove(mouseEvent)
  }
  
  const handleMouseUp = (event) => {
    if (!dragState.active) return
    
    if (dragState.type === 'task') {
      completeDrag(event)
    } else if (dragState.type === 'resize') {
      completeResize(event)
    }
    
    resetDragState()
  }
  
  const handleTouchEnd = (event) => {
    if (!dragState.active) return
    
    const touch = event.changedTouches[0]
    const mouseEvent = new MouseEvent('mouseup', {
      clientX: touch.clientX,
      clientY: touch.clientY,
      bubbles: true
    })
    
    handleMouseUp(mouseEvent)
  }
  
  const createDragPreview = (element) => {
    const preview = element.cloneNode(true)
    preview.classList.add('drag-preview')
    preview.style.position = 'fixed'
    preview.style.pointerEvents = 'none'
    preview.style.zIndex = '9999'
    preview.style.opacity = '0.8'
    preview.style.transform = 'rotate(5deg)'
    preview.style.left = `${dragState.originalPosition.x}px`
    preview.style.top = `${dragState.originalPosition.y}px`
    preview.style.width = `${dragState.originalPosition.width}px`
    preview.style.height = `${dragState.originalPosition.height}px`
    
    document.body.appendChild(preview)
    dragState.preview = preview
  }
  
  const updateDragPreview = () => {
    if (!dragState.preview) return
    
    const deltaX = dragState.currentX - dragState.startX
    const deltaY = dragState.currentY - dragState.startY
    
    dragState.preview.style.left = `${dragState.originalPosition.x + deltaX}px`
    dragState.preview.style.top = `${dragState.originalPosition.y + deltaY}px`
  }
  
  const updateDropTarget = (event) => {
    // Find drop target under cursor
    const elementsUnderCursor = document.elementsFromPoint(event.clientX, event.clientY)
    
    // Clear previous drop targets
    document.querySelectorAll('.drop-target').forEach(el => {
      el.classList.remove('drop-target', 'drop-target-valid', 'drop-target-invalid')
    })
    
    // Find assignee row or time slot
    const assigneeRow = elementsUnderCursor.find(el => el.dataset.assigneeId)
    const timeSlot = elementsUnderCursor.find(el => el.dataset.date)
    
    if (assigneeRow && timeSlot) {
      const assigneeId = assigneeRow.dataset.assigneeId
      const date = timeSlot.dataset.date
      
      dragState.targetAssignee = assigneeId
      dragState.targetDate = date
      
      // Validate drop target
      const isValid = validateDropTarget(assigneeId, date)
      
      assigneeRow.classList.add('drop-target', isValid ? 'drop-target-valid' : 'drop-target-invalid')
      
      if (timeSlot !== assigneeRow) {
        timeSlot.classList.add('drop-target', isValid ? 'drop-target-valid' : 'drop-target-invalid')
      }
    }
  }
  
  const validateDropTarget = (assigneeId, date) => {
    // Add validation logic here
    // Check for conflicts, capacity, etc.
    return true // Placeholder
  }
  
  const updateResizePreview = () => {
    const taskElement = document.querySelector(`[data-task-id="${dragState.taskId}"]`)
    if (!taskElement) return
    
    const deltaX = dragState.currentX - dragState.startX
    const rect = taskElement.getBoundingClientRect()
    
    if (dragState.resizeDirection === 'left') {
      const newWidth = rect.width - deltaX
      if (newWidth > 50) { // Minimum width
        taskElement.style.width = `${newWidth}px`
        taskElement.style.left = `${rect.left + deltaX}px`
      }
    } else if (dragState.resizeDirection === 'right') {
      const newWidth = rect.width + deltaX
      if (newWidth > 50) {
        taskElement.style.width = `${newWidth}px`
      }
    }
  }
  
  const completeDrag = (event) => {
    if (dragState.targetAssignee && dragState.targetDate) {
      // Emit drag complete event
      const dragCompleteEvent = new CustomEvent('task-drag-complete', {
        detail: {
          taskId: dragState.taskId,
          targetAssignee: dragState.targetAssignee,
          targetDate: dragState.targetDate,
          originalEvent: event
        }
      })
      
      document.dispatchEvent(dragCompleteEvent)
    }
  }
  
  const completeResize = (event) => {
    const taskElement = document.querySelector(`[data-task-id="${dragState.taskId}"]`)
    if (!taskElement) return
    
    const rect = taskElement.getBoundingClientRect()
    
    // Calculate new dates based on resize
    const newDates = calculateNewDatesFromResize(rect, dragState.resizeDirection)
    
    if (newDates) {
      // Emit resize complete event
      const resizeCompleteEvent = new CustomEvent('task-resize-complete', {
        detail: {
          taskId: dragState.taskId,
          newStartDate: newDates.startDate,
          newEndDate: newDates.endDate,
          originalEvent: event
        }
      })
      
      document.dispatchEvent(resizeCompleteEvent)
    }
  }
  
  const calculateNewDatesFromResize = (rect, direction) => {
    // This would need to be implemented based on your timeline grid
    // Calculate new dates based on the resized element position
    return null // Placeholder
  }
  
  const resetDragState = () => {
    // Clean up drag preview
    if (dragState.preview) {
      dragState.preview.remove()
      dragState.preview = null
    }
    
    // Remove drag classes
    document.querySelectorAll('.dragging').forEach(el => {
      el.classList.remove('dragging')
    })
    
    document.querySelectorAll('.drop-target').forEach(el => {
      el.classList.remove('drop-target', 'drop-target-valid', 'drop-target-invalid')
    })
    
    document.body.classList.remove('dragging-active', 'resizing-active')
    
    // Reset drag state
    Object.assign(dragState, {
      active: false,
      type: null,
      taskId: null,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
      originalPosition: null,
      targetAssignee: null,
      targetDate: null,
      resizeDirection: null
    })
  }
  
  // Utility functions
  const registerDropZone = (element, config) => {
    dropZones.value.push({
      element,
      config,
      id: config.id || Math.random().toString(36).substr(2, 9)
    })
  }
  
  const unregisterDropZone = (id) => {
    const index = dropZones.value.findIndex(zone => zone.id === id)
    if (index >= 0) {
      dropZones.value.splice(index, 1)
    }
  }
  
  const isDragging = () => dragState.active
  
  const getDraggedTask = () => dragState.taskId
  
  // Cleanup function
  const cleanup = () => {
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    document.removeEventListener('touchmove', handleTouchMove)
    document.removeEventListener('touchend', handleTouchEnd)
    
    resetDragState()
  }
  
  return {
    dragState,
    dropZones,
    setupDragAndDrop,
    registerDropZone,
    unregisterDropZone,
    isDragging,
    getDraggedTask,
    cleanup
  }
}
