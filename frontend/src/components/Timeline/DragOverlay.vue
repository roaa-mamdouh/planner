<template>
  <div 
    v-if="visible"
    class="drag-overlay fixed top-0 left-0 w-full h-full pointer-events-none z-50"
  >
    <div 
      class="drag-preview bg-blue-500 bg-opacity-50 rounded shadow-lg p-2 text-white"
      :style="previewStyle"
    >
      {{ label }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  position: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  },
  label: {
    type: String,
    default: ''
  }
})

const previewStyle = computed(() => ({
  position: 'fixed',
  top: `${props.position.y}px`,
  left: `${props.position.x}px`,
  transform: 'translate(-50%, -50%)',
  pointerEvents: 'none',
  userSelect: 'none'
}))
</script>

<style scoped>
.drag-overlay {
  user-select: none;
}

.drag-preview {
  min-width: 100px;
  text-align: center;
  font-weight: 600;
  font-size: 0.875rem;
}
</style>
