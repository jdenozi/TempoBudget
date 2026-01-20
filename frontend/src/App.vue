<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Root Application Component

  This is the root component that serves as the entry point for the Vue application.
  It renders the router view to display the appropriate page based on the current route.
  Also handles inactivity timeout for auto-logout.
-->

<template>
  <n-config-provider>
    <n-message-provider>
      <router-view />

      <!-- Inactivity Warning Modal -->
      <n-modal
        v-model:show="showWarning"
        preset="dialog"
        type="warning"
        title="Session Expiring"
        :closable="false"
        :mask-closable="false"
      >
        <template #default>
          <p>Your session will expire in <strong>{{ secondsRemaining }}</strong> seconds due to inactivity.</p>
          <p>Click below to stay logged in.</p>
        </template>
        <template #action>
          <n-button type="primary" @click="stayLoggedIn">Stay Logged In</n-button>
        </template>
      </n-modal>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
/**
 * Root application component.
 * Renders the current route's component through router-view.
 * Manages inactivity timeout for automatic logout.
 */

import { onMounted, onUnmounted } from 'vue'
import { NConfigProvider, NMessageProvider, NModal, NButton } from 'naive-ui'
import { useInactivityTimer } from '@/composables/useInactivityTimer'

const {
  showWarning,
  secondsRemaining,
  startMonitoring,
  stopMonitoring,
  stayLoggedIn,
} = useInactivityTimer()

onMounted(() => {
  startMonitoring()
})

onUnmounted(() => {
  stopMonitoring()
})
</script>

<style>
/* Global CSS Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Base body styles */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
</style>