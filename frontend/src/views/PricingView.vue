<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Pricing View

  Displays subscription plans with Stripe checkout integration.
-->

<template>
  <n-space vertical size="large" class="pricing-container">
    <div class="pricing-header">
      <h1 class="pricing-title">{{ t('subscription.choosePlan') }}</h1>
      <p class="pricing-subtitle">{{ t('subscription.choosePlanDesc') }}</p>
    </div>

    <n-spin :show="loading">
      <div class="pricing-grid">
        <!-- Monthly Plan -->
        <n-card class="pricing-card">
          <div class="plan-header">
            <h2 class="plan-name">{{ t('subscription.monthly') }}</h2>
            <div class="plan-price">
              <span class="price-amount">{{ monthlyPrice }} €</span>
              <span class="price-period">/ {{ t('subscription.month') }}</span>
            </div>
          </div>

          <n-divider />

          <ul class="plan-features">
            <li v-for="feature in features" :key="feature">
              <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
              {{ feature }}
            </li>
          </ul>

          <template #footer>
            <n-button
              type="primary"
              block
              :disabled="hasActiveSubscription"
              :loading="checkingOut === 'monthly'"
              @click="handleCheckout('monthly')"
            >
              {{ hasActiveSubscription ? t('subscription.alreadySubscribed') : t('subscription.subscribe') }}
            </n-button>
          </template>
        </n-card>

        <!-- Annual Plan -->
        <n-card class="pricing-card featured">
          <div class="popular-badge">{{ t('subscription.bestValue') }}</div>
          <div class="plan-header">
            <h2 class="plan-name">{{ t('subscription.annual') }}</h2>
            <div class="plan-price">
              <span class="price-amount">{{ annualPrice }} €</span>
              <span class="price-period">/ {{ t('subscription.year') }}</span>
            </div>
            <n-tag type="success" size="small" class="savings-tag">
              {{ t('subscription.save25') }}
            </n-tag>
          </div>

          <n-divider />

          <ul class="plan-features">
            <li v-for="feature in features" :key="feature">
              <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
              {{ feature }}
            </li>
            <li>
              <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
              {{ t('subscription.prioritySupport') }}
            </li>
          </ul>

          <template #footer>
            <n-button
              type="primary"
              block
              :disabled="hasActiveSubscription"
              :loading="checkingOut === 'annual'"
              @click="handleCheckout('annual')"
            >
              {{ hasActiveSubscription ? t('subscription.alreadySubscribed') : t('subscription.subscribe') }}
            </n-button>
          </template>
        </n-card>
      </div>
    </n-spin>

    <!-- Current subscription info -->
    <n-card v-if="subscriptionStore.status?.has_subscription" :title="t('subscription.currentPlan')">
      <n-descriptions :column="isMobile ? 1 : 2" bordered>
        <n-descriptions-item :label="t('subscription.plan')">
          <n-tag :type="subscriptionStore.planType === 'annual' ? 'success' : 'info'">
            {{ subscriptionStore.planType === 'annual' ? t('subscription.annual') : t('subscription.monthly') }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item :label="t('subscription.status')">
          <n-tag :type="statusTagType">
            {{ t(`subscription.statuses.${subscriptionStore.subscriptionStatus}`) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item :label="t('subscription.nextBilling')">
          {{ formatDate(subscriptionStore.currentPeriodEnd) }}
        </n-descriptions-item>
        <n-descriptions-item :label="t('subscription.autoRenew')">
          {{ subscriptionStore.cancelAtPeriodEnd ? t('common.no') : t('common.yes') }}
        </n-descriptions-item>
      </n-descriptions>

      <template #footer>
        <n-button @click="handleManageSubscription" :loading="openingPortal">
          {{ t('subscription.manageSubscription') }}
        </n-button>
      </template>
    </n-card>

    <!-- FAQ -->
    <n-card :title="t('subscription.faq')">
      <n-collapse>
        <n-collapse-item :title="t('subscription.faqCancel')" name="cancel">
          {{ t('subscription.faqCancelAnswer') }}
        </n-collapse-item>
        <n-collapse-item :title="t('subscription.faqPayment')" name="payment">
          {{ t('subscription.faqPaymentAnswer') }}
        </n-collapse-item>
        <n-collapse-item :title="t('subscription.faqRefund')" name="refund">
          {{ t('subscription.faqRefundAnswer') }}
        </n-collapse-item>
      </n-collapse>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NSpace, NCard, NButton, NDivider, NTag, NIcon, NSpin,
  NDescriptions, NDescriptionsItem, NCollapse, NCollapseItem,
  useMessage
} from 'naive-ui'
import { CheckmarkCircleOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { useSubscriptionStore } from '@/stores/subscription'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const { t, locale } = useI18n()
const subscriptionStore = useSubscriptionStore()
const authStore = useAuthStore()

const loading = ref(false)
const checkingOut = ref<'monthly' | 'annual' | null>(null)
const openingPortal = ref(false)
const isMobile = ref(false)

const monthlyPrice = computed(() => {
  const price = subscriptionStore.prices?.monthly ?? 5.99
  return price.toLocaleString(locale.value === 'fr' ? 'fr-FR' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace('.', ',')
})

const annualPrice = computed(() => {
  const price = subscriptionStore.prices?.annual ?? 45
  return price.toLocaleString(locale.value === 'fr' ? 'fr-FR' : 'en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
})

const features = computed(() => [
  t('subscription.featureUnlimited'),
  t('subscription.featureCharts'),
  t('subscription.featureRecurring'),
  t('subscription.featureExport'),
  t('subscription.featureSync'),
])

const hasActiveSubscription = computed(() => subscriptionStore.hasActiveSubscription)

const statusTagType = computed(() => {
  switch (subscriptionStore.subscriptionStatus) {
    case 'active':
    case 'trialing':
      return 'success'
    case 'past_due':
      return 'warning'
    case 'canceled':
      return 'error'
    default:
      return 'default'
  }
})

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // Fetch prices (public endpoint, no auth required)
  subscriptionStore.fetchPrices()

  if (authStore.isAuthenticated) {
    loading.value = true
    try {
      await subscriptionStore.fetchStatus()
    } finally {
      loading.value = false
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
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

const handleCheckout = async (planType: 'monthly' | 'annual') => {
  if (!authStore.isAuthenticated) {
    message.info(t('subscription.loginRequired'))
    router.push('/login?redirect=/pricing')
    return
  }

  checkingOut.value = planType
  try {
    const response = await subscriptionStore.createCheckout(planType)
    window.location.href = response.checkout_url
  } catch (error: unknown) {
    console.error('Checkout error:', error)
    const axiosError = error as { response?: { status?: number } }
    if (axiosError.response?.status === 400) {
      message.warning(t('subscription.alreadySubscribed'))
    } else {
      message.error(t('subscription.checkoutError'))
    }
  } finally {
    checkingOut.value = null
  }
}

const handleManageSubscription = async () => {
  openingPortal.value = true
  try {
    await subscriptionStore.openPortal()
  } catch (error) {
    console.error('Portal error:', error)
    message.error(t('subscription.portalError'))
  } finally {
    openingPortal.value = false
  }
}
</script>

<style scoped>
.pricing-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.pricing-header {
  text-align: center;
  margin-bottom: 24px;
}

.pricing-title {
  margin: 0 0 8px;
  font-size: clamp(24px, 5vw, 36px);
}

.pricing-subtitle {
  margin: 0;
  color: var(--n-text-color-3);
  font-size: 16px;
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.pricing-card {
  position: relative;
}

.pricing-card.featured {
  border: 2px solid var(--n-primary-color);
}

.popular-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--n-primary-color);
  color: white;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.plan-header {
  text-align: center;
}

.plan-name {
  margin: 0 0 12px;
  font-size: 20px;
}

.plan-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}

.price-amount {
  font-size: 40px;
  font-weight: 700;
  color: var(--n-primary-color);
}

.price-period {
  font-size: 14px;
  color: var(--n-text-color-3);
}

.savings-tag {
  margin-top: 8px;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
}
</style>
