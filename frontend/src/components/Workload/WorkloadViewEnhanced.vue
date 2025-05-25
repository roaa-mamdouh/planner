<template>
  <div class="workload-view-enhanced">
    <!-- Loading Skeleton -->
    <div v-if="loading" class="loading-skeleton">
      <div class="animate-pulse space-y-4">
        <div class="h-16 bg-gray-200 dark:bg-gray-700 rounded-xl"></div>
        <div class="h-96 bg-gray-200 dark:bg-gray-700 rounded-xl"></div>
      </div>
    </div>

    <!-- Enhanced Header -->
    <div v-else class="workload-header-enhanced mb-6 p-6 bg-gradient-to-r from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
      <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
        <!-- Left Section -->
        <div class="flex items-center gap-4">
          <div class="view-toggle flex bg-gray-100 dark:bg-gray-700 rounded-xl p-1.5">
            <button 
              v-for="mode in viewModes" 
              :key="mode.value"
              @click="currentViewMode = mode.value"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 flex items-center gap-2',
                currentViewMode === mode.value 
                  ? 'bg-white dark:bg-gray-600 shadow-md text-blue-600 dark:text-blue-400' 
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              ]"
            >
              <FeatherIcon :name="mode.icon" class="w-4 h-4" />
              {{ mode.label }}
            </button>
          </div>

          <div class="date-navigation flex items-center gap-3 bg-white dark:bg-gray-800 rounded-xl p-2 shadow-sm border border-gray-200 dark:border-gray-700">
            <Button 
              variant="ghost" 
              theme="gray" 
              size="sm"
              @click="navigateDate(-1)"
            >
              <FeatherIcon name="chevron-left" class="w-4 h-4" />
            </Button>
            
            <div class="px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg text-sm font-semibold text-blue-900 dark:text-blue-100 min-w-[200px] text-center">
              {{ formatDateRange() }}
            </div>
            
            <Button 
              variant="ghost" 
              theme="gray" 
              size="sm"
              @click="navigateDate(1)"
            >
              <FeatherIcon name="chevron-right" class="w-4 h-4" />
            </Button>
            
            <Button 
              variant="ghost" 
              theme="blue" 
              size="sm"
              @click="goToToday"
            >
              Today
            </Button>
          </div>
        </div>

        <!-- Right Section -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-xl p-3 shadow-sm border border-gray-200 dark:border-gray-700">
            <FeatherIcon name="clock" class="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Hours/day:</span>
            <select 
              v-model="hoursPerDay" 
              class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="6">6h</option>
              <option value="8">8h</option>
              <option value="10">10h</option>
            </select>
          </div>

          <Button 
            variant="ghost" 
            theme="gray" 
            size="sm"
            @click="showUtilizationChart = !showUtilizationChart"
            :class="showUtilizationChart ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400' : ''"
          >
            <FeatherIcon name="bar-chart-2" class="w-4 h-4 mr-2" />
            Analytics
          </Button>
        </div>
      </div>

      <!-- Utilization Chart -->
      <Transition name="slide-down">
        <div v-if="showUtilizationChart" class="mt-6 p-5 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Team Utilization Overview</h3>
          <div class="space-y-3">
            <div v-for="assignee in assignees" :key="assignee.id" class="flex items-center gap-4">
              <div class="flex items-center gap-2 w-48">
                <Avatar :image="assignee.image" :label="assignee.name" size="xs" />
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ assignee.name }}</span>
              </div>
              <div class="flex-1 flex items-center gap-3">
                <div class="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    class="h-full transition-all duration-500 ease-out rounded-full"
                    :class="getCapacityBarClass(assignee.utilization)"
                    :style="{ width: `${Math.min(assignee.utilization, 100)}%` }"
                  ></div>
                </div>
                <span class="text-sm font-semibold w-12 text-right" :class="getUtilizationTextClass(assignee.utilization)">
                  {{ Math.round(assignee.utilization) }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Enhanced Workload Grid -->
    <div class="workload-grid bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <!-- Grid Header -->
      <div class="sticky top-0 z-40 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800 border-b border-gray-200 dark:border-gray-600">
        <div class="grid grid-cols-12 gap-0">
          <div class="col-span-3 p-5 border-r border-gray-200 dark:border-gray-600">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <FeatherIcon name="users" class="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <span class="font-semibold text-gray-900 dark:text-white">Team Members</span>
              </div>
              <div class="flex items-center gap-2">
                <FeatherIcon name="zap" class="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <span class="text-xs font-medium text-gray-500 dark:text-gray-400">Utilization</span>
              </div>
            </div>
          </div>
          
          <div class="col-span-9 grid" :style="{ gridTemplateColumns: `repeat(${dateColumns.length}, 1fr)` }">
            <div 
              v-for="date in dateColumns" 
              :key="date.key"
              class="p-3 text-center border-r border-gray-200 dark:border-gray-600 last:border-r-0"
              :class="{ 'bg-blue-50 dark:bg-blue-900/20': date.isToday }"
            >
              <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ date.label }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ date.sublabel }}</div>
              <div v-if="date.isToday" class="w-2 h-2 bg-blue-500 rounded-full mx-auto mt-1"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Assignee Rows -->
      <div class="assignee-rows">
        <div 
          v-for="assignee in assignees" 
          :key="assignee.id"
          class="border-b border-gray-100 dark:border-gray-700 last:border-b-0 hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-all duration-200"
        >
          <div class="grid grid-cols-12 gap-0 min-h-[100px]">
            <!-- Assignee Info -->
            <div class="col-span-3 p-5 border-r border-gray-200 dark:border-gray-600 bg-gradient-to-r from-gray-50/50 to-transparent dark:from-gray-800/50">
              <div class="flex items-center justify-between h-full">
                <div class="flex items-center gap-4">
                  <div class="relative">
                    <Avatar 
                      :image="assignee.image" 
                      :label="assignee.name"
                      size="md"
                      class="ring-2 ring-white dark:ring-gray-700 shadow-sm"
                    />
                    <div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white dark:border-gray-800" :class="getStatusIndicatorClass(assignee.utilization)"></div>
                  </div>
                  <div>
                    <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ assignee.name }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ assignee.role || 'Team Member' }}</div>
                    <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {{ assignee.totalHours || 0 }}h / {{ assignee.capacity || 40 }}h
                    </div>
                  </div>
                </div>
                
                <div class="text-right">
                  <div class="text-sm font-bold mb-2" :class="getUtilizationTextClass(assignee.utilization)">
                    {{ Math.round(assignee.utilization || 0) }}%
                  </div>
                  <div class="w-20 h-3 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden shadow-inner">
                    <div 
                      class="h-full transition-all duration-500 ease-out rounded-full"
                      :class="getCapacityBarClass(assignee.utilization)"
                      :style="{ width: `${Math.min(assignee.utilization || 0, 100)}%` }"
                    ></div>
                  </div>
                  <div class="text-xs mt-1 font-medium" :class="getUtilizationLabelClass(assignee.utilization)">
                    {{ getUtilizationLabel(assignee.utilization) }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Task Timeline -->
            <div class="col-span-9 relative">
              <div class="grid h-full" :style="{ gridTemplateColumns: `repeat(${dateColumns.length}, 1fr)` }">
                <div 
                  v-for="(date, index) in dateColumns" 
                  :key="`bg-${date.key}`"
                  class="border-r border-gray-100 dark:border-gray-700 last:border-r-0 relative min-h-[100px] transition-all duration-200"
                  :class="{ 
                    'bg-blue-50/50 dark:bg-blue-900/10': date.isToday,
                    'hover:bg-gray-50 dark:hover:bg-gray-700/20': !date.isToday,
                    'drop-zone-active': isDragOver && dragOverDate === date.key && dragOverAssignee === assignee.id
                  }"
                  @drop="handleDrop($event, assignee.id, date.date)"
                  @dragover.prevent="handleDragOver($event, assignee.id, date.key)"
                  @dragenter.prevent="handleDragEnter($event, assignee.id, date.key)"
                  @dragleave="handleDragLeave"
                >
                  <div v-if="date.isToday" class="absolute left-1/2 top-0 w-0.5 h-full bg-blue-500 transform -translate-x-1/2 opacity-30"></div>
                </div>
              </div>

              <!-- Task Blocks -->
              <div class="absolute inset-0 p-1">
                <div 
                  v-for="task in getAssigneeTasks(assignee.id)" 
                  :key="task.id"
                  class="task-block absolute cursor-move group rounded-lg shadow-sm hover:shadow-md transition-all duration-200"
                  :style="getTaskBlockStyle(task)"
                  :class="getTaskBlockClass(task)"
                  @click="$emit('taskClick', task.id)"
                  draggable="true"
                  @dragstart="handleDragStart($event, task)"
                >
                  <div class="p-3 text-xs h-full flex flex-col justify-between text-white">
                    <div>
                      <div class="font-semibold truncate mb-1">{{ task.title }}</div>
                      <div class="text-white/80 truncate text-xs">{{ task.project }}</div>
                    </div>
                    <div class="flex items-center justify-between mt-2">
                      <div class="text-white/70 text-xs">{{ task.duration }}h</div>
                      <div class="w-1.5 h-1.5 bg-white/50 rounded-full" :class="getPriorityIndicatorClass(task.priority)"></div>
                    </div>
                  </div>
                  
                  <!-- Resize Handles -->
                  <div class="resize-handle-left absolute left-0 top-0 w-2 h-full cursor-ew-resize opacity-0 group-hover:opacity-100 bg-white/30 transition-opacity duration-200" @mousedown.stop="startResize($event, task, 'left')"></div>
                  <div class="resize-handle-right absolute right-0 top-0 w-2 h-full cursor-ew-resize opacity-0 group-hover:opacity-100 bg-white/30 transition-opacity duration-200" @mousedown.stop="startResize($event, task, 'right')"></div>
                </div>
              </div>

              <!-- Unscheduled Tasks -->
              <div 
                v-if="getUnscheduledTasks(assignee.id).length > 0"
                class="absolute right-2 top-2 w-36 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 rounded-xl p-3 shadow-lg border border-gray-300 dark:border-gray-600"
                @drop="handleUnscheduledDrop($event, assignee.id)"
                @dragover.prevent
                @dragenter.prevent
              >
                <div class="flex items-center justify-between mb-3">
                  <div class="text-xs font-semibold text-gray-700 dark:text-gray-300">Unscheduled</div>
                  <div class="bg-yellow-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                    {{ getUnscheduledTasks(assignee.id).length }}
                  </div>
                </div>
                <div class="space-y-2 max-h-32 overflow-y-auto">
                  <div 
                    v-for="task in getUnscheduledTasks(assignee.id).slice(0, 4)" 
                    :key="task.id"
                    class="text-xs p-2 bg-white dark:bg-gray-600 rounded-lg cursor-move shadow-sm hover:shadow-md transition-all duration-200 border-l-4"
                    :class="getTaskBorderClass(task.priority)"
                    draggable="true"
                    @dragstart="handleDragStart($event, task)"
                    @click="$emit('taskClick', task.id)"
                  >
                    <div class="font-medium text-gray-900 dark:text-white truncate">{{ task.title }}</div>
                    <div class="text-gray-500 dark:text-gray-400 truncate mt-1">{{ task.duration }}h</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="assignees.length === 0" class="p-12 text-center">
        <div class="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <FeatherIcon name="users" class="w-10 h-10 text-gray-400 dark:text-gray-500" />
        </div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">No team members found</h3>
        <p class="text-gray-500 dark:text-gray-400">Add team members to get started with workload planning</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Avatar, Button } from 'frappe-ui'

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
const showUtilizationChart = ref(false)

