<template>
  <div
    class="task-block group cursor-move rounded-lg shadow-sm hover:shadow-md transition-all duration-200 relative"
    :class="[
      getTaskBlockClass(task),
      {
        'scale-105 z-20': isDragging,
        'opacity-50': isBeingDragged,
        'ring-2 ring-blue-500 ring-offset-2': isSelected
      }
    ]"
    :style="blockStyle"
    draggable="true"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
    @click="handleClick"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- Task Content -->
    <div class="p-3 text-white relative z-10">
      <!-- Task Header -->
      <div class="flex items-start justify-between mb-2">
        <div class="flex-1 min-w-0">
          <h4 class="font-semibold text-sm truncate leading-tight">
            {{ task.title }}
          </h4>
          <p v-if="task.project" class="text-white/80 text-xs truncate mt-1">
            {{ task.project }}
          </p>
        </div>
        
        <!-- Priority Indicator -->
        <div 
          class="w-2 h-2 rounded-full ml-2 flex-shrink-0"
          :class="getPriorityIndicatorClass(task.priority)"
          :title="`${task.priority} Priority`"
        ></div>
      </div>

      <!-- Task Details -->
      <div class="flex items-center justify-between text-xs">
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <FeatherIcon name="clock" class="w-3 h-3" />
            <span class="text-white/90">{{ task.duration }}h</span>
          </div>
          
          <div v-if="task.status" class="flex items-center gap-1">
            <div 
              class="w-2 h-2 rounded-full"
              :class="getStatusIndicatorClass(task.status)"
            ></div>
            <span class="text-white/80 text-xs">{{ task.status }}</span>
          </div>
        </div>

        <!-- Progress Indicator -->
        <div v-if="showProgress" class="text-white/70 text-xs">
          {{ getProgressText() }}
        </div>
      </div>

      <!-- Progress Bar -->
      <div v-if="showProgress && task.progress !== undefined" class="mt-2">
        <div class="w-full bg-white/20 rounded-full h-1">
          <div 
            class="bg-white/60 h-1 rounded-full transition-all duration-300"
            :style="{ width: `${task.progress || 0}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Resize Handles -->
    <div 
      v-if="resizable && isHovered"
      class="resize-handle-left absolute left-0 top-0 w-2 h-full cursor-ew-resize opacity-0 group-hover:opacity-100 bg-white/30 transition-opacity duration-200 rounded-l-lg"
      @mousedown.stop="startResize($event, 'left')"
    ></div>
    <div 
      v-if="resizable && isHovered"
      class="resize-handle-right absolute right-0 top-0 w-2 h-full cursor-ew-resize opacity-0 group-hover:opacity-100 bg-white/30 transition-opacity duration-200 rounded-r-lg"
      @mousedown.stop="startResize($event, 'right')"
    ></div>

    <!-- Drag Handle -->
    <div 
      v-if="isHovered"
      class="drag-handle absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
    >
      <FeatherIcon name="move" class="w-3 h-3 text-white/60" />
    </div>

    <!-- Task Tooltip -->
    <div 
      v-if="showTooltip && isHovered"
      class="task-tooltip absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-30"
    >
      <div class="bg-gray-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-xs">
        <div class="font-semibold mb-1">{{ task.title }}</div>
        <div v-if="task.description" class="text-gray-300 mb-2 line-clamp-3">
          {{ task.description }}
        </div>
        <div class="space-y-1 text-gray-400">
          <div v-if="task.project">Project: {{ task.project }}</div>
          <div>Duration: {{ task.duration }}h</div>
          <div>Priority: {{ task.priority }}</div>
          <div v-if="task.assignee">Assigned to: {{ getAssigneeName(task.assignee) }}</div>
          <div v-if="task.startDate && task.endDate">
            {{ formatDateRange(task.startDate, task.endDate) }}
          </div>
        </div>
        <!-- Tooltip Arrow -->
        <div class="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  assignees: {
    type: Array,
    default: () => []
  },
  resizable: {
    type: Boolean,
    default: true
  },
  showProgress: {
    type: Boolean,
    default: false
  },
  showTooltip: {
    type: Boolean,
    default: true
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  style: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['click', 'dragStart', 'dragEnd', 'resize', 'hover'])

