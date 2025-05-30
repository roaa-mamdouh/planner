<template>
  <div class="timeline-grid relative">
    <!-- Grid background -->
    <div 
      class="grid-background absolute inset-0"
      :style="gridStyle"
    />
    
    <!-- Time columns -->
    <div class="time-columns flex">
      <div
        v-for="(column, index) in timeColumns"
        :key="index"
        :class="[
          'time-column border-r border-gray-200 dark:border-gray-700',
          column.isToday ? 'bg-blue-50 dark:bg-blue-900/10' : '',
          column.isWeekend ? 'bg-gray-50 dark:bg-gray-800/50' : ''
        ]"
        :style="{ width: `${columnWidth}px` }"
      >
        <!-- Column content can be added here if needed -->
      </div>
    </div>
    
    <!-- Current time indicator -->
    <div
      v-if="showCurrentTime"
      class="current-time-line absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
      :style="{ left: `${currentTimePosition}px` }"
    >
      <div class="absolute -top-2 -left-2 w-4 h-4 bg-red-500 rounded-full" />
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
  },
  showCurrentTime: {
    type: Boolean,
    default: true
  }
})

// Computed properties
const columnWidth = computed(() => {
  const baseWidths = {
    day: 120,
    week: 80,
    month: 40,
    quarter: 20
  }
  
  return Math.round(baseWidths[props.viewMode] * props.zoomLevel)
})

const timeColumns = computed(() => {
  const columns = []
  const current = new Date(props.startDate)
  const end = new Date(props.endDate)
  const today = new Date()
  
  while (current <= end) {
    const isToday = current.toDateString() === today.toDateString()
    const isWeekend = current.getDay() === 0 || current.getDay() === 6
    
    columns.push({
      date: new Date(current),
      isToday,
      isWeekend,
      label: formatColumnLabel(current)
    })
    
    // Increment based on view mode
    switch (props.viewMode) {
      case 'day':
        current.setDate(current.getDate() + 1)
        break
      case 'week':
        current.setDate(current.getDate() + 7)
        break
      case 'month':
        current.setMonth(current.getMonth() + 1)
        break
      case 'quarter':
        current.setMonth(current.getMonth() + 3)
        break
    }
  }
  
  return columns
})

const gridStyle = computed(() => {
  return {
    backgroundImage: `repeating-linear-gradient(
      to right,
      transparent,
      transparent ${columnWidth.value - 1}px,
      rgba(0, 0, 0, 0.1) ${columnWidth.value - 1}px,
      rgba(0, 0, 0, 0.1) ${columnWidth.value}px
    )`,
    backgroundSize: `${columnWidth.value}px 100%`
  }
})

const currentTimePosition = computed(() => {
  if (!props.showCurrentTime) return 0
  
  const now = new Date()
  const start = new Date(props.startDate)
  const totalDuration = props.endDate.getTime() - start.getTime()
  const currentDuration = now.getTime() - start.getTime()
  
  if (currentDuration < 0 || currentDuration > totalDuration) {
    return -10 // Hide if outside range
  }
  
  const totalWidth = timeColumns.value.length * columnWidth.value
  return (currentDuration / totalDuration) * totalWidth
})

// Methods
const formatColumnLabel = (date) => {
  switch (props.viewMode) {
    case 'day':
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    case 'week':
      return `Week ${getWeekNumber(date)}`
    case 'month':
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        year: 'numeric' 
      })
    case 'quarter':
      return `Q${Math.ceil((date.getMonth() + 1) / 3)} ${date.getFullYear()}`
    default:
      return date.toLocaleDateString()
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
.timeline-grid {
  min-height: 100%;
}

.time-column {
  min-height: 100%;
  transition: background-color 0.2s ease;
}

.current-time-line {
  pointer-events: none;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Dark mode adjustments */
.dark .grid-background {
  background-image: repeating-linear-gradient(
    to right,
    transparent,
    transparent calc(var(--column-width) - 1px),
    rgba(255, 255, 255, 0.1) calc(var(--column-width) - 1px),
    rgba(255, 255, 255, 0.1) var(--column-width)
  ) !important;
}
</style>