// Drag and drop state
const isDragOver = ref(false)
const dragOverAssignee = ref(null)
const dragOverDate = ref(null)

// Constants
const viewModes = [
  { label: 'Day', value: 'day', icon: 'calendar' },
  { label: 'Week', value: 'week', icon: 'calendar' },
  { label: 'Month', value: 'month', icon: 'calendar' }
]

// Computed properties
const dateColumns = computed(() => {
  const columns = []
  const today = new Date()
  const startDate = new Date(currentDate.value)
  
  // Generate date columns based on view mode
  const daysToShow = currentViewMode.value === 'day' ? 1 : 
                   currentViewMode.value === 'week' ? 7 : 30
  
  for (let i = 0; i < daysToShow; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    
    const isToday = date.toDateString() === today.toDateString()
    
    columns.push({
      key: date.toISOString().split('T')[0],
      date: date,
      label: date.getDate().toString(),
      sublabel: date.toLocaleDateString('en-US', { weekday: 'short' }),
      isToday
    })
  }
  
  return columns
})

// Methods
const navigateDate = (direction) => {
  const newDate = new Date(currentDate.value)
  const daysToMove = currentViewMode.value === 'day' ? 1 : 
                   currentViewMode.value === 'week' ? 7 : 30
  
  newDate.setDate(newDate.getDate() + (direction * daysToMove))
  currentDate.value = newDate
}

