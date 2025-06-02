// Validation Rules
const rules = {
  required: (value) => ({
    valid: value !== undefined && value !== null && value !== '',
    message: 'This field is required'
  }),

  minLength: (min) => (value) => ({
    valid: value && value.length >= min,
    message: `Must be at least ${min} characters`
  }),

  maxLength: (max) => (value) => ({
    valid: !value || value.length <= max,
    message: `Must be no more than ${max} characters`
  }),

  date: (value) => {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/
    const valid = dateRegex.test(value)
    const date = new Date(value)
    return {
      valid: valid && !isNaN(date),
      message: 'Must be a valid date in YYYY-MM-DD format'
    }
  },

  time: (value) => {
    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/
    return {
      valid: timeRegex.test(value),
      message: 'Must be a valid time in HH:MM format'
    }
  },

  dateRange: (startDate, endDate) => {
    if (!startDate || !endDate) return { valid: true }
    const start = new Date(startDate)
    const end = new Date(endDate)
    return {
      valid: end >= start,
      message: 'End date must be after start date'
    }
  },

  email: (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return {
      valid: !value || emailRegex.test(value),
      message: 'Must be a valid email address'
    }
  }
}

// Validation Service
export const useValidation = () => {
  // Validate a single field
  const validateField = (value, fieldRules) => {
    const errors = []

    for (const rule of fieldRules) {
      let validationResult

      if (typeof rule === 'function') {
        // Custom validation function
        validationResult = rule(value)
      } else if (typeof rule === 'string' && rules[rule]) {
        // Predefined rule
        validationResult = rules[rule](value)
      } else if (typeof rule === 'object' && rule.rule && rules[rule.rule]) {
        // Predefined rule with parameters
        validationResult = rules[rule.rule](rule.value)(value)
      }

      if (validationResult && !validationResult.valid) {
        errors.push(validationResult.message)
      }
    }

    return {
      valid: errors.length === 0,
      errors
    }
  }

  // Validate an entire form
  const validateForm = (formData, validationSchema) => {
    const errors = {}
    let isValid = true

    for (const [field, fieldRules] of Object.entries(validationSchema)) {
      const result = validateField(formData[field], fieldRules)
      if (!result.valid) {
        errors[field] = result.errors
        isValid = false
      }
    }

    return {
      valid: isValid,
      errors
    }
  }

  // Task-specific validation schema
  const taskValidationSchema = {
    title: ['required', { rule: 'minLength', value: 3 }],
    description: [{ rule: 'maxLength', value: 500 }],
    start_date: ['required', 'date'],
    end_date: ['required', 'date'],
    assigned_to: ['required'],
    priority: ['required']
  }

  // Validate task form
  const validateTask = (taskData) => {
    const baseValidation = validateForm(taskData, taskValidationSchema)
    
    // Additional validation for date range
    if (taskData.start_date && taskData.end_date) {
      const dateRangeValidation = rules.dateRange(taskData.start_date, taskData.end_date)
      if (!dateRangeValidation.valid) {
        return {
          valid: false,
          errors: {
            ...baseValidation.errors,
            end_date: [...(baseValidation.errors.end_date || []), dateRangeValidation.message]
          }
        }
      }
    }

    return baseValidation
  }

  return {
    validateField,
    validateForm,
    validateTask,
    rules
  }
}

// Example usage:
/*
const { validateTask } = useValidation()

const taskData = {
  title: 'New Task',
  description: 'Task description',
  start_date: '2023-12-01',
  end_date: '2023-12-02',
  assigned_to: 'user@example.com',
  priority: 'high'
}

const validation = validateTask(taskData)
if (!validation.valid) {
  console.error('Validation errors:', validation.errors)
} else {
  // Proceed with task creation/update
}
*/
