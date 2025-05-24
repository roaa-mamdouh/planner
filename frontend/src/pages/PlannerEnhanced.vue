<template>
    <Layout :breadcrumbs="breadcrumbs">
        <div class="mx-auto px-4 lg:px-8 max-w-[1800px]">
            <!-- Enhanced Navigation Controls -->
            <div class="enhanced-nav-controls flex justify-between items-center mb-6 sticky top-0 z-50" ref="timelineInfoRef">
                <div class="flex items-center gap-3">
                    <Button 
                        :variant="'solid'" 
                        theme="gray" 
                        size="md" 
                        id="buttonPrev"
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
                        id="buttonNext"
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
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ completedTasksCount }} Completed</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ inProgressTasksCount }} In Progress</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ overdueTasksCount }} Overdue</span>
                                </div>
                            </div>
                            <div class="text-sm font-medium text-gray-600 dark:text-gray-400">
                                Total: {{ totalTasksCount }} tasks
                            </div>
                        </div>

                        <div ref="timeline" id="timeline" class="min-h-[500px]"></div>
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
                                            @keyup.enter="getBacklogTasks"
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
                                            @keyup.enter="getBacklogTasks"
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
                                    {{ backlog.length }}
                                </div>
                            </div>

                            <!-- Enhanced Task Cards -->
                            <div class="p-4 space-y-3 max-h-[600px] overflow-y-auto">
                                <div 
                                    v-for="(task, index) in backlog" 
                                    :key="task.name"
                                    class="enhanced-task-card"
                                    :style="{ '--task-accent-color': task.color || '#3b82f6', animationDelay: `${index * 50}ms` }"
                                    @click="openTaskDetail(task.name)" 
                                    draggable="true"
                                    @dragstart="dragBackLog($event, task)"
                                    tabindex="0"
                                    @keydown.enter="openTaskDetail(task.name)"
                                >
                                    <div :id="task.name" class="space-y-3">
                                        <!-- Task Header -->
                                        <div class="flex items-start justify-between">
                                            <div class="flex-1 min-w-0">
                                                <div class="flex items-center gap-2 mb-1">
                                                    <span v-if="task.project" class="task-project-tag">
                                                        {{ task.project }}
                                                    </span>
                                                    <span :class="['task-priority-badge', `priority-${task.priority?.toLowerCase() || 'medium'}`]">
                                                        {{ task.priority || 'Medium' }}
                                                    </span>
                                                </div>
                                                <h4 class="font-semibold text-gray-900 dark:text-white text-sm leading-tight mb-1">
                                                    {{ task.subject }}
                                                </h4>
                                                <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                                                    {{ task.project_name }}
                                                </p>
                                            </div>
                                            <FeatherIcon name="more-vertical" class="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-pointer" />
                                        </div>

                                        <!-- Task Footer -->
                                        <div class="flex items-center justify-between">
                                            <div class="flex items-center gap-2">
                                                <div class="task-time-estimate">
                                                    <FeatherIcon name="clock" class="w-3 h-3" />
                                                    {{ task.expected_time }}h
                                                </div>
                                            </div>
                                            <div class="text-right">
                                                <p class="text-xs font-medium text-gray-900 dark:text-white">
                                                    {{ formatDateDisplay(task.exp_start_date) }}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Empty State -->
                                <div v-if="backlog.length === 0" class="text-center py-8">
                                    <FeatherIcon name="inbox" class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                                    <p class="text-gray-500 dark:text-gray-400 text-sm">No tasks in backlog</p>
                                    <p class="text-gray-400 dark:text-gray-500 text-xs mt-1">Tasks will appear here when available</p>
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
                                <!-- Task Link -->
                                <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/30">
                                    <a 
                                        target="_blank" 
                                        :href="getURL() + '/app/task/' + activeTask" 
                                        class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium text-sm flex items-center gap-2 transition-colors duration-200"
                                    >
                                        <FeatherIcon name="external-link" class="w-4 h-4" />
                                        Open in Frappe: {{ activeTask }}
                                    </a>
                                </div>
                                
                                <TaskForm :task='activeTask' :department='department' />
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
import { computed, ref, onMounted, watchEffect, reactive  } from "vue";
import TaskForm from "@/components/Task/TaskForm.vue";
import { Timeline, DataSet } from 'vis-timeline/standalone';
import { useRoute } from 'vue-router';
import { createResource, createListResource, Avatar } from 'frappe-ui'
import { getURL } from '../getURL.js' 

const route = useRoute();
const searchText = defineModel('searchText')
const projectText = defineModel('projectText')

// Enhanced reactive variables
const viewMode = ref('week')
const isRefreshing = ref(false)

// The employees with all tasks
var employees = {}

// All the tasks in backlog
var backlog = reactive([]);

// Computed properties for task statistics
const completedTasksCount = computed(() => {
    if (!employees || !employees.length) return 0
    return employees.reduce((count, employee) => {
        return count + employee.tasks.filter(task => task.status === 'Completed').length
    }, 0)
})

