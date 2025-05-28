<template>
  <Layout :breadcrumbs="breadcrumbs">
    <div class="mx-auto px-4 lg:px-8 max-w-[2000px]">
      <!-- Enhanced Header -->
      <div class="planner-header mb-6 sticky top-0 z-50 bg-white dark:bg-gray-900 pb-4">
        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
          <!-- Title and Info -->
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <FeatherIcon name="calendar" class="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Team Planner</h1>
              <div class="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 mt-1">
                <div class="flex items-center gap-1">
                  <FeatherIcon name="users" class="w-4 h-4" />
                  <span>{{ department.value || 'All Departments' }}</span>
                </div>
                <span class="w-1 h-1 bg-gray-400 rounded-full"></span>
                <div class="flex items-center gap-1">
                  <FeatherIcon name="clock" class="w-4 h-4" />
                  <span>{{ formatCurrentPeriod() }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Stats Cards -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-4 border border-blue-200 dark:border-blue-700">
              <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ workloadStats.totalAssignees }}</div>
              <div class="text-xs text-blue-600/70 dark:text-blue-400/70 font-medium">Team Members</div>
            </div>
            
            <div class="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4 border border-green-200 dark:border-green-700">
              <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ workloadStats.scheduledTasks }}</div>
              <div class="text-xs text-green-600/70 dark:text-green-400/70 font-medium">Scheduled</div>
            </div>
            
            <div class="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-xl p-4 border border-yellow-200 dark:border-yellow-700">
              <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ workloadStats.unscheduledTasks }}</div>
              <div class="text-xs text-yellow-600/70 dark:text-yellow-400/70 font-medium">Backlog</div>
            </div>
            
            <div class="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-4 border border-purple-200 dark:border-purple-700">
              <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ Math.round(workloadStats.overallUtilization) }}%</div>
              <div class="text-xs text-purple-600/70 dark:text-purple-400/70 font-medium">Utilization</div>
            </div>
          </div>
        </div>

        <!-- Action Bar -->
        <div class="flex items-center justify-between mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-4">
            <!-- Department Filter -->
            <div class="flex items-center gap-2">
              <FeatherIcon name="filter" class="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <select 
                v-model="department.value"
                class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                @change="handleDepartmentChange"
              >
                <option value="">All Departments</option>
                <option v-for="dept in availableDepartments" :key="dept" :value="dept">
                  {{ dept }}
                </option>
              </select>
            </div>

            <!-- View Mode Toggle -->
            <div class="flex bg-white dark:bg-gray-700 rounded-lg p-1 border border-gray-200 dark:border-gray-600">
              <button
                @click="viewMode = 'week'"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200',
                  viewMode === 'week' 
                    ? 'bg-blue-500 text-white shadow-sm' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                ]"
              >
                Week
              </button>
              <button
                @click="viewMode = 'month'"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200',
                  viewMode === 'month' 
                    ? 'bg-blue-500 text-white shadow-sm' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                ]"
              >
                Month
              </button>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <!-- Refresh Button -->
            <Button 
              variant="ghost" 
              theme="gray" 
              size="sm" 
              :loading="loading"
              @click="refreshData"
            >
              <FeatherIcon name="refresh-cw" class="w-4 h-4" />
            </Button>

            <!-- Add Task Button -->
            <Button 
              variant="solid" 
              theme="blue" 
              size="sm"
              @click="handleAddTask"
            >
              <FeatherIcon name="plus" class="w-4 h-4 mr-2" />
              Add Task
            </Button>
          </div>
        </div>
      </div>

      <!-- Main Timeline View -->
      <div class="timeline-container">
        <TimelineViewRoster 
          :assignees="assignees"
          :tasks="tasks"
          :loading="loading"
          @taskClick="handleTaskClick"
          @taskMove="handleTaskMove"
          @addTask="handleAddTask"
        />
      </div>

      <!-- Task Details Modal/Sidebar -->
      <div 
        v-if="isTaskFormActive" 
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="closeTaskDetails"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl max-h-[90vh] overflow-hidden">
          <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              {{ activeTask ? 'Edit Task' : 'Create Task' }}
            </h2>
            <Button variant="ghost" theme="gray" size="sm" @click="closeTaskDetails">
              <FeatherIcon name="x" class="w-5 h-5" />
            </Button>
          </div>
          
          <div class="p-6 overflow-y-auto">
            <TaskForm 
              :task="activeTask" 
              :department="department.value"
              :assignees="assignees"
              @close="closeTaskDetails"
              @update="handleTaskUpdate"
              @create="handleTaskCreate"
            />
          </div>
        </div>
      </div>

      <!-- Loading Overlay -->
      <div v-if="loading" class="fixed inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm flex items-center justify-center z-40">
        <div class="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl border border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3">
            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-gray-900 dark:text-white font-medium">Loading timeline...</span>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import Layout from "@/pages/shared/Layout.vue"
