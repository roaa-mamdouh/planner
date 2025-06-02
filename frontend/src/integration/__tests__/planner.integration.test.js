import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PlannerEnhanced from '@/pages/PlannerEnhanced.vue'

describe('PlannerEnhanced Integration', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(PlannerEnhanced, {
      props: {
        // Provide necessary props or mocks
      },
      global: {
        stubs: ['FeatherIcon', 'Avatar', 'Button', 'TimelineViewRoster', 'TaskForm']
      }
    })
  })

  it('renders workload planner header', () => {
    expect(wrapper.text()).toContain('Workload Planner')
  })

  it('toggles analytics panel', async () => {
    const analyticsButton = wrapper.find('button:contains("Analytics")')
    expect(wrapper.vm.showCapacityAnalysis).toBe(false)
    await analyticsButton.trigger('click')
    expect(wrapper.vm.showCapacityAnalysis).toBe(true)
  })

  it('opens task form on task click', async () => {
    // Simulate task click event
    await wrapper.vm.handleTaskClick('task-1')
    expect(wrapper.vm.isTaskFormActive).toBe(true)
    expect(wrapper.vm.activeTask).toBe('task-1')
  })

  it('handles task move event', async () => {
    const moveData = {
      taskId: 'task-1',
      assigneeId: 'user-1',
      startDate: '2023-12-01',
      endDate: '2023-12-02'
    }
    await wrapper.vm.handleTaskMove(moveData)
    // Expect some state update or API call (mocked)
  })

  it('refreshes workload data', async () => {
    await wrapper.vm.refreshWorkloadData()
    expect(wrapper.vm.loading).toBe(false)
  })
})
