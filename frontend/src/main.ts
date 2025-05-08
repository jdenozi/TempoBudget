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
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Initialize authentication state from localStorage
const authStore = useAuthStore()
authStore.init()

app.mount('#app')