<template>
  <div 
    :class="[
      'metric-card p-4 rounded-lg border transition-all duration-200 hover:shadow-md',
      colorClasses
    ]"
  >
    <div class="flex items-center justify-between">
      <div class="flex-1">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
          {{ title }}
        </p>
        <p :class="['text-2xl font-bold', valueColorClass]">
          {{ displayValue }}
        </p>
        <p v-if="subtitle" class="text-xs text-gray-500 dark:text-gray-500 mt-1">
          {{ subtitle }}
        </p>
      </div>
      
      <div :class="['flex-shrink-0 ml-3', iconColorClass]">
        <FeatherIcon :name="icon" class="w-6 h-6" />
      </div>
    </div>
    
    <!-- Trend indicator -->
    <div v-if="trend" class="flex items-center mt-2 text-xs">
      <FeatherIcon 
        :name="trend.direction === 'up' ? 'trending-up' : 'trending-down'"
        :class="[
          'w-3 h-3 mr-1',
          trend.direction === 'up' ? 'text-green-500' : 'text-red-500'
        ]"
      />
      <span :class="trend.direction === 'up' ? 'text-green-600' : 'text-red-600'">
        {{ trend.value }}
      </span>
      <span class="text-gray-500 ml-1">{{ trend.period }}</span>
    </div>
    
    <!-- Progress bar for percentage values -->
    <div v-if="showProgress && progressValue !== null" class="mt-3">
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div 
          :class="[
            'h-2 rounded-full transition-all duration-300',
            progressColorClass
          ]"
          :style="{ width: `${Math.min(100, Math.max(0, progressValue))}%` }"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

// Props
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  subtitle: {
    type: String,
    default: null
  },
  icon: {
    type: String,
    required: true
  },
  color: {
    type: String,
    default: 'gray',
    validator: (value) => ['gray', 'blue', 'green', 'yellow', 'red', 'purple', 'indigo'].includes(value)
  },
  trend: {
    type: Object,
    default: null,
    validator: (value) => {
      if (!value) return true
      return value.direction && value.value && ['up', 'down'].includes(value.direction)
    }
  },
  showProgress: {
    type: Boolean,
    default: false
  },
  clickable: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['click'])

// Computed properties
const displayValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})

const progressValue = computed(() => {
  if (!props.showProgress) return null
  
  // Extract percentage from string values like "85%"
  if (typeof props.value === 'string' && props.value.includes('%')) {
    return parseFloat(props.value.replace('%', ''))
  }
  
  // For numeric values, assume they're already percentages
  if (typeof props.value === 'number' && props.value <= 100) {
    return props.value
  }
  
  return null
})

const colorClasses = computed(() => {
  const baseClasses = 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
  
  if (props.clickable) {
    return `${baseClasses} cursor-pointer hover:border-${props.color}-300 dark:hover:border-${props.color}-600`
  }
  
  return baseClasses
})

const valueColorClass = computed(() => {
  const colorMap = {
    gray: 'text-gray-900 dark:text-white',
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-green-600 dark:text-green-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    red: 'text-red-600 dark:text-red-400',
    purple: 'text-purple-600 dark:text-purple-400',
    indigo: 'text-indigo-600 dark:text-indigo-400'
  }
  
  return colorMap[props.color] || colorMap.gray
})

const iconColorClass = computed(() => {
  const colorMap = {
    gray: 'text-gray-400 dark:text-gray-500',
    blue: 'text-blue-500 dark:text-blue-400',
    green: 'text-green-500 dark:text-green-400',
    yellow: 'text-yellow-500 dark:text-yellow-400',
    red: 'text-red-500 dark:text-red-400',
    purple: 'text-purple-500 dark:text-purple-400',
    indigo: 'text-indigo-500 dark:text-indigo-400'
  }
  
  return colorMap[props.color] || colorMap.gray
})

const progressColorClass = computed(() => {
  const colorMap = {
    gray: 'bg-gray-500',
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
    indigo: 'bg-indigo-500'
  }
  
  return colorMap[props.color] || colorMap.gray
})

// Methods
const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped>
.metric-card {
  min-height: 100px;
}

/* Hover effects for clickable cards */
.metric-card.cursor-pointer:hover {
  transform: translateY(-1px);
}

/* Animation for progress bar */
.metric-card .h-2 {
  transition: width 0.3s ease-in-out;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .metric-card {
    min-height: 80px;
  }
  
  .metric-card .text-2xl {
    @apply text-xl;
  }
  
  .metric-card .w-6 {
    @apply w-5 h-5;
  }
}
</style>
