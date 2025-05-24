<template>
    <div class="wrapper">
        <nav class="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border transition-colors duration-300">
            <div class="mx-auto px-4 lg:px-8 max-w-[1800px]">
                <div class="flex justify-end items-center h-12 gap-3">
                    <Button 
                        :variant="'ghost'" 
                        theme="gray" 
                        size="md" 
                        :icon="isDarkMode ? 'sun' : 'moon'"
                        @click="toggleDarkMode"
                        class="dark:text-dark-text dark:hover:bg-dark-bg"
                    >
                    </Button>
                    <Button :variant="'solid'" theme="red" size="md" label="Button" :loadingText="null" :disabled="false"
                        :link="null" icon="log-out" :loading="false" @click="onSignOut">
                    </Button>
                </div>
            </div>
        </nav>
    </div>
    <div class="p-1 bg-white dark:bg-dark-surface mb-8 transition-colors duration-300">
        <div class="mx-auto px-4 lg:px-8 max-w-[1800px]">
            <Breadcrumbs :items="props.breadcrumbs" />
        </div>
    </div>
    <div class="content-wrapper">
        <slot />
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useDarkMode } from '@/composables/useDarkMode';

const router = useRouter();
const { isDarkMode, toggleDarkMode } = useDarkMode();

const props = defineProps({
    breadcrumbs: {
        type: Array,
    },
});

const onSignOut = () => {
    router.push({ name: 'SignIn' });
}
</script>

<style scoped></style>
