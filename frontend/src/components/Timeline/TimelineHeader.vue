<template>
  <div class="timeline-header bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
    <!-- Top row: Title and actions -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center space-x-4">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Workload Timeline
        </h1>
        
        <!-- Real-time status indicator -->
        <div class="flex items-center space-x-2">
        <div 
          :class="[
            'w-2 h-2 rounded-full',
            realtimeConnected ? 'bg-green-500' : 'bg-red-500'
          ]"
        ></div>

          <span class="text-sm text-gray-600 dark:text-gray-400">
            {{ realtimeConnected ? 'Live' : 'Offline' }}
          </span>
        </div>
        
        <!-- Active users -->
        <div v-if="activeUsers.length > 0" class="flex items-center space-x-1">
          <Avatar
            v-for="user in activeUsers.slice(0, 5)"
            :key="user.user_id"
            :image="user.image"
            :label="user.name"
            size="sm"
            class="border-2 border-white dark:border-gray-800"
          />
          <span 
            v-if="activeUsers.length > 5"
            class="text-xs text-gray-500 dark:text-gray-400 ml-1"
          >
            +{{ activeUsers.length - 5 }}
          </span>
        </div>
      </div>
      
      <!-- Action buttons -->
      <div class="flex items-center space-x-2">
        <Button
          variant="ghost"
          size="sm"
          @click="$emit('refresh')"
          :loading="loading"
        >
          <FeatherIcon name="refresh-cw" class="w-4 h-4" />
          Refresh
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          @click="$emit('export')"
        >
          <FeatherIcon name="download" class="w-4 h-4" />
          Export
        </Button>
        
        <Dropdown :options="viewOptions" @select="handleViewOption">
          <Button variant="ghost" size="sm">
            <FeatherIcon name="more-horizontal" class="w-4 h-4" />
          </Button>
        </Dropdown>
      </div>
    </div>
    
    <!-- Metrics row -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-4">
      <MetricCard
        title="Total Capacity"
        :value="formatHours(metrics.totalCapacity)"
        icon="clock"
        color="blue"
      />
      <MetricCard
        title="Allocated"
        :value="formatHours(metrics.totalAllocated)"
        icon="calendar"
        color="green"
      />
      <MetricCard
        title="Available"
        :value="formatHours(metrics.availableCapacity)"
        icon="plus-circle"
        color="gray"
      />
      <MetricCard
        title="Utilization"
        :value="formatPercent(metrics.overallUtilization)"
        icon="trending-up"
        :color="getUtilizationColor(metrics.overallUtilization)"
      />
      <MetricCard
        title="Overallocated"
        :value="metrics.overallocatedCount"
        icon="alert-triangle"
        color="red"
      />
      <MetricCard
        title="Underutilized"
        :value="metrics.underutilizedCount"
        icon="trending-down"
        color="yellow"
      />
    </div>
    
    <!-- Filters and controls row -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-3">
        <!-- Department filter -->
        <Select
          :value="filters.department"
          :options="departmentOptions"
          placeholder="All Departments"
          @change="updateFilter('department', $event)"
          class="min-w-[150px]"
        />
        
        <!-- Date range filter -->
        <div class="flex items-center space-x-2">
          <VueDatePicker
            v-model="dateRange"
            range
            :enable-time-picker="false"
            placeholder="Select date range"
            @update:model-value="updateDateRange"
            class="min-w-[200px]"
          />
        </div>
        
        <!-- Status filter -->
        <Select
          :value="filters.status"
          :options="statusOptions"
          placeholder="All Statuses"
          @change="updateFilter('status', $event)"
          class="min-w-[120px]"
        />
        
        <!-- Priority filter -->
        <Select
          :value="filters.priority"
          :options="priorityOptions"
          placeholder="All Priorities"
          @change="updateFilter('priority', $event)"
          class="min-w-[120px]"
        />
        
        <!-- Clear filters -->
        <Button
          v-if="hasActiveFilters"
          variant="ghost"
          size="sm"
          @click="clearFilters"
        >
          <FeatherIcon name="x" class="w-4 h-4" />
          Clear
        </Button>
      </div>
      
      <!-- View controls -->
      <div class="flex items-center space-x-3">
        <!-- Timeline view mode -->
        <div class="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            v-for="mode in timelineModes"
            :key="mode.value"
            :class="[
              'px-3 py-1 text-sm rounded-md transition-colors',
              viewSettings.timelineView === mode.value
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            ]"
            @click="updateViewSetting('timelineView', mode.value)"
          >
            {{ mode.label }}
          </button>
        </div>
        
        <!-- Zoom controls -->
        <div class="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            @click="adjustZoom(-0.2)"
            :disabled="viewSettings.zoomLevel <= 0.5"
          >
            <FeatherIcon name="zoom-out" class="w-4 h-4" />
          </Button>
          <span class="text-sm text-gray-600 dark:text-gray-400 min-w-[40px] text-center">
            {{ Math.round(viewSettings.zoomLevel * 100) }}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            @click="adjustZoom(0.2)"
            :disabled="viewSettings.zoomLevel >= 2.0"
          >
            <FeatherIcon name="zoom-in" class="w-4 h-4" />
          </Button>
        </div>
        
        <!-- View options toggles -->
        <div class="flex items-center space-x-2">
          <label class="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              :checked="viewSettings.showUnassigned"
              @change="updateViewSetting('showUnassigned', $event.target.checked)"
              class="rounded border-gray-300 dark:border-gray-600"
            />
            <span class="text-gray-700 dark:text-gray-300">Unassigned</span>
          </label>
          
          <label class="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              :checked="viewSettings.showCompleted"
              @change="updateViewSetting('showCompleted', $event.target.checked)"
              class="rounded border-gray-300 dark:border-gray-600"
            />
            <span class="text-gray-700 dark:text-gray-300">Completed</span>
          </label>
          
          <label class="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              :checked="viewSettings.showBacklog"
              @change="updateViewSetting('showBacklog', $event.target.checked)"
              class="rounded border-gray-300 dark:border-gray-600"
            />
            <span class="text-gray-700 dark:text-gray-300">Backlog</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Avatar, Button, Select, Dropdown, FeatherIcon } from 'frappe-ui'
