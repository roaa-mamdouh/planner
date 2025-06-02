import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { useDragAndDrop } from '@/composables/useDragAndDrop'
import WorkloadViewEnhanced from '@/components/Workload/WorkloadViewEnhanced.vue'

// Mock frappe-ui resource
vi.mock('frappe-ui', () => ({
  createResource: vi.fn(() => ({
    submit: vi.fn()
  }))
}))

describe('Drag and Drop Critical Path Tests', () => {
  let wrapper
  
  const mockTasks = [
    {
      id: 'task-1',
      title: 'Test Task 1',
      assignee: 'user-1',
      startDate: '2023-12-01',
      endDate: '2023-12-02',
      duration: 8,
      isScheduled: true
    }
  ]

  const mockAssignees = [
    {
      id: 'user-1',
      name: 'Test User',
      utilization: 50
    }
  ]

  beforeEach(() => {
    wrapper = mount(WorkloadViewEnhanced, {
      props: {
        tasks: mockTasks,
        assignees: mockAssignees,
        loading: false
      },
      global: {
        stubs: ['FeatherIcon', 'Avatar', 'Button']
      }
    })
  })

  describe('Task Dragging', () => {
    it('initiates drag with correct task data', async () => {
      const taskElement = wrapper.find('.task-block')
      const dragStartEvent = new Event('dragstart')
      dragStartEvent.dataTransfer = {
        setData: vi.fn(),
        effectAllowed: null
      }

      await taskElement.trigger('dragstart', dragStartEvent)

      expect(dragStartEvent.dataTransfer.setData).toHaveBeenCalledWith(
        'application/json',
        JSON.stringify(mockTasks[0])
      )
      expect(dragStartEvent.dataTransfer.effectAllowed).toBe('move')
    })

    it('shows drop target indicator when dragging over valid zone', async () => {
      const dropZone = wrapper.find('.timeline-slot')
      await dropZone.trigger('dragover')
      expect(dropZone.classes()).toContain('drop-zone-active')
    })

    it('emits task move event on successful drop', async () => {
      const dropZone = wrapper.find('.timeline-slot')
      const dropEvent = new Event('drop')
      dropEvent.dataTransfer = {
        getData: () => JSON.stringify(mockTasks[0])
      }

      await dropZone.trigger('drop', dropEvent)

      expect(wrapper.emitted('taskMove')).toBeTruthy()
      const emittedEvent = wrapper.emitted('taskMove')[0][0]
      expect(emittedEvent).toHaveProperty('taskId', 'task-1')
    })
  })

  describe('Task Updates', () => {
    it('updates task position on drop', async () => {
      const { moveTaskResource } = useDragAndDrop()
      
      const dropData = {
        taskId: 'task-1',
        assigneeId: 'user-2',
        startDate: '2023-12-03',
        endDate: '2023-12-04'
      }

      await wrapper.vm.handleDrop(
        { preventDefault: vi.fn(), dataTransfer: { getData: () => JSON.stringify(mockTasks[0]) } },
        dropData.assigneeId,
        dropData.startDate
      )

      expect(moveTaskResource.submit).toHaveBeenCalledWith(expect.objectContaining({
        task_id: dropData.taskId,
        assignee_id: dropData.assigneeId,
        start_date: dropData.startDate
      }))
    })

    it('handles unscheduled task drops', async () => {
      const unscheduledZone = wrapper.find('.unscheduled-tasks')
      const dropEvent = new Event('drop')
      dropEvent.dataTransfer = {
        getData: () => JSON.stringify(mockTasks[0])
      }

      await unscheduledZone.trigger('drop', dropEvent)

      expect(wrapper.emitted('taskMove')).toBeTruthy()
      const emittedEvent = wrapper.emitted('taskMove')[0][0]
      expect(emittedEvent.startDate).toBeNull()
      expect(emittedEvent.endDate).toBeNull()
    })
  })

  describe('Error Handling', () => {
    it('handles drag and drop errors gracefully', async () => {
      const { moveTaskResource } = useDragAndDrop()
      moveTaskResource.submit.mockRejectedValueOnce(new Error('API Error'))

      const dropZone = wrapper.find('.timeline-slot')
      const dropEvent = new Event('drop')
      dropEvent.dataTransfer = {
        getData: () => JSON.stringify(mockTasks[0])
      }

      await dropZone.trigger('drop', dropEvent)

      // Verify error is handled and UI remains stable
      expect(wrapper.find('.error-message').exists()).toBe(false)
      expect(wrapper.find('.task-block').exists()).toBe(true)
    })
  })

  describe('Visual Feedback', () => {
    it('applies correct styles during drag operations', async () => {
      const taskElement = wrapper.find('.task-block')
      
      // Start drag
      await taskElement.trigger('dragstart', {
        dataTransfer: { setData: vi.fn(), effectAllowed: null }
      })
      expect(taskElement.classes()).toContain('dragging')

      // End drag
      await taskElement.trigger('dragend')
      expect(taskElement.classes()).not.toContain('dragging')
    })

    it('shows correct drop target indicators', async () => {
      const dropZone = wrapper.find('.timeline-slot')
      
      // Drag over
      await dropZone.trigger('dragover')
      expect(dropZone.classes()).toContain('drop-zone-active')

      // Drag leave
      await dropZone.trigger('dragleave')
      expect(dropZone.classes()).not.toContain('drop-zone-active')
    })
  })
})
