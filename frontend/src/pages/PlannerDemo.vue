<template>
    <Layout :breadcrumbs="breadcrumbs">
        <div class="mx-auto px-4 lg:px-8 max-w-[1800px]">
            <!-- Demo Header -->
            <div class="mb-8 text-center">
                <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    Enhanced Planner Demo
                </h1>
                <p class="text-gray-600 dark:text-gray-400">
                    Showcasing the creative and appealing improvements to the workload view
                </p>
            </div>

            <!-- Enhanced Navigation Controls -->
            <div class="enhanced-nav-controls flex justify-between items-center mb-6 sticky top-0 z-50" ref="timelineInfoRef">
                <div class="flex items-center gap-3">
                    <Button 
                        :variant="'solid'" 
                        theme="gray" 
                        size="md" 
                        @click="navigateWeek(-1)"
                        class="hover:scale-105 transition-transform duration-200"
                    >
                        <FeatherIcon name="chevron-left" class="w-4 h-4 mr-1" />
                        Previous
                    </Button>
                    
                    <div class="week-indicator">
                        <FeatherIcon name="calendar" class="w-4 h-4 inline mr-2" />
                        Week {{ weekNumber }}
                    </div>
                    
                    <Button 
                        :variant="'solid'" 
                        theme="gray" 
                        size="md" 
                        @click="navigateWeek(1)"
                        class="hover:scale-105 transition-transform duration-200"
                    >
                        Next
                        <FeatherIcon name="chevron-right" class="w-4 h-4 ml-1" />
                    </Button>
                </div>
                
                <div class="flex items-center gap-3">
                    <Button 
                        :variant="'ghost'" 
                        theme="gray" 
                        size="md" 
                        :loading="isRefreshing"
                        @click="refreshData"
                        class="hover:scale-105 transition-transform duration-200"
                    >
                        <FeatherIcon name="refresh-cw" class="w-4 h-4" />
                    </Button>
                    
                    <div class="department-badge">
                        <FeatherIcon name="users" class="w-4 h-4 inline mr-2" />
                        {{ department }}
                    </div>
                    
                    <!-- View Mode Toggle -->
                    <div class="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                        <button 
                            @click="viewMode = 'week'"
                            :class="['px-3 py-1 rounded text-sm font-medium transition-all duration-200', 
                                    viewMode === 'week' ? 'bg-white dark:bg-gray-600 shadow-sm text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white']"
                        >
                            Week
                        </button>
                        <button 
                            @click="viewMode = 'month'"
                            :class="['px-3 py-1 rounded text-sm font-medium transition-all duration-200', 
                                    viewMode === 'month' ? 'bg-white dark:bg-gray-600 shadow-sm text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white']"
                        >
                            Month
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="flex flex-col lg:flex-row justify-between items-start gap-6">
                <!-- Enhanced Timeline Container -->
                <div class="w-full lg:w-9/12">
                    <div class="enhanced-timeline-container p-4 fade-in">
                        <!-- Timeline Stats Bar -->
                        <div class="flex items-center justify-between mb-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-100 dark:border-blue-800/30">
                            <div class="flex items-center gap-4">
                                <div class="flex items-center gap-2">
                                    <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ demoStats.completed }} Completed</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ demoStats.inProgress }} In Progress</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ demoStats.overdue }} Overdue</span>
                                </div>
                            </div>
                            <div class="text-sm font-medium text-gray-600 dark:text-gray-400">
                                Total: {{ demoStats.total }} tasks
                            </div>
                        </div>

                        <!-- Demo Timeline Visualization -->
                        <div class="min-h-[500px] bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                            <div class="text-center py-20">
                                <FeatherIcon name="calendar" class="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Enhanced Timeline View</h3>
                                <p class="text-gray-600 dark:text-gray-400 mb-4">
                                    This would show the enhanced timeline with improved styling, animations, and visual hierarchy
                                </p>
                                <div class="flex justify-center gap-2">
                                    <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                                    <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                                    <div class="w-3 h-3 bg-purple-500 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Enhanced Backlog Section -->
                <div class="w-full lg:w-3/12 sticky top-20">
                    <div class="enhanced-backlog-container slide-up">
                        <template v-if="!isTaskFormActive">
                            <!-- Enhanced Search Section -->
                            <div class="enhanced-search-container">
                                <div class="space-y-3">
                                    <div class="relative">
                                        <TextInput 
                                            type="text" 
                                            placeholder="Search tasks..." 
                                            v-model="searchText" 
                                            class="pl-10 pr-4 py-2 w-full rounded-lg border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        >
                                            <template #prefix>
                                                <FeatherIcon name="search" class="w-4 h-4 text-gray-400" />
                                            </template>
                                        </TextInput>
                                    </div>
                                    
                                    <div class="relative">
                                        <TextInput 
                                            type="text" 
                                            placeholder="Filter by project..." 
                                            v-model="projectText" 
                                            class="pl-10 pr-4 py-2 w-full rounded-lg border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        >
                                            <template #prefix>
                                                <FeatherIcon name="folder" class="w-4 h-4 text-gray-400" />
                                            </template>
                                        </TextInput>
                                    </div>
                                </div>
                            </div>

                            <!-- Backlog Header -->
                            <div class="backlog-header flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <FeatherIcon name="inbox" class="w-5 h-5" />
                                    <span>Backlog</span>
                                </div>
                                <div class="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full text-xs font-semibold">
                                    {{ demoTasks.length }}
                                </div>
                            </div>

                            <!-- Enhanced Task Cards -->
                            <div class="p-4 space-y-3 max-h-[600px] overflow-y-auto">
                                <div 
                                    v-for="(task, index) in filteredTasks" 
                                    :key="task.id"
                                    class="enhanced-task-card"
                                    :style="{ '--task-accent-color': task.color, animationDelay: `${index * 50}ms` }"
                                    @click="openTaskDetail(task)" 
                                    draggable="true"
                                    tabindex="0"
                                    @keydown.enter="openTaskDetail(task)"
                                >
                                    <div class="space-y-3">
                                        <!-- Task Header -->
                                        <div class="flex items-start justify-between">
                                            <div class="flex-1 min-w-0">
                                                <div class="flex items-center gap-2 mb-1">
                                                    <span v-if="task.project" class="task-project-tag">
                                                        {{ task.project }}
                                                    </span>
                                                    <span :class="['task-priority-badge', `priority-${task.priority.toLowerCase()}`]">
                                                        {{ task.priority }}
                                                    </span>
                                                </div>
                                                <h4 class="font-semibold text-gray-900 dark:text-white text-sm leading-tight mb-1">
                                                    {{ task.title }}
                                                </h4>
                                                <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                                                    {{ task.description }}
                                                </p>
                                            </div>
                                            <FeatherIcon name="more-vertical" class="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-pointer" />
                                        </div>

                                        <!-- Task Footer -->
                                        <div class="flex items-center justify-between">
                                            <div class="flex items-center gap-2">
                                                <div class="task-time-estimate">
                                                    <FeatherIcon name="clock" class="w-3 h-3" />
                                                    {{ task.estimatedTime }}h
                                                </div>
                                            </div>
                                            <div class="text-right">
                                                <p class="text-xs font-medium text-gray-900 dark:text-white">
                                                    {{ formatDateDisplay(task.dueDate) }}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>
                        
                        <template v-else>
                            <!-- Enhanced Task Detail Header -->
                            <div class="backlog-header flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <FeatherIcon name="file-text" class="w-5 h-5" />
                                    <span>Task Details</span>
                                </div>
                                <Button 
                                    :variant="'ghost'" 
                                    theme="gray" 
                                    size="sm" 
                                    @click="backToBackLog"
                                    class="hover:scale-105 transition-transform duration-200"
                                >
                                    <FeatherIcon name="arrow-left" class="w-4 h-4 mr-1" />
                                    Back
                                </Button>
                            </div>
                            
                            <div class="p-4">
                                <!-- Task Detail View -->
                                <div class="space-y-4">
                                    <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/30">
                                        <h3 class="font-semibold text-gray-900 dark:text-white mb-2">{{ selectedTask?.title }}</h3>
                                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">{{ selectedTask?.description }}</p>
                                        
                                        <div class="flex items-center gap-4 text-xs">
                                            <span class="flex items-center gap-1">
                                                <FeatherIcon name="clock" class="w-3 h-3" />
                                                {{ selectedTask?.estimatedTime }}h
                                            </span>
                                            <span class="flex items-center gap-1">
                                                <FeatherIcon name="calendar" class="w-3 h-3" />
                                                {{ formatDateDisplay(selectedTask?.dueDate) }}
                                            </span>
                                            <span :class="['task-priority-badge', `priority-${selectedTask?.priority.toLowerCase()}`]">
                                                {{ selectedTask?.priority }}
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <div class="text-center py-8">
                                        <FeatherIcon name="edit-3" class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                                        <p class="text-gray-500 dark:text-gray-400 text-sm">Enhanced task form would appear here</p>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </div>
    </Layout>
