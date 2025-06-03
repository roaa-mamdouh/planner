<template>
    <form @submit.prevent="onSubmit">
        <div class="flex flex-col">
            <div class="mb-3">

                <label class="block text-xs text-gray-600 mb-2">Assigned to</label>

                <div class="flex justify-start items-center">



                    <Avatar :shape="'circle'" :label="assignee.owner" :image="assignee.image" size="2xl"
                        v-for="assignee in docinfo.value?.assignments || []" :key="assignee.owner" />
                    <Button :variant="'subtle'" theme="gray" size="lg" label="Button" :loading="false"
                        :loadingText="null" :disabled="false" :link="null" icon="user-plus" class="rounded-full"
                        type="button" @click="addAssigneePopup = true">
                    </Button>


                    <Dialog v-model="addAssigneePopup">
                        <template #body-title>
                            <p class="text-base">Assigned to</p>
                        </template>
                        <template #body-content>
                            <Autocomplete :options="employeesList" v-model="employees" placeholder="Select people"
                                :multiple="false" class="mb-5" @update:modelValue="onSelectEmployee" />
                            <div class="flex flex-col gap-3">
                                <div class="flex justify-between items-center" v-for="assignee in docinfo.value?.assignments || []" :key="assignee.owner">
                                    <div class="flex justify-start items-center gap-3">
                                        <Avatar :shape="'circle'" :image="assignee.image" :label="assignee.owner"
                                            size="2xl" />
                                        <span>{{ assignee.fullname }}</span>
                                    </div>
                                    <Button :variant="'outline'" theme="gray" size="sm" label="Button" icon="x"
                                        @click="unselectEmployee(assignee.owner)">
                                    </Button>
                                </div>
                            </div>
                        </template>
                    </Dialog>
                </div>
            </div>
            <div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Subject</label>
                    <TextInput :type="'text'" size="sm" variant="subtle" placeholder="Subject" :disabled="false"
                        v-model="values.subject"
                        :class="[errors.subject ? 'border-red-400 hover:border-red-400 hover:bg-grey-200 focus:border-red-500 focus-visible:ring-red-400' : '']" />
                    <ErrorMessage v-if="errors.subject" :message="errors.subject" class="mt-1" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Project</label>
                    <TextInput :type="'text'" size="sm" variant="subtle" placeholder="Project" :disabled="false"
                        v-model="values.project" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Elevator</label>
                    <TextInput :type="'text'" size="sm" variant="subtle" placeholder="Elevator" :disabled="false"
                        v-model="values.elevator" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Type</label>
                    <TextInputAutocomplete v-model="values.type" placeholder="Type" :options="typeOptions" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Status</label>
                    <Select :options="['Open', 'Working', 'Pending Review', 'Overdue', 'Completed', 'Cancelled']"
                        v-model="values.status" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Priority</label>
                    <Select :options="['Low', 'Medium', 'High']" v-model="values.priority" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Parent Task</label>
                    <TextInputAutocomplete v-model="values.parent_task" placeholder="Parent Task" :options="parentTaskOptions"
                        value-by="parent_name" label-by="name" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Expected Start Date</label>
                    <VueDatePicker placeholder="mm/dd/yyyy" v-model="values.exp_start_date" class="mb-3"
                        :week-numbers="{ type: 'iso' }" autoApply :closeOnAutoApply="true" :clearable="false"
                        :enable-time-picker="false">
                        <template #dp-input="{ value }">
                            <input type="text" :value="value"
                                class="text-base relative font-['InterVar'] rounded h-7 py-1.5 pl-2 pr-2 border border-gray-100 bg-gray-100 placeholder-gray-500 hover:border-gray-200 hover:bg-gray-200 focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors w-full"
                                placeholder="mm/dd/yyyy"
                                :class="[errors.exp_start_date ? 'border-red-400 hover:border-red-400 hover:bg-grey-200 focus:border-red-500 focus-visible:ring-red-400' : '']" />
                            <FeatherIcon name="calendar" class="w-4 h-4 datepicker-icon text-gray-600" />
                            <ErrorMessage v-if="errors.exp_start_date" :message="errors.exp_start_date" class="mt-1" />
                        </template>
                    </VueDatePicker>
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Expected End Date</label>
                    <VueDatePicker placeholder="mm/dd/yyyy" v-model="values.exp_end_date" class="mb-3"
                        :week-numbers="{ type: 'iso' }" autoApply :closeOnAutoApply="true" :clearable="false"
                        :enable-time-picker="false">
                        <template #dp-input="{ value }">
                            <input type="text" :value="value"
                                class="text-base relative font-['InterVar'] rounded h-7 py-1.5 pl-2 pr-2 border border-gray-100 bg-gray-100 placeholder-gray-500 hover:border-gray-200 hover:bg-gray-200 focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors w-full"
                                placeholder="mm/dd/yyyy"
                                :class="[errors.exp_end_date ? 'border-red-400 hover:border-red-400 hover:bg-grey-200 focus:border-red-500 focus-visible:ring-red-400' : '']" />
                            <FeatherIcon name="calendar" class="w-4 h-4 datepicker-icon text-gray-600" />
                            <ErrorMessage v-if="errors.exp_end_date" :message="errors.exp_end_date" class="mt-1" />
                        </template>
                    </VueDatePicker>
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Expected Time</label>
                    <TextInput :type="'number'" size="sm" variant="subtle" placeholder="Expected Time" :disabled="false"
                        v-model="values.expected_time"
                        :class="[errors.expected_time ? 'border-red-400 hover:border-red-400 hover:bg-grey-200 focus:border-red-500 focus-visible:ring-red-400' : '']" />
                    <ErrorMessage v-if="errors.expected_time" :message="errors.expected_time" class="mt-1" />
                </div>
                <div class="mb-3">
                    <label class="block text-xs text-gray-600 mb-2">Actual Time in Hours</label>
                    <TextInput :type="'number'" size="sm" variant="subtle" placeholder="Actual Time in Hours"
                        :disabled="false" v-model="values.actual_time"
                        :class="[errors.actual_time ? 'border-red-400 hover:border-red-400 hover:bg-grey-200 focus:border-red-500 focus-visible:ring-red-400' : '']" />
                    <ErrorMessage v-if="errors.actual_time" :message="errors.actual_time" class="mt-1" />
                </div>
            </div>
            <div class="flex justify-end mt-4">
                <button type="submit" class="btn btn-primary">
                    Save
                </button>
            </div>
        </div>
    </form>
