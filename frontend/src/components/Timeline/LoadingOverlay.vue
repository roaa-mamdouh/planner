<template>
  <div class="loading-overlay fixed inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm flex items-center justify-center z-50">
    <div class="loading-content text-center">
      <!-- Spinner -->
      <div class="loading-spinner w-12 h-12 border-4 border-blue-200 dark:border-blue-800 border-t-blue-600 dark:border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
      
      <!-- Loading text -->
      <div class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        {{ title }}
      </div>
      
      <!-- Loading message -->
      <div class="text-sm text-gray-600 dark:text-gray-400">
        {{ message }}
      </div>
      
      <!-- Progress bar (if progress is provided) -->
      <div v-if="progress !== null" class="mt-4 w-64 mx-auto">
        <div class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
          <span>Progress</span>
          <span>{{ Math.round(progress) }}%</span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            class="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${Math.min(100, Math.max(0, progress))}%` }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Props
const props = defineProps({
  title: {
    type: String,
    default: 'Loading...'
  },
  message: {
    type: String,
    default: 'Please wait while we load your data'
  },
  progress: {
    type: Number,
    default: null
  }
})
</script>

<style scoped>
.loading-overlay {
  animation: fadeIn 0.3s ease-out;
}

.loading-content {
  animation: slideUp 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
