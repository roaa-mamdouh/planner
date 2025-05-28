<template>
    <Layout :breadcrumbs="breadcrumbs">
        <div class="mx-auto px-4 lg:px-8 max-w-[2000px]">
            <!-- Enhanced Header with Workload Stats -->
            <div class="workload-header mb-6 sticky top-0 z-50 bg-white dark:bg-gray-900 pb-4" ref="headerRef">
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                    <!-- Title and Department -->
                    <div class="flex items-center gap-4">
                        <div>
                            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Workload Planner</h1>
                            <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                <FeatherIcon name="users" class="w-4 h-4" />
                                <span>{{ department.value }}</span>
                                <span class="mx-2">•</span>
                                <span>{{ workloadStats.totalAssignees }} team members</span>
                            </div>
                        </div>
                    </div>

                    <!-- Quick Stats -->
                    <div class="flex items-center gap-6">
                        <div class="stats-grid grid grid-cols-2 lg:grid-cols-4 gap-4">
                            <div class="stat-item text-center">
                                <div class="text-lg font-semibold text-blue-600 dark:text-blue-400">{{ workloadStats.scheduledTasks }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">Scheduled</div>
                            </div>
                            <div class="stat-item text-center">
                                <div class="text-lg font-semibold text-yellow-600 dark:text-yellow-400">{{ workloadStats.unscheduledTasks }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">Unscheduled</div>
                            </div>
                            <div class="stat-item text-center">
                                <div class="text-lg font-semibold text-green-600 dark:text-green-400">{{ workloadStats.overallUtilization }}%</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">Utilization</div>
                            </div>
                            <div class="stat-item text-center">
                                <div class="text-lg font-semibold" :class="overallocatedAssignees.length > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-400'">
                                    {{ overallocatedAssignees.length }}
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">Overloaded</div>
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="flex items-center gap-2">
                            <Button 
                                :variant="'ghost'" 
                                theme="gray" 
                                size="sm" 
                                :loading="loading"
                                @click="refreshWorkloadData"
                            >
                                <FeatherIcon name="refresh-cw" class="w-4 h-4" />
                            </Button>
                            
                            <Button 
                                :variant="'ghost'" 
                                theme="gray" 
                                size="sm"
                                @click="showCapacityAnalysis = !showCapacityAnalysis"
                            >
                                <FeatherIcon name="bar-chart-2" class="w-4 h-4 mr-2" />
                                Analytics
                            </Button>
                        </div>
                    </div>
                </div>

                <!-- Main Workload View -->
                <div class="flex flex-col xl:flex-row gap-6 mt-6">
                    <!-- Timeline View -->
                    <div class="flex-1">
                        <TimelineViewRoster 
                            :assignees="assignees"
                            :tasks="tasks"
                            :loading="loading"
                            @taskClick="handleTaskClick"
                            @taskMove="handleTaskMove"
                            @taskUpdate="handleTaskUpdate"
                            @addTask="handleAddTask"
                        />
                    </div>

                    <!-- Task Details Panel -->
                    <div v-if="isTaskFormActive" class="w-full xl:w-96">
                        <TaskForm 
                            :task="activeTask" 
                            :department="department.value"
                            :assignees="assignees"
                            @close="closeTaskDetails"
                            @update="handleTaskUpdate"
                            class="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6"
                        />
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
import { Button, TextInput } from 'frappe-ui'
import TimelineViewRoster from "@/components/Timeline/TimelineViewRoster.vue"
import TaskForm from "@/components/Task/TaskForm.vue"
import { useWorkloadManager } from "@/composables/useWorkloadManager"

const route = useRoute()

const department = ref(route.params.department)
const dashboardName = ref(route.params.dashboardName)

// Breadcrumbs
const breadcrumbs = [
    {
        label: 'Dashboard',
        route: { name: 'Dashboard' }
    },
    {
        label: dashboardName.value,
        route: { name: 'PlannerEnhanced' }
    }
]

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
    calculateUtilization
} = useWorkloadManager(department.value)

// Watch for department changes
watch(() => route.params.department, (newDepartment) => {
    if (newDepartment) {
        department.value = newDepartment
        loadWorkloadData(null, null, true)
    }
}, { immediate: true })

// UI State
const showCapacityAnalysis = ref(false)
const isTaskFormActive = ref(false)
const activeTask = ref(null)

// Methods
const refreshWorkloadData = async () => {
    await loadWorkloadData(null, null, true)
}

const handleTaskClick = (taskId) => {
    activeTask.value = taskId
    isTaskFormActive.value = true
}

const handleTaskMove = async (data) => {
    await moveTask(data.taskId, data.assigneeId, data.startDate, data.endDate)
}

const handleTaskUpdate = async (data) => {
    await updateTask(data.taskId, data.updates)
}

const handleAddTask = (data) => {
    // Handle adding new task - could open task form or emit event
    activeTask.value = null // New task
    isTaskFormActive.value = true
}

const closeTaskDetails = () => {
    activeTask.value = null
    isTaskFormActive.value = false
}

// Initialize
onMounted(() => {
    loadWorkloadData()
})
</script>

<style scoped>
.workload-header {
    transition: all 0.3s ease;
}

.workload-header.scrolled {
    @apply shadow-sm border-b border-gray-200 dark:border-gray-700;
    padding-bottom: 1rem;
}

.task-item {
    transition: all 0.2s ease;
}

.task-item:hover {
    transform: translateX(4px);
}
</style>
