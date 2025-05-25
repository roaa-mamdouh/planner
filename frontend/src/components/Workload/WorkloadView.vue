<template>
  <div class="workload-view">
    <!-- Workload Header Controls -->
    <div class="workload-header flex items-center justify-between mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div class="flex items-center gap-4">
        <!-- View Mode Toggle -->
        <div class="view-toggle flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button 
            v-for="mode in viewModes" 
            :key="mode.value"
            @click="setViewMode(mode.value)"
            :class="[
              'px-3 py-1.5 rounded text-sm font-medium transition-all duration-200',
              currentViewMode === mode.value 
                ? 'bg-white dark:bg-gray-600 shadow-sm text-blue-600 dark:text-blue-400' 
                : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
            ]"
          >
            {{ mode.label }}
          </button>
        </div>

        <!-- Date Navigation -->
        <div class="date-navigation flex items-center gap-2">
          <Button 
            :variant="'ghost'" 
            theme="gray" 
            size="sm"
            @click="navigateDate(-1)"
          >
            <FeatherIcon name="chevron-left" class="w-4 h-4" />
          </Button>
          
          <div class="date-display px-3 py-1 bg-gray-50 dark:bg-gray-700 rounded text-sm font-medium">
            {{ formatDateRange() }}
          </div>
          
          <Button 
            :variant="'ghost'" 
            theme="gray" 
            size="sm"
            @click="navigateDate(1)"
          >
            <FeatherIcon name="chevron-right" class="w-4 h-4" />
          </Button>
          
          <Button 
            :variant="'ghost'" 
            theme="gray" 
            size="sm"
            @click="goToToday"
          >
            Today
          </Button>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- Capacity Settings -->
        <div class="capacity-settings flex items-center gap-2">
          <span class="text-sm text-gray-600 dark:text-gray-400">Hours per day:</span>
          <select 
            v-model="hoursPerDay" 
            class="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
            @change="updateCapacitySettings"
          >
            <option value="6">6h</option>
            <option value="8">8h</option>
            <option value="10">10h</option>
          </select>
        </div>

        <!-- Filters -->
        <Button 
          :variant="'ghost'" 
          theme="gray" 
          size="sm"
          @click="showFilters = !showFilters"
        >
          <FeatherIcon name="filter" class="w-4 h-4 mr-2" />
          Filters
        </Button>
      </div>
    </div>

    <!-- Filter Panel -->
    <div v-if="showFilters" class="filter-panel mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</label>
          <div class="space-y-2">
            <label v-for="status in statusOptions" :key="status" class="flex items-center">
              <input 
                type="checkbox" 
                :value="status"
                v-model="selectedStatuses"
                class="rounded border-gray-300 text-blue-600"
              >
              <span class="ml-2 text-sm">{{ status }}</span>
            </label>
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Priority</label>
          <div class="space-y-2">
            <label v-for="priority in priorityOptions" :key="priority" class="flex items-center">
              <input 
                type="checkbox" 
                :value="priority"
                v-model="selectedPriorities"
                class="rounded border-gray-300 text-blue-600"
              >
              <span class="ml-2 text-sm">{{ priority }}</span>
            </label>
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Projects</label>
          <TextInput 
            v-model="projectFilter"
            placeholder="Filter by project..."
            size="sm"
          />
        </div>
      </div>
    </div>

    <!-- Workload Grid -->
    <div class="workload-grid bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <!-- Grid Header -->
      <div class="grid-header sticky top-0 z-40 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
        <div class="grid grid-cols-12 gap-0">
          <!-- Assignee Column Header -->
          <div class="col-span-3 p-4 border-r border-gray-200 dark:border-gray-600">
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-900 dark:text-white">Assignee</span>
              <span class="text-xs text-gray-500 dark:text-gray-400">Capacity</span>
            </div>
          </div>
          
          <!-- Date Column Headers -->
          <div class="col-span-9 grid" :style="{ gridTemplateColumns: `repeat(${dateColumns.length}, 1fr)` }">
            <div 
              v-for="date in dateColumns" 
              :key="date.key"
              class="p-2 text-center border-r border-gray-200 dark:border-gray-600 last:border-r-0"
            >
              <div class="text-xs font-medium text-gray-900 dark:text-white">{{ date.label }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ date.sublabel }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Assignee Rows -->
      <div class="assignee-rows">
        <div 
          v-for="assignee in filteredAssignees" 
          :key="assignee.id"
          class="assignee-row border-b border-gray-100 dark:border-gray-700 last:border-b-0"
        >
          <div class="grid grid-cols-12 gap-0 min-h-[80px]">
            <!-- Assignee Info Column -->
            <div class="col-span-3 p-4 border-r border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800">
              <div class="flex items-center justify-between h-full">
                <div class="flex items-center gap-3">
                  <Avatar 
                    :image="assignee.image" 
                    :label="assignee.name"
                    size="sm"
                  />
                  <div>
                    <div class="font-medium text-gray-900 dark:text-white text-sm">{{ assignee.name }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ assignee.role }}</div>
                  </div>
                </div>
                
                <!-- Capacity Indicator -->
                <div class="capacity-indicator">
                  <div class="text-xs text-gray-600 dark:text-gray-400 mb-1">
                    {{ assignee.totalHours }}h / {{ assignee.capacity }}h
                  </div>
                  <div class="w-16 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                    <div 
                      class="h-full transition-all duration-300"
                      :class="getCapacityBarClass(assignee.utilization)"
                      :style="{ width: `${Math.min(assignee.utilization, 100)}%` }"
                    ></div>
                  </div>
                  <div class="text-xs mt-1" :class="getUtilizationTextClass(assignee.utilization)">
                    {{ Math.round(assignee.utilization) }}%
                  </div>
                </div>
              </div>
            </div>

            <!-- Task Timeline Columns -->
            <div class="col-span-9 relative">
              <div class="grid h-full" :style="{ gridTemplateColumns: `repeat(${dateColumns.length}, 1fr)` }">
                <!-- Date Column Backgrounds -->
                <div 
                  v-for="(date, index) in dateColumns" 
                  :key="`bg-${date.key}`"
                  class="border-r border-gray-100 dark:border-gray-700 last:border-r-0 relative"
                  :class="{ 'bg-blue-50 dark:bg-blue-900/10': date.isToday }"
                  @drop="handleDrop($event, assignee.id, date.date)"
                  @dragover.prevent
                  @dragenter.prevent
                >
                  <!-- Daily Capacity Indicator -->
                  <div class="absolute top-1 right-1 text-xs text-gray-400">
                    {{ getDailyHours(assignee.id, date.date) }}h
                  </div>
                </div>
              </div>

              <!-- Task Blocks -->
              <div class="absolute inset-0 p-1">
                <div 
                  v-for="task in getAssigneeTasks(assignee.id)" 
                  :key="task.id"
                  class="task-block absolute cursor-move"
                  :style="getTaskBlockStyle(task)"
                  :class="getTaskBlockClass(task)"
                  @mousedown="startDrag($event, task)"
                  @click="$emit('taskClick', task.id)"
                  draggable="true"
                  @dragstart="handleDragStart($event, task)"
                >
                  <div class="task-content p-2 text-xs">
                    <div class="font-medium text-white truncate">{{ task.title }}</div>
                    <div class="text-white/80 truncate">{{ task.project }}</div>
                    <div class="text-white/60">{{ task.duration }}h</div>
                  </div>
                  
                  <!-- Resize Handles -->
                  <div class="resize-handle resize-left absolute left-0 top-0 w-1 h-full cursor-ew-resize opacity-0 hover:opacity-100 bg-white/50"></div>
                  <div class="resize-handle resize-right absolute right-0 top-0 w-1 h-full cursor-ew-resize opacity-0 hover:opacity-100 bg-white/50"></div>
                </div>
              </div>

              <!-- Unscheduled Tasks Bucket -->
              <div 
                v-if="getUnscheduledTasks(assignee.id).length > 0"
                class="unscheduled-bucket absolute right-2 top-2 w-32 bg-gray-100 dark:bg-gray-700 rounded p-2"
                @drop="handleUnscheduledDrop($event, assignee.id)"
                @dragover.prevent
                @dragenter.prevent
              >
                <div class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Unscheduled ({{ getUnscheduledTasks(assignee.id).length }})
                </div>
                <div class="space-y-1">
                  <div 
                    v-for="task in getUnscheduledTasks(assignee.id).slice(0, 3)" 
                    :key="task.id"
                    class="text-xs p-1 bg-white dark:bg-gray-600 rounded cursor-move"
                    draggable="true"
                    @dragstart="handleDragStart($event, task)"
                  >
                    {{ task.title }}
                  </div>
                  <div v-if="getUnscheduledTasks(assignee.id).length > 3" class="text-xs text-gray-500">
                    +{{ getUnscheduledTasks(assignee.id).length - 3 }} more
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredAssignees.length === 0" class="empty-state p-8 text-center">
        <FeatherIcon name="users" class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
        <p class="text-gray-500 dark:text-gray-400">No assignees found</p>
        <p class="text-gray-400 dark:text-gray-500 text-sm mt-1">Try adjusting your filters</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Avatar } from 'frappe-ui'

