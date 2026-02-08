<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Login Content Component

  Provides the login and registration forms for user authentication.
  Includes form validation and error handling for auth operations.
-->

<template>
  <div class="login-container">
    <div class="login-box">
      <img src="@/assets/logo.png" alt="Tempo Finance" class="login-logo" />
    <n-card :title="t('auth.login')" style="max-width: 400px; width: 100%;">
      <!-- Session expired/inactivity alert -->
      <n-alert
        v-if="logoutReason"
        :type="logoutReason === 'inactivity' ? 'warning' : 'info'"
        style="margin-bottom: 16px;"
        closable
        @close="logoutReason = null"
      >
        {{ logoutReason === 'inactivity'
          ? t('auth.logoutSuccess')
          : t('auth.logoutSuccess') }}
      </n-alert>
      <n-form ref="formRef" :model="formData" :rules="rules">
        <n-form-item :label="t('auth.email')" path="email">
          <n-input v-model:value="formData.email" placeholder="email@example.com" />
        </n-form-item>

        <n-form-item :label="t('auth.password')" path="password">
          <n-input
            v-model:value="formData.password"
            type="password"
            placeholder="••••••••"
            @keyup.enter="handleLogin"
          />
        </n-form-item>

        <n-space vertical :size="12">
          <n-button
            type="primary"
            block
            size="large"
            :loading="loading"
            @click="handleLogin"
          >
            {{ t('auth.loginButton') }}
          </n-button>

          <n-divider style="margin: 8px 0;">{{ t('auth.noAccount') }}</n-divider>

          <n-button
            block
            size="large"
            :loading="loading"
            @click="showRegister = true"
          >
            {{ t('auth.registerButton') }}
          </n-button>
        </n-space>
      </n-form>
    </n-card>
    </div>

    <!-- Registration Modal -->
    <n-modal v-model:show="showRegister" preset="card" :title="t('auth.register')" style="max-width: 400px;">
      <n-form ref="registerFormRef" :model="registerData" :rules="registerRules">
        <n-form-item :label="t('auth.name')" path="name">
          <n-input v-model:value="registerData.name" :placeholder="t('auth.name')" />
        </n-form-item>

        <n-form-item :label="t('auth.email')" path="email">
          <n-input v-model:value="registerData.email" placeholder="email@example.com" />
        </n-form-item>

        <n-form-item :label="t('auth.password')" path="password">
          <n-input
            v-model:value="registerData.password"
            type="password"
            placeholder="••••••••"
          />
        </n-form-item>

        <n-button
          type="primary"
          block
          size="large"
          :loading="loading"
          @click="handleRegister"
        >
          {{ t('auth.registerButton') }}
        </n-button>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
/**
 * Login content component with login and registration forms.
 *
 * Features:
 * - Login form with email/password validation
 * - Registration modal with name/email/password validation
 * - Error handling for authentication failures
 * - Automatic redirect to dashboard on success
 */

import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NCard, NForm, NFormItem, NInput, NButton,
  NSpace, NDivider, NModal, NAlert, useMessage
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const { t } = useI18n()
const authStore = useAuthStore()

/** Reason for being on login page (from query param) */
const logoutReason = ref<string | null>(null)

onMounted(() => {
  const reason = route.query.reason as string | undefined
  if (reason === 'inactivity') {
    logoutReason.value = 'inactivity'
    message.warning('You have been logged out due to inactivity')
  } else if (reason === 'expired') {
    logoutReason.value = 'expired'
    message.warning('Your session has expired. Please log in again.')
  }
})

/** Loading state for async operations */
const loading = ref(false)

/** Registration modal visibility */
const showRegister = ref(false)

/** Login form reference */
const formRef = ref<any>(null)

/** Login form data */
const formData = ref({
  email: '',
  password: '',
})

/** Login form validation rules */
const rules = {
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { type: 'email' as const, message: 'Invalid email format', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Password is required', trigger: 'blur' },
  ],
}

/** Registration form reference */
const registerFormRef = ref<any>(null)

/** Registration form data */
const registerData = ref({
  name: '',
  email: '',
  password: '',
})

/** Registration form validation rules */
const registerRules = {
  name: [
    { required: true, message: 'Name is required', trigger: 'blur' },
  ],
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { type: 'email' as const, message: 'Invalid email format', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Password is required', trigger: 'blur' },
    { min: 6, message: 'Minimum 6 characters', trigger: 'blur' },
  ],
}

/**
 * Handles login form submission.
 * Validates form and attempts authentication.
 */
const handleLogin = () => {
  formRef.value?.validate(async (errors: any) => {
    if (errors) return

    loading.value = true
    try {
      await authStore.login(formData.value.email, formData.value.password)
      message.success('Login successful!')
      router.push('/dashboard')
    } catch (error: any) {
      console.error('Login error:', error)
      if (error.response?.status === 401) {
        message.error('Invalid email or password')
      } else {
        message.error('Login failed')
      }
    } finally {
      loading.value = false
    }
  })
}

/**
 * Handles registration form submission.
 * Validates form and attempts account creation.
 */
const handleRegister = () => {
  registerFormRef.value?.validate(async (errors: any) => {
    if (errors) return

    loading.value = true
    try {
      await authStore.register(
        registerData.value.email,
        registerData.value.name,
        registerData.value.password
      )
      message.success('Account created! Welcome!')
      showRegister.value = false
      router.push('/dashboard')
    } catch (error: any) {
      console.error('Register error:', error)
      if (error.response?.status === 500) {
        message.error('This email is already in use')
      } else {
        message.error('Error creating account')
      }
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.login-logo {
  width: 120px;
  height: 120px;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
</style>