<template>
  <div class="backlog-panel bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 flex flex-col h-full">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
            <FeatherIcon name="inbox" class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Backlog</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ tasks.length }} unscheduled tasks</p>
          </div>
        </div>
        <Button
          variant="ghost"
          theme="gray"
          size="sm"
          @click="$emit('close')"
        >
          <FeatherIcon name="x" class="w-4 h-4" />
        </Button>
      </div>

      <!-- Search and Filters -->
      <div class="space-y-3">
        <div class="relative">
          <FeatherIcon name="search" class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search tasks..."
            class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div class="flex gap-2">
          <select
            v-model="selectedPriority"
            class="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Priorities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          <select
            v-model="selectedProject"
            class="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Projects</option>
            <option v-for="project in uniqueProjects" :key="project" :value="project">
              {{ project }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Task List -->
    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="animate-pulse">
          <div class="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
        </div>
      </div>

      <div v-else-if="filteredTasks.length === 0" class="text-center py-12">
        <div class="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <FeatherIcon name="check-circle" class="w-8 h-8 text-gray-400 dark:text-gray-500" />
        </div>
        <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">All caught up!</h4>
        <p class="text-gray-500 dark:text-gray-400">No unscheduled tasks found.</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-card group cursor-move bg-gradient-to-r from-white to-gray-50 dark:from-gray-700 dark:to-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4 hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
          :class="getTaskBorderClass(task.priority)"
          draggable="true"
          @dragstart="handleDragStart($event, task)"
          @click="$emit('taskClick', task.id)"
        >
          <!-- Task Header -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex-1 min-w-0">
              <h4 class="font-semibold text-gray-900 dark:text-white text-sm truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {{ task.title }}
              </h4>
              <p v-if="task.project" class="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                {{ task.project }}
              </p>
            </div>
            <div class="flex items-center gap-2 ml-3">
              <span
                class="px-2 py-1 text-xs font-medium rounded-full"
                :class="getPriorityBadgeClass(task.priority)"
              >
                {{ task.priority }}
              </span>
            </div>
          </div>

          <!-- Task Details -->
          <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-1">
                <FeatherIcon name="clock" class="w-3 h-3" />
                <span>{{ task.duration }}h</span>
              </div>
              <div v-if="task.assignee && task.assignee !== 'unassigned'" class="flex items-center gap-1">
                <FeatherIcon name="user" class="w-3 h-3" />
                <span>{{ getAssigneeName(task.assignee) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <FeatherIcon name="calendar" class="w-3 h-3" />
              <span>{{ formatCreatedDate(task.created) }}</span>
            </div>
          </div>

          <!-- Task Description -->
          <div v-if="task.description" class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-600">
            <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
              {{ task.description }}
            </p>
          </div>

          <!-- Drag Indicator -->
          <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <FeatherIcon name="move" class="w-4 h-4 text-gray-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        variant="solid"
        theme="blue"
        size="sm"
        class="w-full"
        @click="$emit('addTask')"
      >
        <FeatherIcon name="plus" class="w-4 h-4 mr-2" />
        Add New Task
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  tasks: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  assignees: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['taskDragStart', 'taskClick', 'addTask', 'close'])

// Filter state
const searchQuery = ref('')
const selectedPriority = ref('')
const selectedProject = ref('')

// Computed properties
const uniqueProjects = computed(() => {
  const projects = props.tasks
    .map(task => task.project)
    .filter(project => project && project.trim() !== '')
  return [...new Set(projects)].sort()
})

const filteredTasks = computed(() => {
  let filtered = props.tasks

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(task =>
      task.title.toLowerCase().includes(query) ||
      (task.project && task.project.toLowerCase().includes(query)) ||
      (task.description && task.description.toLowerCase().includes(query))
    )
  }

  // Priority filter
  if (selectedPriority.value) {
    filtered = filtered.filter(task => task.priority === selectedPriority.value)
  }

  // Project filter
  if (selectedProject.value) {
    filtered = filtered.filter(task => task.project === selectedProject.value)
  }

  // Sort by priority and creation date
  return filtered.sort((a, b) => {
    const priorityOrder = { 'High': 3, 'Medium': 2, 'Low': 1 }
    const aPriority = priorityOrder[a.priority] || 0
    const bPriority = priorityOrder[b.priority] || 0
    
    if (aPriority !== bPriority) {
      return bPriority - aPriority // High priority first
    }
    
    return new Date(b.created) - new Date(a.created) // Newer first
  })
})

// Methods
const handleDragStart = (event, task) => {
  event.dataTransfer.setData('application/json', JSON.stringify(task))
  event.dataTransfer.effectAllowed = 'move'
  emit('taskDragStart', event, task)
}

const getTaskBorderClass = (priority) => {
  switch (priority) {
    case 'High':
      return 'border-l-4 border-l-red-500 hover:border-l-red-600'
    case 'Medium':
      return 'border-l-4 border-l-blue-500 hover:border-l-blue-600'
    case 'Low':
      return 'border-l-4 border-l-green-500 hover:border-l-green-600'
    default:
      return 'border-l-4 border-l-gray-500 hover:border-l-gray-600'
  }
}

const getPriorityBadgeClass = (priority) => {
  switch (priority) {
    case 'High':
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
    case 'Medium':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
    case 'Low':
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300'
  }
}

const getAssigneeName = (assigneeId) => {
  const assignee = props.assignees.find(a => a.id === assigneeId)
  return assignee ? assignee.name : assigneeId
}

const formatCreatedDate = (dateStr) => {
  if (!dateStr) return ''
  
  const date = new Date(dateStr)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 1) return 'Today'
  if (diffDays === 2) return 'Yesterday'
  if (diffDays <= 7) return `${diffDays} days ago`
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.backlog-panel {
  max-height: 70vh;
}

.task-card {
  position: relative;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Custom scrollbar */
.backlog-panel ::-webkit-scrollbar {
  @apply w-2;
}

.backlog-panel ::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-700;
}

.backlog-panel ::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600 rounded;
}

.backlog-panel ::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}
</style>