</template>


<script setup>
import { ref, onMounted, inject, computed, defineProps, watch, defineEmits } from "vue";
import { createResource } from "frappe-ui";
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/yup';
import { object, string, number, date, array } from 'yup';
import { watchDebounced } from '@vueuse/core';
import { getURL } from '../../getURL.js'
import { useRoute } from 'vue-router';
import TextInputAutocomplete from '@/components/TextInputAutocomplete.vue';

// Props and emits
const props = defineProps({
    task: String,
    department: String
});

const emit = defineEmits(['update', 'close']);

// Form validation schema
const schema = toTypedSchema(
    object({
        subject: string().required('Subject is required'),
        project: string(),
        elevator: string(),
        type: string(),
        parent_task: string(),
        status: string().required('Status is required'),
        priority: string().required('Priority is required'),
        exp_start_date: date().required('Start date is required'),
        exp_end_date: date().required('End date is required'),
        expected_time: number().required('Expected time is required'),
        actual_time: number()
    })
);

// Form handling
const { handleSubmit, values, errors, resetForm } = useForm({
    validationSchema: schema,
    initialValues: {
        subject: '',
        project: '',
        elevator: '',
        type: '',
        parent_task: '',
        status: 'Open',
        priority: 'Medium',
        exp_start_date: null,
        exp_end_date: null,
        expected_time: 0,
        actual_time: 0
    }
});

// Form submission handler
const onSubmit = handleSubmit(async (values) => {
    console.log('Form submitted with values:', values);
    console.log('Task ID:', props.task);
    try {
        console.log('Submitting form with values:', values);
        // Exclude actual_time, parent_task, type, and elevator from updates as backend does not accept them
        const { actual_time, parent_task, type, elevator, project, subject, exp_end_date, exp_start_date, ...updates } = values;
        const resource = createResource({
            url: 'planner.api.update_task',
            params: {
                task_id: props.task,
                updates: updates
            },
            onSuccess: (response) => {
                console.log('Update successful:', response);
                emit('update', response);
                emit('close');
            }
        });
        
        await resource.submit();
    } catch (error) {
        console.error('Error updating task:', error);
    }
});

// State
const dataTask = ref(null);
const employees = ref(null);
const employeesList = ref([]);
const addAssigneePopup = ref(false);
const docinfo = ref({
    assignments: [],
    user_info: {}
});