</template>

<script setup>
import Layout from "@/pages/shared/Layout.vue";
import { computed, ref, onMounted } from "vue";

// Demo data and state
const searchText = ref('')
const projectText = ref('')
const viewMode = ref('week')
const isRefreshing = ref(false)
const isTaskFormActive = ref(false)
const selectedTask = ref(null)
const weekNumber = ref(42)
const department = ref('Engineering')

const breadcrumbs = [
    {
        label: 'Dashboard',
        route: { name: 'Dashboard' },
    },
    {
        label: 'Enhanced Planner Demo',
        route: { name: 'PlannerDemo' }
    },
];

// Demo statistics
const demoStats = ref({
    completed: 12,
    inProgress: 8,
    overdue: 3,
    total: 23
})

// Demo tasks
const demoTasks = ref([
    {
        id: 1,
        title: 'Implement user authentication',
        description: 'Add JWT-based authentication system with role-based access control',
        project: 'WebApp',
        priority: 'High',
        estimatedTime: 8,
        dueDate: '2024-01-15',
        color: '#ef4444'
    },
    {
        id: 2,
        title: 'Design dashboard mockups',
        description: 'Create wireframes and high-fidelity mockups for the admin dashboard',
        project: 'Design',
        priority: 'Medium',
        estimatedTime: 6,
        dueDate: '2024-01-18',
        color: '#f59e0b'
    },
    {
        id: 3,
        title: 'Database optimization',
        description: 'Optimize slow queries and add proper indexing to improve performance',
        project: 'Backend',
        priority: 'High',
        estimatedTime: 12,
        dueDate: '2024-01-20',
        color: '#ef4444'
    },
    {
        id: 4,
        title: 'Write API documentation',
        description: 'Document all REST API endpoints with examples and response schemas',
        project: 'Docs',
        priority: 'Low',
        estimatedTime: 4,
        dueDate: '2024-01-25',
        color: '#22c55e'
    },
    {
        id: 5,
        title: 'Mobile app testing',
        description: 'Comprehensive testing of mobile application across different devices',
        project: 'Mobile',
        priority: 'Medium',
        estimatedTime: 10,
        dueDate: '2024-01-22',
        color: '#f59e0b'
    }
])

