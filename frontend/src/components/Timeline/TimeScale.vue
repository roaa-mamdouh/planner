<template>
  <div class="time-scale bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-20">
    <!-- Main time scale -->
    <div class="flex" :style="{ height: `${scaleHeight}px` }">
      <div
        v-for="(period, index) in timePeriods"
        :key="index"
        :class="[
          'time-period border-r border-gray-200 dark:border-gray-700 flex items-center justify-center text-sm font-medium',
          period.isToday ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300',
          period.isWeekend ? 'bg-gray-50 dark:bg-gray-800/50' : ''
        ]"
        :style="{ width: `${period.width}px` }"
      >
        <div class="text-center">
          <div class="font-semibold">{{ period.primary }}</div>
          <div v-if="period.secondary" class="text-xs text-gray-500 dark:text-gray-400">
            {{ period.secondary }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Sub-scale for detailed view -->
    <div v-if="showSubScale" class="flex border-t border-gray-100 dark:border-gray-700" :style="{ height: `${subScaleHeight}px` }">
      <div
        v-for="(subPeriod, index) in subTimePeriods"
        :key="index"
        :class="[
          'sub-time-period border-r border-gray-100 dark:border-gray-700 flex items-center justify-center text-xs',
          subPeriod.isToday ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400',
          subPeriod.isWeekend ? 'bg-gray-50 dark:bg-gray-800/50' : ''
        ]"
        :style="{ width: `${subPeriod.width}px` }"
      >
        {{ subPeriod.label }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  startDate: {
    type: Date,
    required: true
  },
  endDate: {
    type: Date,
    required: true
  },
  viewMode: {
    type: String,
    default: 'month',
    validator: (value) => ['day', 'week', 'month', 'quarter'].includes(value)
  },
  zoomLevel: {
    type: Number,
    default: 1.0
  }
})

// Computed properties
const scaleHeight = computed(() => {
  return props.viewMode === 'day' ? 60 : 40
})

const subScaleHeight = computed(() => {
  return 30
})

const showSubScale = computed(() => {
  return props.viewMode === 'day' || (props.viewMode === 'week' && props.zoomLevel > 1.5)
})

const columnWidth = computed(() => {
  const baseWidths = {
    day: 120,
    week: 80,
    month: 40,
    quarter: 20
  }
  
  return Math.round(baseWidths[props.viewMode] * props.zoomLevel)
})

const timePeriods = computed(() => {
  const periods = []
  const current = new Date(props.startDate)
  const end = new Date(props.endDate)
  const today = new Date()
  
  while (current <= end) {
    const isToday = isDateToday(current, today)
    const isWeekend = current.getDay() === 0 || current.getDay() === 6
    
    periods.push({
      date: new Date(current),
      primary: getPrimaryLabel(current),
      secondary: getSecondaryLabel(current),
      width: columnWidth.value,
      isToday,
      isWeekend
    })
    
    incrementDate(current)
  }
  
  return periods
})

const subTimePeriods = computed(() => {
  if (!showSubScale.value) return []
  
  const periods = []
  const current = new Date(props.startDate)
  const end = new Date(props.endDate)
  const today = new Date()
  
  while (current <= end) {
    const isToday = isDateToday(current, today)
    const isWeekend = current.getDay() === 0 || current.getDay() === 6
    
    periods.push({
      date: new Date(current),
      label: getSubLabel(current),
      width: getSubColumnWidth(),
      isToday,
      isWeekend
    })
    
    incrementSubDate(current)
  }
  
  return periods
})

// Methods
const isDateToday = (date, today) => {
  switch (props.viewMode) {
    case 'day':
      return date.toDateString() === today.toDateString()
    case 'week':
      return getWeekNumber(date) === getWeekNumber(today) && date.getFullYear() === today.getFullYear()
    case 'month':
      return date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear()
    case 'quarter':
      return Math.ceil((date.getMonth() + 1) / 3) === Math.ceil((today.getMonth() + 1) / 3) && date.getFullYear() === today.getFullYear()
    default:
      return false
  }
}

const getPrimaryLabel = (date) => {
  switch (props.viewMode) {
    case 'day':
      return date.toLocaleDateString('en-US', { weekday: 'short' })
    case 'week':
      return `Week ${getWeekNumber(date)}`
    case 'month':
      return date.toLocaleDateString('en-US', { month: 'short' })
    case 'quarter':
      return `Q${Math.ceil((date.getMonth() + 1) / 3)}`
    default:
      return ''
  }
}

const getSecondaryLabel = (date) => {
  switch (props.viewMode) {
    case 'day':
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    case 'week':
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    case 'month':
      return date.getFullYear().toString()
    case 'quarter':
      return date.getFullYear().toString()
    default:
      return ''
  }
}

const getSubLabel = (date) => {
  switch (props.viewMode) {
    case 'day':
      return date.getHours().toString().padStart(2, '0') + ':00'
    case 'week':
      return date.toLocaleDateString('en-US', { weekday: 'short' }).charAt(0)
    default:
      return ''
  }
}

const getSubColumnWidth = () => {
  switch (props.viewMode) {
    case 'day':
      return Math.round(columnWidth.value / 24) // Hours in a day
    case 'week':
      return Math.round(columnWidth.value / 7) // Days in a week
    default:
      return columnWidth.value
  }
}

const incrementDate = (date) => {
  switch (props.viewMode) {
    case 'day':
      date.setDate(date.getDate() + 1)
      break
    case 'week':
      date.setDate(date.getDate() + 7)
      break
    case 'month':
      date.setMonth(date.getMonth() + 1)
      break
    case 'quarter':
      date.setMonth(date.getMonth() + 3)
      break
  }
}

const incrementSubDate = (date) => {
  switch (props.viewMode) {
    case 'day':
      date.setHours(date.getHours() + 1)
      break
    case 'week':
      date.setDate(date.getDate() + 1)
      break
    default:
      incrementDate(date)
  }
}

const getWeekNumber = (date) => {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  d.setDate(d.getDate() + 3 - (d.getDay() + 6) % 7)
  const week1 = new Date(d.getFullYear(), 0, 4)
  return 1 + Math.round(((d.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7)
}
</script>

<style scoped>
.time-scale {
  user-select: none;
}

.time-period {
  transition: background-color 0.2s ease;
}

.time-period:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .time-period:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.sub-time-period {
  transition: background-color 0.2s ease;
}

.sub-time-period:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.dark .sub-time-period:hover {
  background-color: rgba(255, 255, 255, 0.03);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .time-period {
    font-size: 0.75rem;
  }
  
  .sub-time-period {
    font-size: 0.625rem;
  }
}
</style>
