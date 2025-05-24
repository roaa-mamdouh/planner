<template>
  <div class="timeline-view">
    <!-- Timeline Header -->
    <div class="timeline-header flex items-center justify-between mb-4">
      <div class="timeline-controls flex items-center gap-3">
        <div class="zoom-controls flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button 
            v-for="zoom in zoomLevels" 
            :key="zoom.value"
            @click="setZoom(zoom.value)"
            :class="[
              'px-3 py-1 rounded text-sm font-medium transition-all duration-200',
              currentZoom === zoom.value 
                ? 'bg-white dark:bg-gray-600 shadow-sm text-blue-600 dark:text-blue-400' 
                : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
            ]"
          >
            {{ zoom.label }}
          </button>
        </div>
      </div>

      <div class="timeline-filters flex items-center gap-3">
        <div class="filter-dropdown relative">
          <Button 
            :variant="'ghost'" 
            theme="gray" 
            size="sm"
            @click="showFilters = !showFilters"
          >
            <FeatherIcon name="filter" class="w-4 h-4 mr-2" />
            Filters
          </Button>
          <div v-if="showFilters" class="filter-menu absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 z-50">
            <div class="space-y-4">
              <div class="filter-group">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">Status</label>
                <div class="space-y-2">
                  <label v-for="status in statusOptions" :key="status" class="flex items-center">
                    <input 
                      type="checkbox" 
                      :value="status"
                      v-model="selectedStatuses"
                      class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    >
                    <span class="ml-2 text-sm text-gray-600 dark:text-gray-400">{{ status }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Timeline Container -->
    <div ref="timelineContainer" class="timeline-container min-h-[500px] relative">
      <div v-if="loading" class="timeline-loader absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm">
        <div class="loading-spinner"></div>
      </div>
      <div ref="timelineElement" class="timeline-element w-full h-full"></div>
    </div>

    <!-- Task Details Tooltip -->
    <div 
      v-if="hoveredTask"
      class="task-tooltip absolute bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 max-w-sm z-50"
      :style="tooltipStyle"
    >
      <div class="flex items-start justify-between mb-3">
        <div class="flex-1">
          <span :class="['task-priority-badge', `priority-${hoveredTask.priority?.toLowerCase() || 'medium'}`]">
            {{ hoveredTask.priority || 'Medium' }}
          </span>
          <h4 class="font-semibold text-gray-900 dark:text-white mt-2">{{ hoveredTask.subject }}</h4>
        </div>
      </div>
      <div class="space-y-2 text-sm">
        <div class="flex items-center text-gray-600 dark:text-gray-400">
          <FeatherIcon name="calendar" class="w-4 h-4 mr-2" />
          {{ formatDateRange(hoveredTask.exp_start_date, hoveredTask.exp_end_date) }}
        </div>
        <div class="flex items-center text-gray-600 dark:text-gray-400">
          <FeatherIcon name="clock" class="w-4 h-4 mr-2" />
          {{ hoveredTask.expected_time }}h estimated
        </div>
        <div v-if="hoveredTask.project" class="flex items-center text-gray-600 dark:text-gray-400">
          <FeatherIcon name="folder" class="w-4 h-4 mr-2" />
          {{ hoveredTask.project }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { Timeline, DataSet } from 'vis-timeline/standalone'
import 'vis-timeline/styles/vis-timeline-graph2d.css'

const props = defineProps({
  tasks: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['taskClick', 'taskUpdate'])

// Timeline refs and state
const timelineContainer = ref(null)
const timelineElement = ref(null)
let timeline = null
const currentZoom = ref('day')
const showFilters = ref(false)
const selectedStatuses = ref(['Working', 'Completed', 'Overdue'])
const hoveredTask = ref(null)
const tooltipStyle = ref({
  top: '0px',
  left: '0px',
  display: 'none'
})

// Constants
const zoomLevels = [
  { label: 'Day', value: 'day' },
  { label: 'Week', value: 'week' },
  { label: 'Month', value: 'month' }
]

const statusOptions = ['Working', 'Completed', 'Overdue', 'Not Started']

// Timeline options
const options = {
  editable: {
    updateTime: true,
    updateGroup: true
  },
  onMove: function(item, callback) {
    emit('taskUpdate', {
      id: item.id,
      start: item.start,
      end: item.end,
      group: item.group
    })
    callback(item)
  },
  margin: {
    item: {
      horizontal: 10,
      vertical: 5
    }
  },
  orientation: 'top'
}

// Computed
const filteredTasks = computed(() => {
  return props.tasks.filter(task => 
    selectedStatuses.value.includes(task.status)
  )
})

// Methods
const initTimeline = () => {
  if (!timelineElement.value) return

  const items = new DataSet(
    filteredTasks.value.map(task => ({
      id: task.name,
      content: createTaskContent(task),
      start: new Date(task.exp_start_date),
      end: new Date(task.exp_end_date),
      group: task.assigned_to,
      className: `task-item status-${task.status.toLowerCase()}`
    }))
  )

  const groups = new DataSet(
    [...new Set(props.tasks.map(t => t.assigned_to))].map(employee => ({
      id: employee,
      content: employee
    }))
  )

  timeline = new Timeline(timelineElement.value, items, groups, options)
  
  // Event listeners
  timeline.on('click', (props) => {
    const item = props.item
    if (item) {
      emit('taskClick', item)
    }
  })

  timeline.on('itemover', (props) => {
    const item = items.get(props.item)
    if (item) {
      const task = props.tasks.find(t => t.name === item.id)
      if (task) {
        hoveredTask.value = task
        updateTooltipPosition(props.event)
      }
    }
  })

  timeline.on('itemout', () => {
    hoveredTask.value = null
    tooltipStyle.value.display = 'none'
  })
}

const createTaskContent = (task) => {
  return `
    <div class="task-item-content">
      <div class="task-title">${task.subject}</div>
      <div class="task-meta">
        ${task.project ? `<span class="task-project">${task.project}</span>` : ''}
        <span class="task-time">${task.expected_time}h</span>
      </div>
    </div>
  `
}

const updateTooltipPosition = (event) => {
  if (!event) return
  
  tooltipStyle.value = {
    top: `${event.pageY + 10}px`,
    left: `${event.pageX + 10}px`,
    display: 'block'
  }
}

const setZoom = (zoom) => {
  currentZoom.value = zoom
  if (!timeline) return

  const now = new Date()
  let start = new Date()
  let end = new Date()

  switch (zoom) {
    case 'day':
      start.setHours(0, 0, 0)
      end.setHours(23, 59, 59)
      break
    case 'week':
      start.setDate(now.getDate() - now.getDay())
      end.setDate(start.getDate() + 6)
      break
    case 'month':
      start.setDate(1)
      end.setMonth(start.getMonth() + 1, 0)
      break
  }

  timeline.setWindow(start, end)
}

const formatDateRange = (start, end) => {
  if (!start || !end) return ''
  
  const startDate = new Date(start)
  const endDate = new Date(end)
  
  return `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`
}

// Watchers
watch(() => filteredTasks.value, () => {
  if (timeline) {
    timeline.setItems(new DataSet(
      filteredTasks.value.map(task => ({
        id: task.name,
        content: createTaskContent(task),
        start: new Date(task.exp_start_date),
        end: new Date(task.exp_end_date),
        group: task.assigned_to,
        className: `task-item status-${task.status.toLowerCase()}`
      }))
    ))
  }
}, { deep: true })

// Lifecycle hooks
onMounted(() => {
  initTimeline()
})

onUnmounted(() => {
  if (timeline) {
    timeline.destroy()
  }
})
</script>

<style scoped>
.timeline-view {
  @apply relative;
}

.timeline-container {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden;
}

/* Timeline customization */
:deep(.vis-timeline) {
  border: none;
  font-family: inherit;
}

:deep(.vis-item) {
  @apply rounded-lg border-none shadow-sm transition-all duration-200;
  background-color: white;
}

:deep(.vis-item.status-working) {
  @apply bg-blue-50 border-l-4 border-l-blue-500;
}

:deep(.vis-item.status-completed) {
  @apply bg-green-50 border-l-4 border-l-green-500;
}

:deep(.vis-item.status-overdue) {
  @apply bg-red-50 border-l-4 border-l-red-500;
}

:deep(.vis-item.vis-selected) {
  @apply ring-2 ring-blue-500 ring-offset-2;
}

:deep(.task-item-content) {
  @apply p-2;
}

:deep(.task-title) {
  @apply font-medium text-gray-900 dark:text-white text-sm mb-1;
}

:deep(.task-meta) {
  @apply flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400;
}

:deep(.task-project) {
  @apply bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded;
}

:deep(.task-time) {
  @apply bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded;
}

/* Loading spinner */
.loading-spinner {
  @apply w-8 h-8 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin;
}

/* Tooltip */
.task-tooltip {
  @apply transition-all duration-200 transform;
}
</style>