const inProgressTasksCount = computed(() => {
    if (!employees || !employees.length) return 0
    return employees.reduce((count, employee) => {
        return count + employee.tasks.filter(task => task.status === 'Working').length
    }, 0)
})

const overdueTasksCount = computed(() => {
    if (!employees || !employees.length) return 0
    const today = new Date()
    return employees.reduce((count, employee) => {
        return count + employee.tasks.filter(task => {
            const endDate = new Date(task.endDate)
            return endDate < today && task.status !== 'Completed'
        }).length
    }, 0)
})

const totalTasksCount = computed(() => {
    if (!employees || !employees.length) return 0
    return employees.reduce((count, employee) => count + employee.tasks.length, 0)
})

// Enhanced refresh function
const refreshData = async () => {
    isRefreshing.value = true
    try {
        await Promise.all([
            getEmployeeTasks(),
            getBacklogTasks()
        ])
    } finally {
        isRefreshing.value = false
    }
}

const getBacklogTasks = () => {
    const resp = createResource({
        url: 'planner.api.planner_get_backlog', 
        params : {
            searchtext: searchText.value, 
            projectText: projectText.value
        }, 
        auto: true,
        onSuccess:(data) => {
            backlog.splice(0);
            data.forEach(task => {
                backlog.push(task);
            });
        }
    });
}

// Get which dashboard we are supposed to load
const dashboardName = route.params.dashboardName;
const department = route.params.department;

let breadcrumbs = [
    {
        label: 'Dashboard',
        route: {
            name: 'Dashboard',
        },
    },
    {
        label: dashboardName,
        route: {
            name: 'Planner'
        }
    },
];

let currentDate = ref(new Date());
let isTaskFormActive = ref(false);
let activeTask = ref("");
let weekNumber = ref(0);

const timeline = ref();

const openTaskDetail = (taskName) => {
    activeTask = taskName
    isTaskFormActive.value = true;
};

const dragEndBackLog = (val) => {
    console.log("drop", val)
}

const dragBackLog = (event, task) => {
    event.dataTransfer.effectAllowed = 'move';

    var tasktitle = task.project ? task.project + ' - ' + task.subject : task.subject

    let item = {
        id: task.name,
        name: task.name,
        type: 'range',
        content: {
            name: task.name,
            title: tasktitle, 
            project_name: task.project_name, 
            type: task.type
        }
    };

    event.target.id = item.id; 

    let startDateTime = new Date(currentDate.value);
    startDateTime.setHours(0, 0, 0, 0);
    item.content.startDate = startDateTime.toLocaleDateString('de-DE'); 

    let endDateTime = new Date(currentDate.value.setDate(currentDate.value.getDate() + 2));
    endDateTime.setHours(0, 0, 0, 0);
    item.content.endDate = endDateTime.toLocaleDateString('de-DE'); 

    event.dataTransfer.setData('text', JSON.stringify(item));
    event.target.addEventListener('dragend', dragEndBackLog.bind(this), false);
};

const backToBackLog = () => {
    isTaskFormActive.value = false;
    let selectedItem = timeline.value?.querySelector('.vis-item.vis-range.vis-selected');
    if (selectedItem) {
        selectedItem.classList.remove('vis-selected');
    }
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
};

const formatDateDisplay = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
    });
};

const getWeekNumber = (d) => {
    d = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    let date = d;
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() + 3 - (date.getDay() + 6) % 7);
    let week1 = new Date(date.getFullYear(), 0, 4);
    return 1 + Math.round(((date.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
}

const getEmployeeTasks = () => {
    const resource = createResource({
        url: 'planner.api.get_planner_tasks', 
        params : {
            department: department
        }, 
        auto: true,
        onSuccess: (data) => {
            employees = resource.data
            initTimeLine()
        }
    });
}

const timelineInfoRef = ref();

// Watch for view mode changes
watchEffect(() => {
    if (employees && employees.length > 0) {
        initTimeLine()
    }
})

onMounted(() => {
    searchText.value = "";
    projectText.value = "";

    getEmployeeTasks();
    getBacklogTasks();
    
    weekNumber.value = getWeekNumber(new Date(currentDate.value));
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            timelineInfoRef.value?.classList.add('scrolled');
        } else {
            timelineInfoRef.value?.classList.remove('scrolled');
        }
        
        var element = document.querySelector(".vis-panel.vis-top");
        if (window.scrollY > 200) {
            if (element) {
                element.classList.add('scroll');
                element.style.top = (window.scrollY - 135) + 'px';
            }
        } else {
            if (element) {
                element.classList.remove('scroll');
                element.style.top = '0px';
            }
        }
    });
});

const initTimeLine = () => {
    // Implementation will be added in next step
    console.log("Timeline initialization - enhanced version");
}

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
