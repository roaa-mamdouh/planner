import { ref } from 'vue'

// Error types
export const ErrorType = {
  VALIDATION: 'validation',
  API: 'api',
  NETWORK: 'network',
  AUTHORIZATION: 'authorization',
  NOT_FOUND: 'not_found',
  UNKNOWN: 'unknown'
}

// Create a global error store
const errors = ref([])
const isShowingError = ref(false)

export const useErrorHandler = () => {
  // Add a new error
  const addError = (error) => {
    const errorObject = normalizeError(error)
    errors.value.push({
      ...errorObject,
      id: Date.now(),
      timestamp: new Date()
    })
    showError()
  }

  // Remove an error by id
  const removeError = (errorId) => {
    errors.value = errors.value.filter(error => error.id !== errorId)
  }

  // Clear all errors
  const clearErrors = () => {
    errors.value = []
    isShowingError.value = false
  }

  // Show error toast/notification
  const showError = () => {
    isShowingError.value = true
    // Auto-hide after 5 seconds
    setTimeout(() => {
      isShowingError.value = false
    }, 5000)
  }

  // Normalize different error types into a consistent format
  const normalizeError = (error) => {
    // If it's already in our format, return as is
    if (error.type && error.message) {
      return error
    }

    // If it's a transformed Frappe error (from useWorkloadManager), handle it directly
    if (error.exc_type || error.exception) {
      return {
        type: ErrorType.API,
        message: error.message || 'An unexpected error occurred',
        details: {
          error: error.exception || 'Unknown error',
          exc_type: error.exc_type || 'ServerError',
          data: error.data || null
        }
      }
    }

    // Handle API errors
    if (error.response) {
      const status = error.response.status
      const errorData = error.response.data || {}
      
      // Authentication errors
      if (status === 401 || status === 403) {
        return {
          type: ErrorType.AUTHORIZATION,
          message: 'You do not have permission to perform this action',
          details: errorData.message || errorData._error_message
        }
      }

      // Not found errors
      if (status === 404) {
        return {
          type: ErrorType.NOT_FOUND,
          message: 'The requested resource was not found',
          details: errorData.message || errorData._error_message
        }
      }

      // Validation errors from backend
      if (status === 400) {
        return {
          type: ErrorType.VALIDATION,
          message: 'Please check your input',
          details: errorData.errors || errorData.message || errorData._error_message
        }
      }

      // Server errors
      if (status >= 500) {
        // Handle Frappe error format
        const message = errorData._error_message || errorData.message || 'An unexpected server error occurred'
        const errorDetails = {
          error: errorData.error || errorData.exception || 'Unknown error',
          exc_type: 'ServerError',
          traceback: errorData.traceback,
          data: errorData.data // Include fallback data if available
        }

        // Log error details for debugging
        console.error('Server Error:', {
          message,
          details: errorDetails,
          rawError: errorData
        })

        return {
          type: ErrorType.API,
          message,
          details: errorDetails,
          // Include any fallback/recovery data
          fallback: errorData.data || null
        }
      }
    }

    // Network errors
    if (error.message === 'Network Error') {
      return {
        type: ErrorType.NETWORK,
        message: 'Unable to connect to the server',
        details: 'Please check your internet connection'
      }
    }

    // Default unknown error
    return {
      type: ErrorType.UNKNOWN,
      message: error.message || 'An unexpected error occurred',
      details: error.stack
    }
  }

  // Handle form validation errors
  const handleValidationErrors = (validationResult) => {
    if (!validationResult.valid) {
      addError({
        type: ErrorType.VALIDATION,
        message: 'Please fix the following errors:',
        details: validationResult.errors
      })
      return false
    }
    return true
  }

  // Handle API errors
  const handleApiError = async (promise) => {
    try {
      return await promise
    } catch (error) {
      addError(error)
      throw error
    }
  }

  // Get user-friendly error message
  const getErrorMessage = (error) => {
    const normalizedError = normalizeError(error)
    
    switch (normalizedError.type) {
      case ErrorType.VALIDATION:
        if (typeof normalizedError.details === 'object') {
          return Object.entries(normalizedError.details)
            .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
            .join('\n')
        }
        return normalizedError.message
      
      case ErrorType.AUTHORIZATION:
        return 'You do not have permission to perform this action. Please log in or contact your administrator.'
      
      case ErrorType.NOT_FOUND:
        return 'The requested resource could not be found. It may have been moved or deleted.'
      
      case ErrorType.NETWORK:
        return 'Unable to connect to the server. Please check your internet connection and try again.'
      
      default:
        return normalizedError.message || 'An unexpected error occurred. Please try again.'
    }
  }

  return {
    errors,
    isShowingError,
    addError,
    removeError,
    clearErrors,
    handleValidationErrors,
    handleApiError,
    getErrorMessage
  }
}

// Example usage:
/*
const { handleApiError, handleValidationErrors } = useErrorHandler()

// Handling API calls
const fetchData = async () => {
  return handleApiError(async () => {
    const response = await api.get('/data')
    return response.data
  })
}

// Handling form validation
const submitForm = async (formData) => {
  const validationResult = validateForm(formData)
  if (!handleValidationErrors(validationResult)) {
    return
  }
  
  // Proceed with form submission
  await handleApiError(async () => {
    await api.post('/submit', formData)
  })
}
*/
