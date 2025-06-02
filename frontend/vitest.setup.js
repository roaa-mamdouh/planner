import { config } from '@vue/test-utils'
import { FeatherIcon } from 'frappe-ui'

// Mock Frappe UI components globally
config.global.components = {
  FeatherIcon,
  Button: {
    template: '<button><slot></slot></button>'
  },
  Avatar: {
    template: '<div class="avatar"><slot></slot></div>',
    props: ['image', 'label', 'size']
  }
}