// Options
const projectOptions = ref([
    { label: "TASK-2024-00004", value: "PROJ-0001" },
    { label: "TASK-2024-00005", value: "PROJ-0006" },
    { label: "TASK-2024-00008", value: "PROJ-0008" }
]);

const typeOptions = ref([
    { label: "Task", value: "Task" },
    { label: "Bug", value: "Bug" },
    { label: "Feature", value: "Feature" }
]);

const elevatorOptions = ref([
    { name: "Elevator 1", elevator: "Elevator 1 value" },
    { name: "Elevator 2", elevator: "Elevator 2 value" },
    { name: "Elevator 3", elevator: "Elevator 3 value" }
]);

const parentTaskOptions = ref([
    { name: "TASK-2024-00004", parent_name: "TASK-2024-00004 value" },
    { name: "TASK-2024-00005", parent_name: "TASK-2024-00005 value" },
    { name: "TASK-2024-00008", parent_name: "TASK-2024-00008 value" }
]);


const unselectEmployee = async (assignedperson) => {
    try {
        const resource = createResource({
            url: 'frappe.desk.form.assign_to.remove',
            params: {
                doctype: "Task",
                name: props.task,
                assign_to: assignedperson
            }
        });
        
        await resource.submit();
        
        if (docinfo.value?.assignments) {
            const index = docinfo.value.assignments.findIndex(a => a.owner === assignedperson);
            if (index !== -1) {
                docinfo.value.assignments.splice(index, 1);
            }
        }
    } catch (error) {
        console.error('Error removing assignee:', error);
    }
};

const onSelectEmployee = async (employee) => {
    try {
        const resource = createResource({
            url: 'frappe.desk.form.assign_to.add',
            params: {
                doctype: "Task",
                name: props.task,
                description: props.task,
                assign_to: [employee.value],
                bulk_assign: false
            }
        });
        
        await resource.submit();
        
        if (docinfo.value?.assignments) {
            docinfo.value.assignments.push({
                owner: employee.value,
                fullname: employee.label,
                image: employee.image
            });
        }
    } catch (error) {
        console.error('Error assigning employee:', error);
    }
};

const updateValue = async (field, value) => {
    try {
        const resource = createResource({
            url: 'planner.api.update_task',
            params: {
                task_id: props.task,
                updates: { [field]: value }
            }
        });
        await resource.submit();
    } catch (error) {
        console.error(`Error updating field ${field}:`, error);
    }
};

// Watch for form changes
watchDebounced(
    values,
    async (newValues) => {
        if (!dataTask.value) return;
        
        const fields = ['subject', 'project', 'status', 'priority', 'exp_start_date', 'exp_end_date'];
        for (const field of fields) {
            if (dataTask.value[field] !== newValues[field]) {
                await updateValue(field, newValues[field]);
                dataTask.value[field] = newValues[field];
            }
        }
    },
    { debounce: 2000, maxWait: 8000 }
);

// Initialize
onMounted(async () => {
    try {
        // Load employees
        const employeeResource = createResource({
            url: 'planner.api.get_workload_data',
            params: { department: props.department }
        });
        const employeesData = await employeeResource.submit();
        employeesList.value = (employeesData.assignees || []).map(emp => ({
            value: emp.id,
            label: emp.name,
            image: emp.image
        }));

        // Load task
        console.log('************Loading task:', props.task);   
        const taskResource = createResource({
            url: 'frappe.desk.form.load.getdoc',
            params: {
                doctype: "Task",
                name: props.task
            }
        });
        const taskData = await taskResource.submit();
        
        if (taskData?.docs?.[0]) {
            dataTask.value = taskData.docs[0];
            docinfo.value = taskData.docinfo;

            // Map task data to form fields
            const fields = {
                subject: 'subject',
                project: 'project',
                elevator: 'elevator',
                type: 'type',
                parent_task: 'parent_task',
                status: 'status',
                priority: 'priority',
                exp_start_date: 'exp_start_date',
                exp_end_date: 'exp_end_date',
                expected_time: 'expected_time',
                actual_time: 'actual_time'
            };

            const mappedValues = {};
            Object.entries(fields).forEach(([formField, taskField]) => {
                if (dataTask.value[taskField] !== undefined) {
                    mappedValues[formField] = dataTask.value[taskField];
                }
            });
            resetForm({ values: mappedValues });
        }
    } catch (error) {
        console.error('Error initializing form:', error);
    }
});

</script>
