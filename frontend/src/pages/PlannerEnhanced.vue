<template>
    <Layout :breadcrumbs="breadcrumbs">
        <div class="mx-auto px-4 lg:px-8 max-w-[2000px] h-screen flex flex-col">
            <!-- Enhanced Timeline V2 Component -->
            <TimelineV2 />
        </div>
    </Layout>
</template>

<script setup>
import Layout from "@/pages/shared/Layout.vue"
import { ref } from "vue"
import { useRoute } from 'vue-router'
import TimelineV2 from "@/components/Timeline/TimelineV2.vue"

const route = useRoute()
const dashboardName = ref(route.params.dashboardName)

// Breadcrumbs
const breadcrumbs = [
    {
        label: 'Dashboard',
        route: { name: 'Dashboard' }
    },
    {
        label: dashboardName.value,
        route: { name: 'PlannerEnhanced' }
    }
]
</script>

<style scoped>
/* Styles are now handled by TimelineV2 component */
</style>
