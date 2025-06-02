import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TimelineViewRoster from '../Timeline/TimelineViewRoster.vue'

// Mock API calls and frappe-ui to avoid backend errors
vi.mock('frappe-ui', () => ({
  FeatherIcon: {
    template: '<svg></svg>'
  },
  usePageMeta: () => {},
  call: () => Promise.resolve({
    assignees: [],
    tasks: [],
    capacity_settings: {
      default_hours_per_day: 8,
      default_days_per_week: 5
    }
  })
}))

describe('TimelineViewRoster', () => {
  const mockProps = {
    assignees: [
      { id: 1, name: 'John Doe', role: 'Developer', utilization: 75 }
    ],
    tasks: [
      { 
        id: 1, 
        title: 'Task 1',
        isScheduled: false,
        assignee: null,
        duration: 8
      },
      {
        id: 2,
        title: 'Task 2',
        isScheduled: false,
        assignee: undefined,
        duration: 4
      },
      {
        id: 3,
        title: 'Task 3',
        isScheduled: false,
        assignee: 1,
        duration: 2
      }
    ],
    loading: true
  }

  it('applies loading class correctly', () => {
    const wrapper = mount(TimelineViewRoster, {
      props: mockProps
    })
    
    const timelineDiv = wrapper.find('.timeline-roster-view > div:nth-child(2) > div:nth-child(1) > div')
    expect(timelineDiv.classes()).toContain('animate-pulse')
    expect(timelineDiv.classes()).toContain('pointer-events-none')
  })

  it('filters unscheduled tasks correctly', () => {
    const wrapper = mount(TimelineViewRoster, {
      props: mockProps
    })
    
    const vm = wrapper.vm
    const unscheduledTasks = vm.unscheduledTasks
    
    expect(unscheduledTasks.length).toBe(2)
    expect(unscheduledTasks.map(t => t.id)).toEqual([1, 2])
  })

  it('forces BacklogPanel re-render when showBacklog changes', async () => {
    const wrapper = mount(TimelineViewRoster, {
      props: mockProps
    })
    
    const vm = wrapper.vm
    const oldKey = wrapper.findComponent({ name: 'BacklogPanel' }).props('key')
    
    await vm.$nextTick()
    vm.showBacklog = false
    await vm.$nextTick()
    vm.showBacklog = true
    await vm.$nextTick()
    
    const newKey = wrapper.findComponent({ name: 'BacklogPanel' }).props('key')
    expect(newKey).not.toBe(oldKey)
  })
})