const props = defineProps({
  assignees: {
    type: Array,
    required: true
  },
  tasks: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['taskClick', 'taskUpdate', 'taskMove'])

// View state
const currentViewMode = ref('week')
const currentDate = ref(new Date())
const hoursPerDay = ref(8)
const showFilters = ref(false)

// Filter state
const selectedStatuses = ref(['Working', 'Open', 'Completed'])
const selectedPriorities = ref(['High', 'Medium', 'Low'])
const projectFilter = ref('')

// Constants
const viewModes = [
  { label: 'Day', value: 'day' },
  { label: 'Week', value: 'week' },
  { label: 'Month', value: 'month' }
]

const statusOptions = ['Working', 'Open', 'Completed', 'Overdue']
const priorityOptions = ['High', 'Medium', 'Low']

// Computed properties
const dateColumns = computed(() => {
  const columns = []
  const start = getViewStartDate()
  const days = getViewDays()
  
  for (let i = 0; i < days; i++) {
    const date = new Date(start)
    date.setDate(start.getDate() + i)
    
    columns.push({
      key: date.toISOString().split('T')[0],
      date: new Date(date),
      label: formatDateLabel(date),
      sublabel: formatDateSublabel(date),
      isToday: isToday(date)
    })
  }
  
  return columns
})

const filteredAssignees = computed(() => {
  return props.assignees.map(assignee => {
    const tasks = getAssigneeTasks(assignee.id)
    const totalHours = tasks.reduce((sum, task) => sum + (task.duration || 0), 0)
    const capacity = getAssigneeCapacity(assignee.id)
    const utilization = capacity > 0 ? (totalHours / capacity) * 100 : 0
    
    return {
      ...assignee,
      totalHours,
      capacity,
      utilization
    }
  })
})

// Methods
const setViewMode = (mode) => {
  currentViewMode.value = mode
}

const navigateDate = (direction) => {
  const newDate = new Date(currentDate.value)
  
  switch (currentViewMode.value) {
    case 'day':
      newDate.setDate(newDate.getDate() + direction)
      break
    case 'week':
      newDate.setDate(newDate.getDate() + (direction * 7))
      break
    case 'month':
      newDate.setMonth(newDate.getMonth() + direction)
      break
  }
  
  currentDate.value = newDate
}

const goToToday = () => {
  currentDate.value = new Date()
}

const getViewStartDate = () => {
  const date = new Date(currentDate.value)
  
  switch (currentViewMode.value) {
    case 'day':
      return date
    case 'week':
      const dayOfWeek = date.getDay()
      date.setDate(date.getDate() - dayOfWeek)
      return date
    case 'month':
      date.setDate(1)
      return date
    default:
      return date
  }
}

const getViewDays = () => {
  switch (currentViewMode.value) {
    case 'day':
      return 1
    case 'week':
      return 7
    case 'month':
      const date = new Date(currentDate.value)
      return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
    default:
      return 7
  }
}

const formatDateRange = () => {
  const start = getViewStartDate()
  const end = new Date(start)
  end.setDate(start.getDate() + getViewDays() - 1)
  
  const options = { month: 'short', day: 'numeric' }
  if (start.getFullYear() !== new Date().getFullYear()) {
    options.year = 'numeric'
  }
  
  if (currentViewMode.value === 'day') {
    return start.toLocaleDateString('en-US', { ...options, weekday: 'long' })
  }
  
  return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`
}

const formatDateLabel = (date) => {
  switch (currentViewMode.value) {
    case 'day':
      return date.toLocaleDateString('en-US', { weekday: 'long' })
    case 'week':
      return date.toLocaleDateString('en-US', { weekday: 'short' })
    case 'month':
      return date.getDate().toString()
    default:
      return date.toLocaleDateString('en-US', { weekday: 'short' })
  }
}

const formatDateSublabel = (date) => {
  switch (currentViewMode.value) {
    case 'day':
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    case 'week':
      return date.getDate().toString()
    case 'month':
      return date.toLocaleDateString('en-US', { weekday: 'short' })
    default:
      return ''
  }
}

const isToday = (date) => {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

const getAssigneeTasks = (assigneeId) => {
  return props.tasks.filter(task => 
    task.assignee === assigneeId && 
    task.startDate && 
    task.endDate &&
    selectedStatuses.value.includes(task.status) &&
    selectedPriorities.value.includes(task.priority) &&
    (!projectFilter.value || task.project?.toLowerCase().includes(projectFilter.value.toLowerCase()))
  )
}

const getUnscheduledTasks = (assigneeId) => {
  return props.tasks.filter(task => 
    task.assignee === assigneeId && 
    (!task.startDate || !task.endDate) &&
    selectedStatuses.value.includes(task.status)
  )
}

const getAssigneeCapacity = (assigneeId) => {
  const days = getViewDays()
  return days * hoursPerDay.value
}

const getDailyHours = (assigneeId, date) => {
  const tasks = getAssigneeTasks(assigneeId)
  return tasks
    .filter(task => {
      const taskStart = new Date(task.startDate)
      const taskEnd = new Date(task.endDate)
      return date >= taskStart && date <= taskEnd
    })
    .reduce((sum, task) => {
      const taskDays = Math.ceil((new Date(task.endDate) - new Date(task.startDate)) / (1000 * 60 * 60 * 24)) + 1
      return sum + (task.duration / taskDays)
    }, 0)
}

const getTaskBlockStyle = (task) => {
  const startDate = new Date(task.startDate)
  const endDate = new Date(task.endDate)
  const viewStart = getViewStartDate()
  const viewDays = getViewDays()
  
  // Calculate position and width
  const startOffset = Math.max(0, (startDate - viewStart) / (1000 * 60 * 60 * 24))
  const duration = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1
  
  const left = (startOffset / viewDays) * 100
  const width = (duration / viewDays) * 100
  
  return {
    left: `${left}%`,
    width: `${Math.min(width, 100 - left)}%`,
    top: '4px',
    height: 'calc(100% - 8px)',
    zIndex: 10
  }
}

const getTaskBlockClass = (task) => {
  const baseClass = 'rounded shadow-sm border-l-4 transition-all duration-200 hover:shadow-md'
  
  switch (task.status) {
    case 'Completed':
      return `${baseClass} bg-green-500 border-l-green-600`
    case 'Working':
      return `${baseClass} bg-blue-500 border-l-blue-600`
    case 'Overdue':
      return `${baseClass} bg-red-500 border-l-red-600`
    default:
      return `${baseClass} bg-gray-500 border-l-gray-600`
  }
}

const getCapacityBarClass = (utilization) => {
  if (utilization <= 80) return 'bg-green-500'
  if (utilization <= 100) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getUtilizationTextClass = (utilization) => {
  if (utilization <= 80) return 'text-green-600 dark:text-green-400'
  if (utilization <= 100) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

// Utility function to format date as YYYY-MM-DD
const formatDateForAPI = (date) => {
  if (!date) return null
  const d = new Date(date)
  return d.getFullYear() + '-' + 
         String(d.getMonth() + 1).padStart(2, '0') + '-' + 
         String(d.getDate()).padStart(2, '0')
}

// Drag and drop handlers
const handleDragStart = (event, task) => {
  event.dataTransfer.setData('application/json', JSON.stringify(task))
  event.dataTransfer.effectAllowed = 'move'
}

const handleDrop = (event, assigneeId, date) => {
  event.preventDefault()
  const taskData = JSON.parse(event.dataTransfer.getData('application/json'))
  
  // Calculate end date based on task duration (in days)
  const startDate = new Date(date)
  const endDate = new Date(startDate)
  const durationDays = Math.max(1, Math.ceil((taskData.duration || 8) / 8)) // Convert hours to days, minimum 1 day
  endDate.setDate(startDate.getDate() + durationDays - 1)
  
  emit('taskMove', {
    taskId: taskData.id,
    assigneeId,
    startDate: formatDateForAPI(startDate),
    endDate: formatDateForAPI(endDate)
  })
}

const handleUnscheduledDrop = (event, assigneeId) => {
  event.preventDefault()
  const taskData = JSON.parse(event.dataTransfer.getData('application/json'))
  
  emit('taskMove', {
    taskId: taskData.id,
    assigneeId,
    startDate: null,
    endDate: null
  })
}

const updateCapacitySettings = () => {
  // Emit capacity settings change
  emit('capacityChange', { hoursPerDay: hoursPerDay.value })
}

// Lifecycle
onMounted(() => {
  // Initialize component
})
</script>

<style scoped>
.workload-view {
  @apply w-full;
}

.task-block {
  @apply relative overflow-hidden;
}

.task-block:hover .resize-handle {
  @apply opacity-100;
}

.unscheduled-bucket {
  @apply transition-all duration-200;
}

.unscheduled-bucket:hover {
  @apply bg-gray-200 dark:bg-gray-600;
}

/* Grid styling */
.workload-grid {
  @apply relative;
  min-height: 400px;
}

.assignee-row:hover {
  @apply bg-gray-50/50 dark:bg-gray-700/50;
}

/* Scrollbar styling */
.workload-grid::-webkit-scrollbar {
  @apply w-2 h-2;
}

.workload-grid::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-700;
}

.workload-grid::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600 rounded;
}

.workload-grid::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}
</style>