// Computed properties
const filteredTasks = computed(() => {
    return demoTasks.value.filter(task => {
        const matchesSearch = !searchText.value || 
            task.title.toLowerCase().includes(searchText.value.toLowerCase()) ||
            task.description.toLowerCase().includes(searchText.value.toLowerCase())
        
        const matchesProject = !projectText.value || 
            task.project.toLowerCase().includes(projectText.value.toLowerCase())
        
        return matchesSearch && matchesProject
    })
})

// Methods
const navigateWeek = (direction) => {
    weekNumber.value += direction
}

const refreshData = async () => {
    isRefreshing.value = true
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    isRefreshing.value = false
}

const openTaskDetail = (task) => {
    selectedTask.value = task
    isTaskFormActive.value = true
}

const backToBackLog = () => {
    isTaskFormActive.value = false
    selectedTask.value = null
}

const formatDateDisplay = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
    });
}

const timelineInfoRef = ref()

onMounted(() => {
    // Simulate scroll behavior
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            timelineInfoRef.value?.classList.add('scrolled');
        } else {
            timelineInfoRef.value?.classList.remove('scrolled');
        }
    });
});

</script>

<style scoped>
.scrolled {
    background-color: #fff;
    z-index: 999;
    padding: 0.5rem 1rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    border-radius: 0 0 0.5rem 0.5rem;
    transition: all 0.3s ease;
}

.dark .scrolled {
    background-color: var(--bg-secondary);
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.2);
}

.line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
</style>
