<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-96 max-w-full p-6">
      <header class="mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Resolve Conflict</h3>
      </header>
      <div class="mb-6">
        <p class="mb-4 text-gray-600 dark:text-gray-300">There is a conflict with the selected task. Please choose how to resolve it.</p>
        <div class="flex flex-col space-y-3">
          <Button variant="primary" @click="resolve('overwrite')">Overwrite</Button>
          <Button variant="secondary" @click="resolve('merge')">Merge</Button>
          <Button variant="ghost" @click="close">Cancel</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineEmits } from 'vue'
import { Button } from 'frappe-ui'

const props = defineProps({
  visible: Boolean
})

const emit = defineEmits(['close', 'resolve'])

const close = () => {
  emit('close')
}

const resolve = (action) => {
  emit('resolve', action)
  close()
}
</script>

<style scoped>
/* Add any styles if needed */
</style>
