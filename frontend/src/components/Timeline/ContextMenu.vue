<template>
  <div 
    v-if="visible"
    class="context-menu fixed bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded shadow-lg z-50"
    :style="{ top: `${position.y}px`, left: `${position.x}px` }"
    @click.stop
  >
    <ul class="py-1">
      <li 
        v-for="(item, index) in items" 
        :key="index" 
        class="px-4 py-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
        @click="selectItem(item)"
      >
        {{ item.label }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { defineEmits } from 'vue'

const props = defineProps({
  visible: Boolean,
  position: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  },
  items: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'close'])

const selectItem = (item) => {
  emit('select', item)
  emit('close')
}
</script>

<style scoped>
.context-menu {
  min-width: 150px;
  user-select: none;
}
</style>
