<template>
  <div class="timeline-roster-view">
    <!-- Header Controls -->
    <div class="timeline-header mb-6 p-6 bg-gradient-to-r from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
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
            <FeatherIcon name="users" class="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ assignees.length }} team members</span>
          </div>

          <Button 
            variant="ghost" 
            theme="gray" 
            size="sm"
            @click="showBacklog = !showBacklog"
            :class="showBacklog ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400' : ''"
          >
            <FeatherIcon name="inbox" class="w-4 h-4 mr-2" />
            Backlog ({{ unscheduledTasks.length }})
          </Button>
        </div>
      </div>
    </div>

    <!-- Main Timeline Grid -->
    <div class="flex gap-6">
      <!-- Timeline Table -->
      <div class="flex-1">
        <div 
          class="rounded-xl border overflow-auto shadow-lg bg-white dark:bg-gray-800"
          :class="loading && 'animate-pulse pointer-events-none'"
          style="max-height: 70vh;"
        >
          <table class="border-separate border-spacing-0 w-full">
            <thead>
              <tr class="sticky top-0 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800 z-20">
                <!-- Assignee Search Column -->
                <th class="p-4 border-b border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800">
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
                </th>

                <!-- Date Columns -->
                <th
                  v-for="(date, idx) in dateColumns"
                  :key="date.key"
                  class="font-medium border-b border-gray-200 dark:border-gray-600 p-3 text-center min-w-[140px]"
                  :class="{ 
                    'border-l border-gray-200 dark:border-gray-600': idx > 0,
                    'bg-blue-50 dark:bg-blue-900/20': date.isToday 
                  }"
                >
                  <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ date.label }}</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ date.sublabel }}</div>
                  <div v-if="date.isToday" class="w-2 h-2 bg-blue-500 rounded-full mx-auto mt-1"></div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(assignee, rowIdx) in filteredAssignees" 
                :key="assignee.id"
                class="border-b border-gray-100 dark:border-gray-700 last:border-b-0 hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-all duration-200"
              >
                <!-- Assignee Info Column -->
                <td 
                  class="p-4 border-r border-gray-200 dark:border-gray-600 bg-gradient-to-r from-gray-50/50 to-transparent dark:from-gray-800/50"
                  :class="{ 'border-t border-gray-200 dark:border-gray-600': rowIdx > 0 }"
                >
                  <div class="flex items-center justify-between h-full min-h-[100px]">
                    <div class="flex items-center gap-4">
                      <div class="relative">
                        <Avatar 
                          :image="assignee.image" 
                          :label="assignee.name"
                          size="md"
                          class="ring-2 ring-white dark:ring-gray-700 shadow-sm"
                        />
                        <div 
                          class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white dark:border-gray-800" 
                          :class="getStatusIndicatorClass(assignee.utilization)"
                        ></div>
                      </div>
                      <div>
                        <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ assignee.name }}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ assignee.role || 'Team Member' }}</div>
                        <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {{ getAssigneeScheduledHours(assignee.id) }}h / {{ assignee.capacity || 40 }}h
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
                </td>

                <!-- Date Cells -->
                <td
                  v-for="(date, colIdx) in dateColumns"
                  :key="`${assignee.id}-${date.key}`"
                  class="p-2 relative min-h-[100px] align-top"
                  :class="{
                    'border-l border-gray-200 dark:border-gray-600': colIdx > 0,
                    'border-t border-gray-200 dark:border-gray-600': rowIdx > 0,
                    'bg-blue-50/50 dark:bg-blue-900/10': date.isToday,
                    'hover:bg-gray-50 dark:hover:bg-gray-700/20': !date.isToday,
                    'drop-zone-active': isDragOver && dragOverDate === date.key && dragOverAssignee === assignee.id
                  }"
                  @drop="handleDrop($event, assignee.id, date.date)"
                  @dragover.prevent="handleDragOver($event, assignee.id, date.key)"
                  @dragenter.prevent="handleDragEnter($event, assignee.id, date.key)"
                  @dragleave="handleDragLeave"
                  @mouseenter="handleCellMouseEnter(assignee.id, date.key)"
                  @mouseleave="handleCellMouseLeave"
                >
                  <!-- Today Indicator -->
                  <div v-if="date.isToday" class="absolute left-1/2 top-0 w-0.5 h-full bg-blue-500 transform -translate-x-1/2 opacity-30"></div>
                  
                  <!-- Task Blocks -->
                  <div class="space-y-2">
                    <div
                      v-for="task in getTasksForDateAndAssignee(assignee.id, date.date)"
                      :key="task.id"
                      class="task-block cursor-move group rounded-lg shadow-sm hover:shadow-md transition-all duration-200 p-3"
                      :class="getTaskBlockClass(task)"
                      @click="$emit('taskClick', task.id)"
                      draggable="true"
                      @dragstart="handleDragStart($event, task)"
                    >
                      <div class="text-xs text-white">
                        <div class="font-semibold truncate mb-1">{{ task.title }}</div>
                        <div class="text-white/80 truncate text-xs mb-2">{{ task.project }}</div>
                        <div class="flex items-center justify-between">
                          <div class="text-white/70 text-xs">{{ task.duration }}h</div>
                          <div 
                            class="w-1.5 h-1.5 rounded-full" 
                            :class="getPriorityIndicatorClass(task.priority)"
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Add Task Button -->
                  <Button
                    v-if="hoveredCell.assignee === assignee.id && hoveredCell.date === date.key"
                    variant="outline"
                    icon="plus"
                    size="sm"
                    class="border-2 border-dashed border-gray-300 dark:border-gray-600 w-full mt-2 text-gray-500 dark:text-gray-400 hover:border-blue-400 hover:text-blue-600"
                    @click="$emit('addTask', { assigneeId: assignee.id, date: date.date })"
                  >
                    Add Task
                  </Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Backlog Panel -->
      <BacklogPanel
        v-if="showBacklog"
        :tasks="unscheduledTasks"
        :loading="loading"
        @taskDragStart="handleDragStart"
        @taskClick="$emit('taskClick', $event)"
        @addTask="$emit('addTask', $event)"
        class="w-80 flex-shrink-0"
      />
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl">
        <div class="flex items-center gap-3">
          <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-gray-900 dark:text-white font-medium">Loading timeline...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Avatar, Button, FeatherIcon } from 'frappe-ui'
