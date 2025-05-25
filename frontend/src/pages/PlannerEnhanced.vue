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
                    <!-- Workload Timeline -->
                    <div class="flex-1">
                        <WorkloadViewEnhanced 
                            :assignees="assignees"
                            :tasks="tasks"
                            :loading="loading"
                            @taskClick="handleTaskClick"
                            @taskMove="handleTaskMove"
                            @taskUpdate="handleTaskUpdate"
                        />
                    </div>

                    <!-- Side Panel -->
                    <div class="w-full xl:w-80">
                        <TaskForm 
                            v-if="isTaskFormActive" 
                            :task="activeTask" 
                            :department="department.value"
                            @close="closeTaskDetails"
                        />
                        <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                            <!-- Tab Header -->
                            <div class="border-b border-gray-200 dark:border-gray-700">
                                <div class="flex">
                                    <button
                                        @click="activeTab = 'unscheduled'"
                                        :class="[
                                            'flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors duration-200',
                                            activeTab === 'unscheduled'
                                                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                                                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                                        ]"
                                    >
                                        <div class="flex items-center justify-center gap-2">
                                            <FeatherIcon name="clock" class="w-4 h-4" />
                                            <span>Unscheduled Tasks</span>
                                            <span class="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 px-2 py-0.5 rounded-full text-xs font-semibold">
                                                {{ unscheduledTasks.length }}
                                            </span>
                                        </div>
                                    </button>
                                    <button
                                        @click="activeTab = 'scheduled'"
                                        :class="[
                                            'flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors duration-200',
                                            activeTab === 'scheduled'
                                                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                                                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                                        ]"
                                    >
                                        <div class="flex items-center justify-center gap-2">
                                            <FeatherIcon name="calendar" class="w-4 h-4" />
                                            <span>Scheduled Tasks</span>
                                            <span class="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded-full text-xs font-semibold">
                                                {{ scheduledUnassignedTasks.length }}
                                            </span>
                                        </div>
                                    </button>
                                </div>
                            </div>

                            <!-- Tab Content -->
                            <div class="p-4">
                                <div class="space-y-2">
                                    <TextInput 
                                        v-model="searchText"
                                        placeholder="Search tasks..."
                                        size="sm"
                                    >
                                        <template #prefix>
                                            <FeatherIcon name="search" class="w-4 h-4 text-gray-400" />
                                        </template>
                                    </TextInput>
                                    
                                    <div class="max-h-[500px] overflow-y-auto">
                                        <!-- Task items -->
                                        <div 
                                            v-for="task in currentTasks" 
                                            :key="task.id"
                                            class="task-item p-3 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer rounded-lg mb-2 last:border-b-0"
                                            @click="handleTaskClick(task.id)"
                                        >
                                            <div class="flex items-start justify-between">
                                                <div class="flex-1">
                                                    <h4 class="font-medium text-gray-900 dark:text-white text-sm">{{ task.title }}</h4>
                                                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                        {{ task.duration }}h • {{ getAssigneeName(task.assignee) }}
                                                    </div>
                                                    <div v-if="task.project" class="mt-1 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded inline-block">
                                                        {{ task.project }}
                                                    </div>
                                                    <!-- Show dates for scheduled tasks -->
                                                    <div v-if="activeTab === 'scheduled' && task.startDate && task.endDate" class="mt-1 text-xs text-gray-600 dark:text-gray-400">
                                                        <FeatherIcon name="calendar" class="w-3 h-3 inline mr-1" />
                                                        {{ formatDate(task.startDate) }} - {{ formatDate(task.endDate) }}
                                                    </div>
                                                </div>
                                                <div class="text-xs rounded-full px-2 py-1" :class="getStatusClass(task.status)">
                                                    {{ task.status }}
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <!-- Empty state -->
                                        <div v-if="currentTasks.length === 0" class="py-8 text-center">
                                            <FeatherIcon 
                                                :name="activeTab === 'unscheduled' ? 'clock' : 'calendar'" 
                                                class="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" 
                                            />
                                            <p class="text-gray-500 dark:text-gray-400 text-sm">
                                                {{ activeTab === 'unscheduled' ? 'No unscheduled tasks found' : 'No scheduled unassigned tasks found' }}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
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
import WorkloadViewEnhanced from "@/components/Workload/WorkloadViewEnhanced.vue"
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
const searchText = ref("")
const activeTab = ref('unscheduled') // 'unscheduled' or 'scheduled'

// Computed
const unscheduledTasks = computed(() => {
    // Include all tasks that don't have both start and end dates
    return tasks.value.filter(task => !task.startDate || !task.endDate);
})

const scheduledUnassignedTasks = computed(() => {
    // Include tasks that have dates but are unassigned or assigned to 'unassigned' or 'Unassigned'
    return tasks.value.filter(task => 
        (task.startDate && task.endDate) && 
        (!task.assignee || task.assignee === 'unassigned' || task.assignee === 'Unassigned')
    );
})

const filteredUnscheduledTasks = computed(() => {
    if (!searchText.value) return unscheduledTasks.value;
    
    const search = searchText.value.toLowerCase();
    return unscheduledTasks.value.filter(task => 
        task.title.toLowerCase().includes(search) ||
        task.project?.toLowerCase().includes(search)
    );
})

const filteredScheduledTasks = computed(() => {
    if (!searchText.value) return scheduledUnassignedTasks.value;
    
    const search = searchText.value.toLowerCase();
    return scheduledUnassignedTasks.value.filter(task => 
        task.title.toLowerCase().includes(search) ||
        task.project?.toLowerCase().includes(search)
    );
})

const currentTasks = computed(() => {
    return activeTab.value === 'unscheduled' ? filteredUnscheduledTasks.value : filteredScheduledTasks.value;
})

const currentTasksCount = computed(() => {
    return activeTab.value === 'unscheduled' ? unscheduledTasks.value.length : scheduledUnassignedTasks.value.length;
})

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

const closeTaskDetails = () => {
    activeTask.value = null
    isTaskFormActive.value = false
}

const getAssigneeName = (assigneeId) => {
    if (!assigneeId || assigneeId === 'unassigned') {
        return 'Unassigned';
    }
    const assignee = assignees.value.find(a => a.id === assigneeId);
    return assignee ? assignee.name : 'Unassigned';
}

const getStatusClass = (status) => {
    switch (status) {
        case 'Completed': return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300';
        case 'Working': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300';
        case 'Overdue': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300';
        default: return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
}

const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
    });
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
