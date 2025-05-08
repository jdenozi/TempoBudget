<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Login View

  Entry point for user authentication. Wraps the LoginContent component
  with the Naive UI theme and message providers.
-->

<template>
  <n-config-provider :theme="darkTheme">
    <n-message-provider>
      <LoginContent />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
/**
 * Login view wrapper component.
 * Provides theme configuration and message provider context.
 */

import { NConfigProvider, NMessageProvider, darkTheme } from 'naive-ui'
import LoginContent from './LoginContent.vue'
</script>