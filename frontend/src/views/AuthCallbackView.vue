<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Auth Callback View

  Handles the OIDC callback after successful authentication.
  Extracts the token from URL and stores it in the auth store.
-->

<template>
  <div class="callback-container">
    <n-spin size="large" />
    <p>Connexion en cours...</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NSpin, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const authStore = useAuthStore()

onMounted(async () => {
  const token = route.query.token as string | undefined

  if (token) {
    try {
      await authStore.setTokenAndFetchUser(token)
      message.success('Connexion SSO réussie!')
      router.push('/dashboard')
    } catch {
      message.error('Erreur lors de la connexion SSO')
      router.push('/login')
    }
  } else {
    message.error('Token manquant')
    router.push('/login')
  }
})
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}
</style>
