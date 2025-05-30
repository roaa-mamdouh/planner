<template>
  <div class="assignee-sidebar w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
    <!-- Sidebar Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Team Members
        </h3>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ assignees.length }}
        </div>
      </div>
    </div>
    
    <!-- Assignee List -->
    <div class="flex-1 overflow-y-auto">
      <div class="p-2 space-y-1">
        <div
          v-for="assignee in assignees"
          :key="assignee.id"
          :class="[
            'assignee-row p-3 rounded-lg cursor-pointer transition-all duration-200',
            selectedAssignee === assignee.id
              ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700'
              : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
          ]"
          @click="$emit('select-assignee', assignee.id)"
        >
          <!-- Assignee Info -->
          <div class="flex items-center space-x-3">
            <Avatar
              :image="assignee.image"
              :label="assignee.name"
              size="md"
            />
            
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ assignee.name }}
                </p>
                <div class="flex items-center space-x-1">
                  <!-- Utilization indicator -->
                  <div
                    :class="[
                      'w-2 h-2 rounded-full',
                      getUtilizationColor(assignee.utilization)
                    ]"
                  />
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    {{ Math.round(assignee.utilization || 0) }}%
                  </span>
                </div>
              </div>
              
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
                {{ assignee.department || 'No Department' }}
              </p>
              
              <!-- Metrics (if enabled) -->
              <div v-if="showMetrics" class="mt-2 grid grid-cols-3 gap-2 text-xs">
                <div class="text-center">
                  <div class="font-medium text-gray-900 dark:text-white">
                    {{ assignee.taskCount || 0 }}
                  </div>
                  <div class="text-gray-500 dark:text-gray-400">Tasks</div>
                </div>
                <div class="text-center">
                  <div class="font-medium text-gray-900 dark:text-white">
                    {{ formatHours(assignee.allocatedHours || 0) }}
                  </div>
                  <div class="text-gray-500 dark:text-gray-400">Hours</div>
                </div>
                <div class="text-center">
                  <div class="font-medium text-gray-900 dark:text-white">
                    {{ formatHours(assignee.availableHours || 0) }}
                  </div>
                  <div class="text-gray-500 dark:text-gray-400">Available</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Capacity Bar -->
          <div class="mt-3">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="text-gray-600 dark:text-gray-400">Capacity</span>
              <span :class="getUtilizationTextColor(assignee.utilization)">
                {{ Math.round(assignee.utilization || 0) }}%
              </span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                :class="[
                  'h-2 rounded-full transition-all duration-300',
                  getUtilizationBarColor(assignee.utilization)
                ]"
                :style="{ width: `${Math.min(100, Math.max(0, assignee.utilization || 0))}%` }"
              />
            </div>
          </div>
          
          <!-- Action Menu -->
          <div class="mt-2 flex items-center justify-end space-x-1">
            <Button
              variant="ghost"
              size="sm"
              @click.stop="$emit('assignee-action', 'view_capacity', assignee.id)"
            >
              <FeatherIcon name="bar-chart-2" class="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              @click.stop="$emit('assignee-action', 'assign_task', assignee.id)"
            >
              <FeatherIcon name="plus" class="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              @click.stop="$emit('assignee-action', 'view_workload', assignee.id)"
            >
              <FeatherIcon name="eye" class="w-3 h-3" />
            </Button>
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-if="assignees.length === 0" class="text-center py-8">
          <FeatherIcon name="users" class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p class="text-gray-500 dark:text-gray-400 text-sm">No team members found</p>
          <p class="text-gray-400 dark:text-gray-500 text-xs mt-1">Add team members to get started</p>
        </div>
      </div>
    </div>
    
    <!-- Sidebar Footer -->
    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
      <div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
        <div class="flex items-center justify-between">
          <span>Total Capacity:</span>
          <span>{{ formatHours(totalCapacity) }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Allocated:</span>
          <span>{{ formatHours(totalAllocated) }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Available:</span>
          <span>{{ formatHours(totalCapacity - totalAllocated) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, Button, FeatherIcon } from 'frappe-ui'

// Props
const props = defineProps({
  assignees: {
    type: Array,
    default: () => []
  },
  selectedAssignee: {
    type: String,
    default: null
  },
  showMetrics: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'select-assignee',
  'assignee-action'
])

// Computed properties
const totalCapacity = computed(() => {
  return props.assignees.reduce((sum, assignee) => sum + (assignee.totalCapacity || 0), 0)
})

const totalAllocated = computed(() => {
  return props.assignees.reduce((sum, assignee) => sum + (assignee.allocatedHours || 0), 0)
})

// Methods
const getUtilizationColor = (utilization) => {
  if (!utilization) return 'bg-gray-300'
  if (utilization > 100) return 'bg-red-500'
  if (utilization > 90) return 'bg-yellow-500'
  if (utilization > 70) return 'bg-green-500'
  return 'bg-blue-500'
}

const getUtilizationTextColor = (utilization) => {
  if (!utilization) return 'text-gray-500'
  if (utilization > 100) return 'text-red-600 dark:text-red-400'
  if (utilization > 90) return 'text-yellow-600 dark:text-yellow-400'
  if (utilization > 70) return 'text-green-600 dark:text-green-400'
  return 'text-blue-600 dark:text-blue-400'
}

const getUtilizationBarColor = (utilization) => {
  if (!utilization) return 'bg-gray-300'
  if (utilization > 100) return 'bg-red-500'
  if (utilization > 90) return 'bg-yellow-500'
  if (utilization > 70) return 'bg-green-500'
  return 'bg-blue-500'
}

const formatHours = (hours) => {
  if (!hours) return '0h'
  return `${Math.round(hours)}h`
}
</script>

<style scoped>
.assignee-sidebar {
  min-width: 280px;
  max-width: 320px;
}

.assignee-row {
  transition: all 0.2s ease;
}

.assignee-row:hover {
  transform: translateX(2px);
}

/* Scrollbar styling */
.assignee-sidebar ::-webkit-scrollbar {
  width: 6px;
}

.assignee-sidebar ::-webkit-scrollbar-track {
  background: rgba(0,0,0,0.1);
}

.assignee-sidebar ::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.3);
  border-radius: 3px;
}

.assignee-sidebar ::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.5);
}

.dark .assignee-sidebar ::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.1);
}

.dark .assignee-sidebar ::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.3);
}

.dark .assignee-sidebar ::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.5);
}
</style>
