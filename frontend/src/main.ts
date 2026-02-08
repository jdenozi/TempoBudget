/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Application entry point.
 *
 * Initializes the Vue application with Pinia state management and Vue Router.
 * Also restores the authentication state from localStorage on startup.
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { useAuthStore } from './stores/auth'
import { useSettingsStore } from './stores/settings'
import { setupApiInterceptors } from './services/api'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(i18n)

// Initialize stores from localStorage
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
authStore.init()
settingsStore.init()

// Setup API interceptors (for auto-logout on 401)
setupApiInterceptors(authStore, router)

app.mount('#app')