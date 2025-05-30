<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-96 max-w-full p-6">
      <header class="mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Edit Task</h3>
      </header>
      <form @submit.prevent="submit">
        <div class="mb-4">
          <label class="block text-sm font-medium mb-1" for="taskName">Task Name</label>
          <input
            id="taskName"
            v-model="task.name"
            type="text"
            class="w-full border border-gray-300 rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            required
          />
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium mb-1" for="taskDescription">Description</label>
          <textarea
            id="taskDescription"
            v-model="task.description"
            class="w-full border border-gray-300 rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            rows="4"
          ></textarea>
        </div>
        <!-- Add more fields as needed -->
        <div class="flex justify-end space-x-2">
          <button type="button" class="btn btn-ghost" @click="close">Cancel</button>
          <button type="submit" class="btn btn-primary">Save</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  taskData: Object
})

const emit = defineEmits(['close', 'save'])

const task = ref({})

watch(() => props.taskData, (newVal) => {
  task.value = { ...newVal }
}, { immediate: true })

const close = () => {
  emit('close')
}

const submit = () => {
  emit('save', task.value)
  close()
}
</script>