import BacklogPanel from './BacklogPanel.vue'

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

const emit = defineEmits(['taskClick', 'taskMove', 'addTask'])

// View state
const currentViewMode = ref('week')
const currentDate = ref(new Date())
const showBacklog = ref(true)
const assigneeSearch = ref('')

// Drag and drop state
const isDragOver = ref(false)
const dragOverAssignee = ref(null)
const dragOverDate = ref(null)
const hoveredCell = ref({ assignee: '', date: '' })

// Constants
const viewModes = [
  { label: 'Week', value: 'week', icon: 'calendar' },
  { label: 'Month', value: 'month', icon: 'calendar' }
]

// Computed properties
const dateColumns = computed(() => {
  const columns = []
  const today = new Date()
  const startDate = getWeekStart(currentDate.value)
  
  const daysToShow = currentViewMode.value === 'week' ? 7 : 30
  
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

const filteredAssignees = computed(() => {
  if (!assigneeSearch.value) return props.assignees
  
  return props.assignees.filter(assignee => 
    assignee.name.toLowerCase().includes(assigneeSearch.value.toLowerCase())
  )
})

const unscheduledTasks = computed(() => {
  return props.tasks.filter(task => !task.isScheduled)
})

// Methods
const getWeekStart = (date) => {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1) // Adjust when day is Sunday
  return new Date(d.setDate(diff))
}

const navigateDate = (direction) => {
  const newDate = new Date(currentDate.value)
  const daysToMove = currentViewMode.value === 'week' ? 7 : 30
  
  newDate.setDate(newDate.getDate() + (direction * daysToMove))
  currentDate.value = newDate
}

const goToToday = () => {
  currentDate.value = new Date()
}

const formatDateRange = () => {
  if (currentViewMode.value === 'week') {
    const start = getWeekStart(currentDate.value)
    const end = new Date(start)
    end.setDate(start.getDate() + 6)
    return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  } else {
    return currentDate.value.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
  }
}

const getTasksForDateAndAssignee = (assigneeId, date) => {
  const dateStr = date.toISOString().split('T')[0]
  
  return props.tasks.filter(task => {
    if (!task.isScheduled || task.assignee !== assigneeId) return false
    
    const taskStart = new Date(task.startDate).toISOString().split('T')[0]
    const taskEnd = new Date(task.endDate).toISOString().split('T')[0]
    
    return dateStr >= taskStart && dateStr <= taskEnd
  })
}

const getAssigneeScheduledHours = (assigneeId) => {
  const assigneeTasks = props.tasks.filter(t => t.assignee === assigneeId && t.isScheduled)
  return assigneeTasks.reduce((sum, t) => sum + (t.duration || 0), 0)
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
  
  // Calculate end date based on task duration
  const startDate = new Date(date)
  const endDate = new Date(startDate)
  const durationDays = Math.max(1, Math.ceil((taskData.duration || 8) / 8))
  endDate.setDate(startDate.getDate() + durationDays - 1)
  
  emit('taskMove', {
    taskId: taskData.id,
    assigneeId,
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0]
  })
}

// Mouse events for hover states
const handleCellMouseEnter = (assigneeId, dateKey) => {
  hoveredCell.value = { assignee: assigneeId, date: dateKey }
}

const handleCellMouseLeave = () => {
  hoveredCell.value = { assignee: '', date: '' }
}

// Watch for prop changes
watch(() => props.assignees, () => {
  // Recalculate utilizations when assignees change
}, { deep: true })

onMounted(() => {
  // Initialize component
})
</script>

<style scoped>
.timeline-roster-view {
  @apply w-full;
}

.drop-zone-active {
  @apply bg-blue-100 dark:bg-blue-900/30 border-2 border-dashed border-blue-400;
}

.task-block:hover {
  transform: translateY(-1px);
  z-index: 10;
}

/* Table styling */
th,
td {
  font-size: 0.875rem;
}

th:first-child,
td:first-child {
  @apply sticky left-0 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-600;
  min-width: 280px;
  max-width: 280px;
}

/* Scrollbar styling */
.timeline-roster-view ::-webkit-scrollbar {
  @apply w-2 h-2;
}

.timeline-roster-view ::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-700;
}

.timeline-roster-view ::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600 rounded;
}

.timeline-roster-view ::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}
</style>
