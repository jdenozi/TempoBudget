<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Subscription Cancel View

  Displayed when user cancels Stripe checkout.
-->

<template>
  <n-space vertical size="large" align="center" class="cancel-container">
    <n-result
      status="info"
      :title="t('subscription.checkoutCanceled')"
      :description="t('subscription.checkoutCanceledDesc')"
    >
      <template #footer>
        <n-space>
          <n-button type="primary" @click="goToPricing">
            {{ t('subscription.viewPlans') }}
          </n-button>
          <n-button @click="goToDashboard">
            {{ t('subscription.goToDashboard') }}
          </n-button>
        </n-space>
      </template>
    </n-result>
  </n-space>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NSpace, NResult, NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t } = useI18n()

const goToPricing = () => {
  router.push('/pricing')
}

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.cancel-container {
  min-height: 60vh;
  padding: 40px 20px;
}
</style>
