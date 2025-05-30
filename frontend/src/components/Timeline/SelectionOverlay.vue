<template>
  <div 
    v-if="isVisible"
    class="selection-overlay absolute pointer-events-none z-30"
    :style="overlayStyle"
  >
    <!-- Selection rectangle -->
    <div class="selection-rect border-2 border-blue-500 bg-blue-100/20 dark:bg-blue-900/20 rounded">
      <!-- Selection info -->
      <div 
        v-if="showInfo"
        class="selection-info absolute -top-8 left-0 bg-blue-600 text-white text-xs px-2 py-1 rounded whitespace-nowrap"
      >
        {{ selectionInfo }}
      </div>
    </div>
    
    <!-- Multi-select indicators -->
    <div 
      v-for="(item, index) in selectedItems"
      :key="index"
      class="selected-item-indicator absolute border-2 border-blue-400 bg-blue-200/30 dark:bg-blue-800/30 rounded"
      :style="getItemStyle(item)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  startPosition: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  },
  endPosition: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  },
  selectedItems: {
    type: Array,
    default: () => []
  },
  showInfo: {
    type: Boolean,
    default: true
  },
  containerOffset: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  }
})

// Computed properties
const overlayStyle = computed(() => {
  if (!props.isVisible) return {}
  
  const startX = Math.min(props.startPosition.x, props.endPosition.x) - props.containerOffset.x
  const startY = Math.min(props.startPosition.y, props.endPosition.y) - props.containerOffset.y
  const width = Math.abs(props.endPosition.x - props.startPosition.x)
  const height = Math.abs(props.endPosition.y - props.startPosition.y)
  
  return {
    left: `${startX}px`,
    top: `${startY}px`,
    width: `${width}px`,
    height: `${height}px`
  }
})

const selectionInfo = computed(() => {
  const count = props.selectedItems.length
  if (count === 0) return 'Selecting...'
  if (count === 1) return '1 item selected'
  return `${count} items selected`
})

// Methods
const getItemStyle = (item) => {
  return {
    left: `${item.x - props.containerOffset.x}px`,
    top: `${item.y - props.containerOffset.y}px`,
    width: `${item.width}px`,
    height: `${item.height}px`
  }
}
</script>

<style scoped>
.selection-overlay {
  animation: fadeIn 0.1s ease-out;
}

.selection-rect {
  width: 100%;
  height: 100%;
  animation: pulse 0.2s ease-out;
}

.selected-item-indicator {
  animation: highlight 0.3s ease-out;
}

.selection-info {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes highlight {
  0% {
    transform: scale(1.05);
    opacity: 0.5;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .selection-info {
    font-size: 0.625rem;
    padding: 0.25rem 0.5rem;
  }
}
</style>