import VueDatePicker from '@vuepic/vue-datepicker'
import MetricCard from './MetricCard.vue'

// Props
const props = defineProps({
  loading: Boolean,
  metrics: {
    type: Object,
    default: () => ({})
  },
  filters: {
    type: Object,
    default: () => ({})
  },
  viewSettings: {
    type: Object,
    default: () => ({})
  },
  activeUsers: {
    type: Array,
    default: () => []
  },
  realtimeConnected: Boolean
})

// Emits
const emit = defineEmits([
  'update-filters',
  'update-view-settings',
  'refresh',
  'export'
])

// Local state
const dateRange = ref([
  props.filters.start_date ? new Date(props.filters.start_date) : null,
  props.filters.end_date ? new Date(props.filters.end_date) : null
])

// Options
const departmentOptions = [
  { label: 'All Departments', value: null },
  { label: 'Engineering', value: 'Engineering' },
  { label: 'Design', value: 'Design' },
  { label: 'Marketing', value: 'Marketing' },
  { label: 'Sales', value: 'Sales' },
  { label: 'Support', value: 'Support' }
]

const statusOptions = [
  { label: 'All Statuses', value: null },
  { label: 'Open', value: 'Open' },
  { label: 'Working', value: 'Working' },
  { label: 'Pending Review', value: 'Pending Review' },
  { label: 'Completed', value: 'Completed' },
  { label: 'Cancelled', value: 'Cancelled' }
]

const priorityOptions = [
  { label: 'All Priorities', value: null },
  { label: 'Low', value: 'Low' },
  { label: 'Medium', value: 'Medium' },
  { label: 'High', value: 'High' },
  { label: 'Urgent', value: 'Urgent' }
]

