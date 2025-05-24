import { ref, watch } from 'vue'

const isDarkMode = ref(false)

// Initialize dark mode from localStorage or system preference
const initializeDarkMode = () => {
  const stored = localStorage.getItem('darkMode')
  if (stored !== null) {
    isDarkMode.value = JSON.parse(stored)
  } else {
    // Check system preference
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  
  // Apply initial theme
  updateTheme()
}

// Update the theme by adding/removing dark class from html element
const updateTheme = () => {
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Watch for changes and persist to localStorage
watch(isDarkMode, (newValue) => {
  localStorage.setItem('darkMode', JSON.stringify(newValue))
  updateTheme()
})

export function useDarkMode() {
  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value
  }

  return {
    isDarkMode,
    toggleDarkMode,
    initializeDarkMode
  }
}
