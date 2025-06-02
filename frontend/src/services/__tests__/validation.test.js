import { describe, it, expect } from 'vitest'
import { useValidation } from '../validation'

describe('useValidation', () => {
  const { validateField, validateForm, validateTask, rules } = useValidation()

  describe('Field Validation', () => {
    it('should validate required fields', () => {
      expect(validateField('', ['required'])).toEqual({
        valid: false,
        errors: ['This field is required']
      })

      expect(validateField('test', ['required'])).toEqual({
        valid: true,
        errors: []
      })
    })

    it('should validate minimum length', () => {
      const minLength3 = { rule: 'minLength', value: 3 }
      
      expect(validateField('ab', [minLength3])).toEqual({
        valid: false,
        errors: ['Must be at least 3 characters']
      })

      expect(validateField('abc', [minLength3])).toEqual({
        valid: true,
        errors: []
      })
    })

    it('should validate maximum length', () => {
      const maxLength5 = { rule: 'maxLength', value: 5 }
      
      expect(validateField('123456', [maxLength5])).toEqual({
        valid: false,
        errors: ['Must be no more than 5 characters']
      })

      expect(validateField('12345', [maxLength5])).toEqual({
        valid: true,
        errors: []
      })
    })

    it('should validate date format', () => {
      expect(validateField('2023-12-01', ['date'])).toEqual({
        valid: true,
        errors: []
      })

      expect(validateField('2023/12/01', ['date'])).toEqual({
        valid: false,
        errors: ['Must be a valid date in YYYY-MM-DD format']
      })
    })

    it('should validate time format', () => {
      expect(validateField('13:45', ['time'])).toEqual({
        valid: true,
        errors: []
      })

      expect(validateField('25:00', ['time'])).toEqual({
        valid: false,
        errors: ['Must be a valid time in HH:MM format']
      })
    })

    it('should validate email format', () => {
      expect(validateField('test@example.com', ['email'])).toEqual({
        valid: true,
        errors: []
      })

      expect(validateField('invalid-email', ['email'])).toEqual({
        valid: false,
        errors: ['Must be a valid email address']
      })
    })
  })

  describe('Form Validation', () => {
    it('should validate multiple fields in a form', () => {
      const formData = {
        name: 'John',
        email: 'invalid-email',
        age: ''
      }

      const validationSchema = {
        name: ['required', { rule: 'minLength', value: 2 }],
        email: ['required', 'email'],
        age: ['required']
      }

      const result = validateForm(formData, validationSchema)
      
      expect(result).toEqual({
        valid: false,
        errors: {
          email: ['Must be a valid email address'],
          age: ['This field is required']
        }
      })
    })
  })

  describe('Task Validation', () => {
    it('should validate a complete task object', () => {
      const validTask = {
        title: 'New Task',
        description: 'Task description',
        start_date: '2023-12-01',
        end_date: '2023-12-02',
        assigned_to: 'user@example.com',
        priority: 'high'
      }

      expect(validateTask(validTask)).toEqual({
        valid: true,
        errors: {}
      })
    })

    it('should validate task date ranges', () => {
      const invalidTask = {
        title: 'New Task',
        description: 'Task description',
        start_date: '2023-12-02',
        end_date: '2023-12-01', // End date before start date
        assigned_to: 'user@example.com',
        priority: 'high'
      }

      const result = validateTask(invalidTask)
      expect(result.valid).toBe(false)
      expect(result.errors.end_date).toContain('End date must be after start date')
    })

    it('should validate required task fields', () => {
      const incompleteTask = {
        description: 'Task description',
        start_date: '2023-12-01'
      }

      const result = validateTask(incompleteTask)
      expect(result.valid).toBe(false)
      expect(result.errors).toHaveProperty('title')
      expect(result.errors).toHaveProperty('end_date')
      expect(result.errors).toHaveProperty('assigned_to')
      expect(result.errors).toHaveProperty('priority')
    })
  })
})
