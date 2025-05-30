<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-96 max-w-full p-6">
      <header class="mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Bulk Actions</h3>
      </header>
      <div class="mb-6">
        <p class="mb-4 text-gray-600 dark:text-gray-300">Perform actions on multiple selected tasks.</p>
        <div class="flex flex-col space-y-3">
          <Button variant="primary" @click="performAction('assign')">Assign to User</Button>
          <Button variant="secondary" @click="performAction('change_status')">Change Status</Button>
          <Button variant="danger" @click="performAction('delete')">Delete Tasks</Button>
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

const emit = defineEmits(['close', 'action'])

const close = () => {
  emit('close')
}

const performAction = (action) => {
  emit('action', action)
  close()
}
</script>

<style scoped>
/* Add any styles if needed */
</style>