const goToToday = () => {
  currentDate.value = new Date()
}

const formatDateRange = () => {
  const start = new Date(currentDate.value)
  const end = new Date(start)
  
  if (currentViewMode.value === 'day') {
    return start.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  } else if (currentViewMode.value === 'week') {
    end.setDate(start.getDate() + 6)
    return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  } else {
    return start.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
  }
}

const getAssigneeTasks = (assigneeId) => {
  return props.tasks.filter(task => task.assignee === assigneeId && task.isScheduled)
}

const getUnscheduledTasks = (assigneeId) => {
  return props.tasks.filter(task => task.assignee === assigneeId && !task.isScheduled)
}

const getTaskBlockStyle = (task) => {
  if (!task.startDate || !task.endDate) return {}
  
  const startDate = new Date(task.startDate)
  const endDate = new Date(task.endDate)
  const gridStart = new Date(currentDate.value)
  
  // Calculate position and width
  const dayWidth = 100 / dateColumns.value.length
  const startDay = Math.max(0, Math.floor((startDate - gridStart) / (1000 * 60 * 60 * 24)))
  const duration = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1
  
  return {
    left: `${startDay * dayWidth}%`,
    width: `${Math.min(duration * dayWidth, 100 - startDay * dayWidth)}%`,
    top: '8px',
    height: 'calc(100% - 16px)'
  }
}

