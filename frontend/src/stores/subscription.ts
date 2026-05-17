/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Subscription Store
 *
 * Pinia store for managing subscription state.
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { stripeAPI, type SubscriptionStatus, type StripePrices, type ProAccessStatus } from '@/services/api'

export const useSubscriptionStore = defineStore('subscription', () => {
  const status = ref<SubscriptionStatus | null>(null)
  const prices = ref<StripePrices | null>(null)
  const proAccess = ref<ProAccessStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasActiveSubscription = computed(() => {
    return status.value?.has_subscription &&
      (status.value?.status === 'active' || status.value?.status === 'trialing')
  })

  const hasProAccess = computed(() => proAccess.value?.has_pro_access ?? false)
  const proAccessReason = computed(() => proAccess.value?.reason ?? 'none')

  const planType = computed(() => status.value?.plan_type)
  const subscriptionStatus = computed(() => status.value?.status)
  const currentPeriodEnd = computed(() => status.value?.current_period_end)
  const cancelAtPeriodEnd = computed(() => status.value?.cancel_at_period_end ?? false)

  const fetchPrices = async () => {
    try {
      prices.value = await stripeAPI.getPrices()
    } catch (e) {
      console.error('Failed to fetch prices', e)
    }
  }

  const fetchStatus = async () => {
    loading.value = true
    error.value = null
    try {
      status.value = await stripeAPI.getSubscription()
    } catch (e) {
      error.value = 'Failed to fetch subscription status'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  const fetchProAccess = async () => {
    try {
      proAccess.value = await stripeAPI.getProAccess()
    } catch (e) {
      console.error('Failed to fetch pro access status', e)
    }
  }

  const createCheckout = async (planType: 'monthly' | 'annual') => {
    const baseUrl = window.location.origin
    const response = await stripeAPI.createCheckout({
      plan_type: planType,
      success_url: `${baseUrl}/subscription/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${baseUrl}/subscription/cancel`,
    })
    return response
  }

  const openPortal = async () => {
    const response = await stripeAPI.createPortalSession()
    window.location.href = response.portal_url
  }

  const reset = () => {
    status.value = null
    prices.value = null
    proAccess.value = null
    error.value = null
  }

  return {
    status,
    prices,
    proAccess,
    loading,
    error,
    hasActiveSubscription,
    hasProAccess,
    proAccessReason,
    planType,
    subscriptionStatus,
    currentPeriodEnd,
    cancelAtPeriodEnd,
    fetchPrices,
    fetchStatus,
    fetchProAccess,
    createCheckout,
    openPortal,
    reset,
  }
})
