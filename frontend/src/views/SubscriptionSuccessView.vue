<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Subscription Success View

  Displayed after successful Stripe checkout.
-->

<template>
  <n-space vertical size="large" align="center" class="success-container">
    <n-result
      status="success"
      :title="t('subscription.thankYou')"
      :description="t('subscription.successDesc')"
    >
      <template #icon>
        <n-icon :size="80" color="#10b981">
          <CheckmarkCircleOutline />
        </n-icon>
      </template>

      <template #footer>
        <n-space vertical align="center">
          <n-card v-if="subscriptionStore.status?.subscription" size="small" class="sub-details">
            <n-descriptions :column="1" bordered size="small">
              <n-descriptions-item :label="t('subscription.plan')">
                <n-tag :type="subscriptionStore.planType === 'annual' ? 'success' : 'info'">
                  {{ subscriptionStore.planType === 'annual' ? t('subscription.annual') : t('subscription.monthly') }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item :label="t('subscription.nextBilling')">
                {{ formatDate(subscriptionStore.currentPeriodEnd) }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>

          <n-space>
            <n-button type="primary" @click="goToDashboard">
              {{ t('subscription.goToDashboard') }}
            </n-button>
            <n-button @click="goToProfile">
              {{ t('subscription.viewProfile') }}
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-result>
  </n-space>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NSpace, NResult, NButton, NCard, NDescriptions, NDescriptionsItem,
  NTag, NIcon
} from 'naive-ui'
import { CheckmarkCircleOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { useSubscriptionStore } from '@/stores/subscription'

const router = useRouter()
const { t, locale } = useI18n()
const subscriptionStore = useSubscriptionStore()

onMounted(async () => {
  await subscriptionStore.fetchStatus()
})

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
}

const goToDashboard = () => {
  router.push('/dashboard')
}

const goToProfile = () => {
  router.push('/profile')
}
</script>

<style scoped>
.success-container {
  min-height: 60vh;
  padding: 40px 20px;
}

.sub-details {
  min-width: 280px;
  margin-bottom: 16px;
}
</style>