const getTaskBlockClass = (task) => {
  const baseClass = 'bg-gradient-to-r border-l-4'
  
  switch (task.priority) {
    case 'High':
      return `${baseClass} from-red-500 to-red-600 border-red-700`
    case 'Medium':
      return `${baseClass} from-blue-500 to-blue-600 border-blue-700`
    case 'Low':
      return `${baseClass} from-green-500 to-green-600 border-green-700`
    default:
      return `${baseClass} from-gray-500 to-gray-600 border-gray-700`
  }
}

const getTaskBorderClass = (priority) => {
  switch (priority) {
    case 'High': return 'border-red-500'
    case 'Medium': return 'border-blue-500'
    case 'Low': return 'border-green-500'
    default: return 'border-gray-500'
  }
}

const getPriorityIndicatorClass = (priority) => {
  switch (priority) {
    case 'High': return 'bg-red-300'
    case 'Medium': return 'bg-blue-300'
    case 'Low': return 'bg-green-300'
    default: return 'bg-gray-300'
  }
}

const getCapacityBarClass = (utilization) => {
  if (utilization >= 100) return 'bg-red-500'
  if (utilization >= 80) return 'bg-yellow-500'
  if (utilization >= 50) return 'bg-green-500'
  return 'bg-blue-500'
}

const getUtilizationTextClass = (utilization) => {
  if (utilization >= 100) return 'text-red-600 dark:text-red-400'
  if (utilization >= 80) return 'text-yellow-600 dark:text-yellow-400'
  if (utilization >= 50) return 'text-green-600 dark:text-green-400'
  return 'text-blue-600 dark:text-blue-400'
}

const getUtilizationLabelClass = (utilization) => {
  if (utilization >= 100) return 'text-red-600 dark:text-red-400'
  if (utilization >= 80) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
}

const getUtilizationLabel = (utilization) => {
  if (utilization >= 100) return 'Overloaded'
  if (utilization >= 80) return 'High'
  if (utilization >= 50) return 'Optimal'
  if (utilization > 0) return 'Low'
  return 'Available'
}

const getStatusIndicatorClass = (utilization) => {
  if (utilization >= 100) return 'bg-red-500'
  if (utilization >= 80) return 'bg-yellow-500'
  if (utilization >= 50) return 'bg-green-500'
  return 'bg-blue-500'
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

const handleDragOver = (event, assigneeId, dateKey) => {
  event.preventDefault()
  isDragOver.value = true
  dragOverAssignee.value = assigneeId
  dragOverDate.value = dateKey
}

const handleDragEnter = (event, assigneeId, dateKey) => {
  event.preventDefault()
  dragOverAssignee.value = assigneeId
  dragOverDate.value = dateKey
}

const handleDragLeave = () => {
  isDragOver.value = false
  dragOverAssignee.value = null
  dragOverDate.value = null
}

const handleDrop = (event, assigneeId, date) => {
  event.preventDefault()
  isDragOver.value = false
  dragOverAssignee.value = null
  dragOverDate.value = null
  
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

const startResize = (event, task, direction) => {
  // Implement resize functionality
  console.log('Start resize:', task.id, direction)
}
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.drop-zone-active {
  @apply bg-blue-100 dark:bg-blue-900/30 border-2 border-dashed border-blue-400;
}

.task-block:hover {
  transform: translateY(-1px);
  z-index: 10;
}

.resize-handle-left:hover,
.resize-handle-right:hover {
  @apply bg-white/50;
}
</style>