import { ref, computed, onMounted, watch } from "vue"
import { useRoute } from 'vue-router'
import { Button, FeatherIcon } from 'frappe-ui'
import TimelineViewRoster from "@/components/Timeline/TimelineViewRoster.vue"
import TaskForm from "@/components/Task/TaskForm.vue"
import { useWorkloadManager } from "@/composables/useWorkloadManager"

const route = useRoute()

// Reactive state
const department = ref(route.params.department || '')
const dashboardName = ref(route.params.dashboardName || 'Team Planner')
const viewMode = ref('week')
const isTaskFormActive = ref(false)
const activeTask = ref(null)

// Breadcrumbs
const breadcrumbs = computed(() => [
  {
    label: 'Dashboard',
    route: { name: 'Dashboard' }
  },
  {
    label: dashboardName.value,
    route: { name: 'PlannerRoster' }
  }
])

// Initialize workload manager
const {
  assignees,
  tasks,
  loading,
  workloadStats,
  overallocatedAssignees,
  underutilizedAssignees,
  loadWorkloadData,
  moveTask,
  updateTask,
  createTask
} = useWorkloadManager(department.value)

// Computed properties
const availableDepartments = computed(() => {
  const departments = new Set()
  assignees.value.forEach(assignee => {
    if (assignee.department) {
      departments.add(assignee.department)
    }
  })
  return Array.from(departments).sort()
})

// Methods
const refreshData = async () => {
  await loadWorkloadData(null, null, true)
}

const handleDepartmentChange = () => {
  loadWorkloadData(null, null, true)
}

const handleTaskClick = (taskId) => {
  const task = tasks.value.find(t => t.id === taskId)
  activeTask.value = task || null
  isTaskFormActive.value = true
}

const handleTaskMove = async (data) => {
  try {
    await moveTask(data.taskId, data.assigneeId, data.startDate, data.endDate)
  } catch (error) {
    console.error('Error moving task:', error)
  }
}

const handleTaskUpdate = async (data) => {
  try {
    await updateTask(data.taskId, data.updates)
    closeTaskDetails()
  } catch (error) {
    console.error('Error updating task:', error)
  }
}

const handleTaskCreate = async (taskData) => {
  try {
    await createTask(taskData)
    closeTaskDetails()
  } catch (error) {
    console.error('Error creating task:', error)
  }
}

const handleAddTask = (data = {}) => {
  activeTask.value = null // New task
  isTaskFormActive.value = true
}

const closeTaskDetails = () => {
  activeTask.value = null
  isTaskFormActive.value = false
}

const formatCurrentPeriod = () => {
  const now = new Date()
  if (viewMode.value === 'week') {
    const startOfWeek = new Date(now)
    const day = startOfWeek.getDay()
    const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1)
    startOfWeek.setDate(diff)
    
    const endOfWeek = new Date(startOfWeek)
    endOfWeek.setDate(startOfWeek.getDate() + 6)
    
    return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  } else {
    return now.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
  }
}

// Watch for route changes
watch(() => route.params.department, (newDepartment) => {
  if (newDepartment !== department.value) {
    department.value = newDepartment || ''
    loadWorkloadData(null, null, true)
  }
}, { immediate: true })

// Initialize
onMounted(() => {
  loadWorkloadData()
})
</script>

<style scoped>
.planner-header {
  transition: all 0.3s ease;
}

.timeline-container {
  min-height: 600px;
}

/* Custom scrollbar for modal */
.overflow-y-auto::-webkit-scrollbar {
  @apply w-2;
}

.overflow-y-auto::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-700;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600 rounded;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}

/* Smooth transitions */
* {
  transition: all 0.2s ease;
}

/* Modal animation */
.fixed.inset-0 {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.bg-white.dark\:bg-gray-800.rounded-2xl {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to { 
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