const timelineModes = [
  { label: 'Day', value: 'day' },
  { label: 'Week', value: 'week' },
  { label: 'Month', value: 'month' },
  { label: 'Quarter', value: 'quarter' }
]

const viewOptions = [
  { label: 'Reset View', value: 'reset' },
  { label: 'Fit to Screen', value: 'fit' },
  { label: 'Show All Tasks', value: 'show_all' },
  { label: 'Hide Completed', value: 'hide_completed' },
  { label: 'Group by Project', value: 'group_project' },
  { label: 'Group by Priority', value: 'group_priority' }
]

// Computed
const hasActiveFilters = computed(() => {
  return props.filters.department || 
         props.filters.status || 
         props.filters.priority ||
         props.filters.start_date ||
         props.filters.end_date
})

// Methods
const updateFilter = (key, value) => {
  emit('update-filters', { [key]: value })
}

const updateViewSetting = (key, value) => {
  emit('update-view-settings', { [key]: value })
}

const updateDateRange = (range) => {
  if (range && range.length === 2) {
    emit('update-filters', {
      start_date: range[0]?.toISOString().split('T')[0],
      end_date: range[1]?.toISOString().split('T')[0]
    })
  } else {
    emit('update-filters', {
      start_date: null,
      end_date: null
    })
  }
}

const clearFilters = () => {
  dateRange.value = [null, null]
  emit('update-filters', {
    department: null,
    status: null,
    priority: null,
    assignee: null,
    start_date: null,
    end_date: null
  })
}

const adjustZoom = (delta) => {
  const newZoom = Math.max(0.5, Math.min(2.0, props.viewSettings.zoomLevel + delta))
  updateViewSetting('zoomLevel', newZoom)
}

const handleViewOption = (option) => {
  switch (option.value) {
    case 'reset':
      resetView()
      break
    case 'fit':
      fitToScreen()
      break
    case 'show_all':
      showAllTasks()
      break
    case 'hide_completed':
      hideCompleted()
      break
    case 'group_project':
      updateViewSetting('groupBy', 'project')
      break
    case 'group_priority':
      updateViewSetting('groupBy', 'priority')
      break
  }
}

const resetView = () => {
  emit('update-view-settings', {
    timelineView: 'month',
    zoomLevel: 1.0,
    showUnassigned: true,
    showCompleted: false,
    showBacklog: true,
    groupBy: 'assignee',
    sortBy: 'priority'
  })
}

const fitToScreen = () => {
  // Calculate optimal zoom level based on content
  updateViewSetting('zoomLevel', 1.0)
}

const showAllTasks = () => {
  emit('update-view-settings', {
    showUnassigned: true,
    showCompleted: true,
    showBacklog: true
  })
}

const hideCompleted = () => {
  updateViewSetting('showCompleted', false)
}

// Utility functions
const formatHours = (hours) => {
  if (!hours) return '0h'
  return `${Math.round(hours)}h`
}

const formatPercent = (percent) => {
  if (!percent) return '0%'
  return `${Math.round(percent)}%`
}

const getUtilizationColor = (utilization) => {
  if (utilization > 100) return 'red'
  if (utilization > 90) return 'yellow'
  if (utilization > 70) return 'green'
  return 'gray'
}

// Watch for external filter changes
watch(() => props.filters, (newFilters) => {
  if (newFilters.start_date && newFilters.end_date) {
    dateRange.value = [
      new Date(newFilters.start_date),
      new Date(newFilters.end_date)
    ]
  }
}, { deep: true })
</script>

<style scoped>
.timeline-header {
  min-height: 120px;
}

/* Custom checkbox styling */
input[type="checkbox"] {
  @apply w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600;
}

/* Date picker custom styling */
:deep(.dp__input) {
  @apply border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white;
}

:deep(.dp__input:focus) {
  @apply ring-2 ring-blue-500 border-blue-500;
}
</style>