// State
const isDragging = ref(false)
const isBeingDragged = ref(false)
const isHovered = ref(false)

// Computed
const blockStyle = computed(() => ({
  ...props.style
}))

// Methods
const handleDragStart = (event) => {
  isDragging.value = true
  isBeingDragged.value = true
  
  event.dataTransfer.setData('application/json', JSON.stringify(props.task))
  event.dataTransfer.effectAllowed = 'move'
  
  emit('dragStart', event, props.task)
}

const handleDragEnd = (event) => {
  isDragging.value = false
  isBeingDragged.value = false
  
  emit('dragEnd', event, props.task)
}

const handleClick = (event) => {
  if (!isDragging.value) {
    emit('click', props.task.id, event)
  }
}

const handleMouseEnter = () => {
  isHovered.value = true
  emit('hover', props.task, true)
}

const handleMouseLeave = () => {
  isHovered.value = false
  emit('hover', props.task, false)
}

const startResize = (event, direction) => {
  event.preventDefault()
  event.stopPropagation()
  
  emit('resize', {
    task: props.task,
    direction,
    startEvent: event
  })
}

const getTaskBlockClass = (task) => {
  const baseClass = 'bg-gradient-to-r border-l-4'
  
  switch (task.priority) {
    case 'High':
      return `${baseClass} from-red-500 to-red-600 border-red-700 hover:from-red-600 hover:to-red-700`
    case 'Medium':
      return `${baseClass} from-blue-500 to-blue-600 border-blue-700 hover:from-blue-600 hover:to-blue-700`
    case 'Low':
      return `${baseClass} from-green-500 to-green-600 border-green-700 hover:from-green-600 hover:to-green-700`
    default:
      return `${baseClass} from-gray-500 to-gray-600 border-gray-700 hover:from-gray-600 hover:to-gray-700`
  }
}

const getPriorityIndicatorClass = (priority) => {
  switch (priority) {
    case 'High': return 'bg-red-300 shadow-sm'
    case 'Medium': return 'bg-blue-300 shadow-sm'
    case 'Low': return 'bg-green-300 shadow-sm'
    default: return 'bg-gray-300 shadow-sm'
  }
}

const getStatusIndicatorClass = (status) => {
  switch (status) {
    case 'Completed': return 'bg-green-400'
    case 'Working': return 'bg-blue-400'
    case 'Overdue': return 'bg-red-400'
    case 'Open': return 'bg-yellow-400'
    default: return 'bg-gray-400'
  }
}

const getProgressText = () => {
  if (props.task.progress !== undefined) {
    return `${props.task.progress}%`
  }
  
  if (props.task.status === 'Completed') return '100%'
  if (props.task.status === 'Working') return '50%'
  if (props.task.status === 'Open') return '0%'
  
  return ''
}

const getAssigneeName = (assigneeId) => {
  const assignee = props.assignees.find(a => a.id === assigneeId)
  return assignee ? assignee.name : assigneeId
}

const formatDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) return ''
  
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  const formatOptions = { month: 'short', day: 'numeric' }
  
  if (start.getFullYear() !== end.getFullYear()) {
    formatOptions.year = 'numeric'
  }
  
  if (start.toDateString() === end.toDateString()) {
    return start.toLocaleDateString('en-US', formatOptions)
  }
  
  return `${start.toLocaleDateString('en-US', formatOptions)} - ${end.toLocaleDateString('en-US', formatOptions)}`
}
</script>

<style scoped>
.task-block {
  min-height: 60px;
  user-select: none;
}

.task-block:hover {
  transform: translateY(-1px);
}

.resize-handle-left:hover,
.resize-handle-right:hover {
  @apply bg-white/50;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Smooth transitions */
.task-block * {
  transition: all 0.2s ease;
}

/* Drag feedback */
.task-block.scale-105 {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

/* Tooltip positioning */
.task-tooltip {
  pointer-events: none;
  z-index: 1000;
}

/* Animation for hover states */
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1); }
}

.task-block:hover {
  animation: pulse-glow 2s infinite;
}
</style>
