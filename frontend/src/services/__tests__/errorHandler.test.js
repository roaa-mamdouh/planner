import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useErrorHandler, ErrorType } from '../errorHandler'

describe('useErrorHandler', () => {
  let errorHandler

  beforeEach(() => {
    vi.useFakeTimers()
    errorHandler = useErrorHandler()
  })

  describe('Error Management', () => {
    it('should add and remove errors', () => {
      // Add error
      errorHandler.addError({
        type: ErrorType.VALIDATION,
        message: 'Test error'
      })

      expect(errorHandler.errors.value).toHaveLength(1)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.VALIDATION,
        message: 'Test error'
      })

      // Remove error
      const errorId = errorHandler.errors.value[0].id
      errorHandler.removeError(errorId)
      expect(errorHandler.errors.value).toHaveLength(0)
    })

    it('should clear all errors', () => {
      // Add multiple errors
      errorHandler.addError({ type: ErrorType.VALIDATION, message: 'Error 1' })
      errorHandler.addError({ type: ErrorType.API, message: 'Error 2' })
      
      expect(errorHandler.errors.value).toHaveLength(2)
      
      // Clear errors
      errorHandler.clearErrors()
      expect(errorHandler.errors.value).toHaveLength(0)
      expect(errorHandler.isShowingError.value).toBe(false)
    })

    it('should auto-hide errors after timeout', () => {
      errorHandler.addError({ type: ErrorType.VALIDATION, message: 'Test error' })
      expect(errorHandler.isShowingError.value).toBe(true)

      // Fast-forward 5 seconds
      vi.advanceTimersByTime(5000)
      expect(errorHandler.isShowingError.value).toBe(false)
    })
  })

  describe('Error Normalization', () => {
    it('should normalize API errors', () => {
      const apiError = {
        response: {
          status: 400,
          data: {
            message: 'Validation failed',
            errors: {
              field1: ['Invalid input']
            }
          }
        }
      }

      errorHandler.addError(apiError)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.VALIDATION,
        message: 'Please check your input',
        details: {
          field1: ['Invalid input']
        }
      })
    })

    it('should handle Frappe-style errors', () => {
      const frappeError = {
        exc_type: 'ValidationError',
        exception: 'Invalid data',
        message: 'Validation failed',
        data: { field1: 'Required' }
      }

      errorHandler.addError(frappeError)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.API,
        message: 'Validation failed',
        details: {
          error: 'Invalid data',
          exc_type: 'ValidationError',
          data: { field1: 'Required' }
        }
      })
    })

    it('should handle missing exc_type in Frappe errors', () => {
      const frappeError = {
        exception: 'Invalid data',
        message: 'Validation failed',
        data: { field1: 'Required' }
      }

      errorHandler.addError(frappeError)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.API,
        message: 'Validation failed',
        details: {
          error: 'Invalid data',
          exc_type: 'ServerError', // Default exc_type
          data: { field1: 'Required' }
        }
      })
    })

    it('should normalize authorization errors', () => {
      const authError = {
        response: {
          status: 401,
          data: {
            message: 'Unauthorized'
          }
        }
      }

      errorHandler.addError(authError)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.AUTHORIZATION,
        message: 'You do not have permission to perform this action'
      })
    })

    it('should normalize network errors', () => {
      const networkError = new Error('Network Error')
      
      errorHandler.addError(networkError)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.NETWORK,
        message: 'Unable to connect to the server'
      })
    })

    it('should handle unknown errors', () => {
      const unknownError = new Error('Something went wrong')
      
      errorHandler.addError(unknownError)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.UNKNOWN,
        message: 'Something went wrong'
      })
    })
  })

  describe('Validation Error Handling', () => {
    it('should handle validation errors', () => {
      const validationResult = {
        valid: false,
        errors: {
          field1: ['Required field'],
          field2: ['Invalid format']
        }
      }

      const result = errorHandler.handleValidationErrors(validationResult)
      expect(result).toBe(false)
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.VALIDATION,
        message: 'Please fix the following errors:',
        details: validationResult.errors
      })
    })

    it('should return true for valid validation results', () => {
      const validationResult = {
        valid: true,
        errors: {}
      }

      const result = errorHandler.handleValidationErrors(validationResult)
      expect(result).toBe(true)
      expect(errorHandler.errors.value).toHaveLength(0)
    })
  })

  describe('API Error Handling', () => {
    it('should handle API errors', async () => {
      const apiError = new Error('API Error')
      apiError.response = {
        status: 500,
        data: { message: 'Server error' }
      }

      const promise = Promise.reject(apiError)
      
      await expect(errorHandler.handleApiError(promise)).rejects.toThrow()
      expect(errorHandler.errors.value[0]).toMatchObject({
        type: ErrorType.API,
        message: 'An unexpected error occurred'
      })
    })

    it('should pass through successful responses', async () => {
      const successPromise = Promise.resolve({ data: 'success' })
      
      const result = await errorHandler.handleApiError(successPromise)
      expect(result).toEqual({ data: 'success' })
      expect(errorHandler.errors.value).toHaveLength(0)
    })
  })

  describe('Error Message Formatting', () => {
    it('should format validation errors', () => {
      const error = {
        type: ErrorType.VALIDATION,
        message: 'Validation failed',
        details: {
          field1: ['Required'],
          field2: ['Invalid format']
        }
      }

      const message = errorHandler.getErrorMessage(error)
      expect(message).toBe('field1: Required\nfield2: Invalid format')
    })

    it('should format authorization errors', () => {
      const error = {
        type: ErrorType.AUTHORIZATION,
        message: 'Unauthorized'
      }

      const message = errorHandler.getErrorMessage(error)
      expect(message).toBe('You do not have permission to perform this action. Please log in or contact your administrator.')
    })

    it('should format network errors', () => {
      const error = {
        type: ErrorType.NETWORK,
        message: 'Network Error'
      }

      const message = errorHandler.getErrorMessage(error)
      expect(message).toBe('Unable to connect to the server. Please check your internet connection and try again.')
    })
  })
})
