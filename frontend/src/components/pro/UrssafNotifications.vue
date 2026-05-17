<template>
  <div v-if="notifications.length > 0" class="urssaf-notifications">
    <n-alert
      v-for="notification in notifications"
      :key="notification.id"
      :type="notification.type"
      :title="notification.title"
      closable
      @close="handleDismiss(notification.id)"
      style="margin-bottom: 12px;"
    >
      {{ notification.message }}
      <n-button size="small" text style="margin-left: 8px;" @click="goToSchedule">
        {{ t('pro.urssaf.notifications.viewSchedule') }} →
      </n-button>
    </n-alert>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NAlert, NButton } from 'naive-ui'
import { useUrssafNotifications, type UrssafDeadline } from '@/composables/useUrssafNotifications'

const props = defineProps<{
  deadlines: UrssafDeadline[]
}>()

const { t } = useI18n()
const router = useRouter()
const { notifications, setDeadlines, dismiss } = useUrssafNotifications()

// Update deadlines when prop changes
watch(() => props.deadlines, (newDeadlines) => {
  setDeadlines(newDeadlines)
}, { immediate: true })

function handleDismiss(notificationId: string) {
  dismiss(notificationId)
}

function goToSchedule() {
  router.push({ name: 'pro-declaration' })
}
</script>

<style scoped>
.urssaf-notifications {
  margin-bottom: 16px;
}
</style>
