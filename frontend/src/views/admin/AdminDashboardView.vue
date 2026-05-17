<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Admin Dashboard View

  Overview of subscription stats and key metrics.
-->

<template>
  <n-space vertical size="large">
    <h1 class="page-title">{{ t('admin.dashboard') }}</h1>

    <n-spin :show="loading">
      <!-- Key Metrics -->
      <n-grid :cols="isMobile ? 2 : 4" :x-gap="16" :y-gap="16">
        <n-gi>
          <n-card>
            <n-statistic :label="t('admin.totalUsers')" :value="stats?.total_users ?? 0" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic :label="t('admin.activeSubscriptions')" :value="stats?.active_subscriptions ?? 0" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic :label="t('admin.mrr')">
              <template #default>
                {{ formatCurrency(stats?.mrr ?? 0) }}
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic :label="t('admin.arr')">
              <template #default>
                {{ formatCurrency(stats?.arr ?? 0) }}
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- Subscription Breakdown -->
      <n-card :title="t('admin.subscriptionBreakdown')" style="margin-top: 24px;">
        <n-grid :cols="isMobile ? 1 : 3" :x-gap="16" :y-gap="16">
          <n-gi>
            <n-statistic :label="t('admin.monthlySubscribers')" :value="stats?.monthly_subscribers ?? 0">
              <template #suffix>
                <n-text depth="3"> ({{ formatCurrency(5.99 * (stats?.monthly_subscribers ?? 0)) }}/{{ t('subscription.month') }})</n-text>
              </template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic :label="t('admin.annualSubscribers')" :value="stats?.annual_subscribers ?? 0">
              <template #suffix>
                <n-text depth="3"> ({{ formatCurrency(45 * (stats?.annual_subscribers ?? 0)) }}/{{ t('subscription.year') }})</n-text>
              </template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic :label="t('admin.churnRate')">
              <template #default>
                {{ stats?.churn_rate?.toFixed(1) ?? 0 }}%
              </template>
            </n-statistic>
          </n-gi>
        </n-grid>
      </n-card>

      <!-- Quick Actions -->
      <n-card :title="t('admin.quickActions')" style="margin-top: 24px;">
        <n-space>
          <n-button @click="router.push('/admin/users')">
            {{ t('admin.manageUsers') }}
          </n-button>
          <n-button @click="router.push('/admin/quotes')">
            {{ t('admin.manageQuotes') }}
          </n-button>
        </n-space>
      </n-card>
    </n-spin>
  </n-space>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { NSpace, NCard, NGrid, NGi, NStatistic, NButton, NText, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { adminAPI, type SubscriptionStats } from '@/services/api'

const router = useRouter()
const { t, locale } = useI18n()

const loading = ref(false)
const stats = ref<SubscriptionStats | null>(null)
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  loading.value = true
  try {
    stats.value = await adminAPI.getSubscriptionStats()
  } catch (error) {
    console.error('Error loading stats:', error)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    style: 'currency',
    currency: 'EUR',
  }).format(value)
}
</script>

<style scoped>
.page-title {
  margin: 0;
  font-size: clamp(20px, 5vw, 28px);
}
</style>
