import './index.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from "./router";
import App from './App.vue'
import { useDarkMode } from './composables/useDarkMode'

import { setConfig, frappeRequest, resourcesPlugin, 
    Button, 
    Breadcrumbs,
    Avatar,  
    FormControl,
    FeatherIcon,
    Select,
    Dropdown,
    Dialog,
    Autocomplete,
    ErrorMessage,
    TextInput
} from 'frappe-ui'
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';

// Initialize dark mode
const { initializeDarkMode } = useDarkMode()
initializeDarkMode()

// Create Pinia store
const pinia = createPinia()

const app = createApp(App);
setConfig('resourceFetcher', frappeRequest)
app.use(router)
app.use(pinia)
app.use(resourcesPlugin)
app.component('Button', Button)
app.component('Breadcrumbs', Breadcrumbs)
app.component('Avatar', Avatar)
app.component('FormControl', FormControl)
app.component('FeatherIcon', FeatherIcon)
app.component('Select', Select)
app.component('Dropdown', Dropdown)
app.component('Dialog', Dialog)
app.component('Autocomplete', Autocomplete)
app.component('ErrorMessage', ErrorMessage)
app.component('TextInput', TextInput)
app.component('VueDatePicker', VueDatePicker);
app.mount("#app");
