<template>
  <div class="alert-panel bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <h3 class="text-sm font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
          <FeatherIcon name="alert-triangle" class="w-4 h-4 inline mr-2" />
          Workload Alerts & Recommendations
        </h3>
        
        <!-- Alerts -->
        <div v-if="alerts.length > 0" class="space-y-2 mb-4">
          <div
            v-for="alert in alerts"
            :key="alert.id"
            class="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-md border border-yellow-200 dark:border-yellow-700"
          >
            <div class="flex items-center space-x-3">
              <FeatherIcon 
                :name="getAlertIcon(alert.type)" 
                :class="getAlertIconClass(alert.severity)"
                class="w-4 h-4"
              />
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ alert.title }}
                </p>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  {{ alert.message }}
                </p>
              </div>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              @click="$emit('dismiss-alert', alert.id)"
            >
              <FeatherIcon name="x" class="w-3 h-3" />
            </Button>
          </div>
        </div>
        
        <!-- Recommendations -->
        <div v-if="recommendations.length > 0" class="space-y-2">
          <div
            v-for="recommendation in recommendations"
            :key="recommendation.id"
            class="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md border border-blue-200 dark:border-blue-700"
          >
            <div class="flex items-center space-x-3">
              <FeatherIcon name="lightbulb" class="w-4 h-4 text-blue-500" />
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ recommendation.title }}
                </p>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  {{ recommendation.description }}
                </p>
              </div>
            </div>
            
            <div class="flex items-center space-x-2">
              <Button
                variant="solid"
                theme="blue"
                size="sm"
                @click="$emit('apply-recommendation', recommendation)"
              >
                Apply
              </Button>
              <Button
                variant="ghost"
                size="sm"
                @click="$emit('dismiss-recommendation', recommendation.id)"
              >
                <FeatherIcon name="x" class="w-3 h-3" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Button, FeatherIcon } from 'frappe-ui'

// Props
const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  },
  recommendations: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits([
  'dismiss-alert',
  'dismiss-recommendation',
  'apply-recommendation'
])

// Methods
const getAlertIcon = (type) => {
  const iconMap = {
    overallocation: 'alert-triangle',
    deadline: 'clock',
    capacity: 'users',
    conflict: 'alert-circle',
    performance: 'trending-down'
  }
  
  return iconMap[type] || 'alert-triangle'
}

const getAlertIconClass = (severity) => {
  const classMap = {
    high: 'text-red-500',
    medium: 'text-yellow-500',
    low: 'text-blue-500'
  }
  
  return classMap[severity] || 'text-yellow-500'
}
</script>

<style scoped>
.alert-panel {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
