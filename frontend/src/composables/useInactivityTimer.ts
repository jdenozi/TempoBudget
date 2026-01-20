/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Inactivity Timer Composable
 *
 * Monitors user activity and triggers auto-logout after a period of inactivity.
 * Activity is detected through mouse movements, clicks, key presses, and touch events.
 */

import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'

/** Events that indicate user activity */
const ACTIVITY_EVENTS = [
  'mousedown',
  'mousemove',
  'keydown',
  'scroll',
  'touchstart',
  'click',
] as const

export function useInactivityTimer() {
  const router = useRouter()
  const authStore = useAuthStore()
  const settingsStore = useSettingsStore()

  let timeoutId: ReturnType<typeof setTimeout> | null = null
  let warningTimeoutId: ReturnType<typeof setTimeout> | null = null

  /** Whether the warning is currently shown */
  const showWarning = ref(false)

  /** Seconds remaining before logout */
  const secondsRemaining = ref(0)

  let countdownInterval: ReturnType<typeof setInterval> | null = null

  /**
   * Resets the inactivity timer.
   */
  function resetTimer() {
    // Clear existing timers
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
    if (warningTimeoutId) {
      clearTimeout(warningTimeoutId)
      warningTimeoutId = null
    }
    if (countdownInterval) {
      clearInterval(countdownInterval)
      countdownInterval = null
    }

    showWarning.value = false
    secondsRemaining.value = 0

    // Don't set timer if disabled or not authenticated
    if (settingsStore.inactivityTimeout === 0 || !authStore.isAuthenticated) {
      return
    }

    const timeoutMs = settingsStore.inactivityTimeout * 60 * 1000
    const warningMs = 60 * 1000 // Show warning 60 seconds before logout

    // Set warning timer (1 minute before logout)
    if (timeoutMs > warningMs) {
      warningTimeoutId = setTimeout(() => {
        showWarning.value = true
        secondsRemaining.value = 60

        // Start countdown
        countdownInterval = setInterval(() => {
          secondsRemaining.value--
          if (secondsRemaining.value <= 0 && countdownInterval) {
            clearInterval(countdownInterval)
            countdownInterval = null
          }
        }, 1000)
      }, timeoutMs - warningMs)
    }

    // Set logout timer
    timeoutId = setTimeout(() => {
      performLogout()
    }, timeoutMs)
  }

  /**
   * Performs the auto-logout.
   */
  function performLogout() {
    showWarning.value = false
    authStore.logout()
    router.push('/login?reason=inactivity')
  }

  /**
   * Keeps the session alive (user clicked "Stay logged in").
   */
  function stayLoggedIn() {
    resetTimer()
  }

  /**
   * Handles user activity events.
   */
  function handleActivity() {
    // Only reset if warning is not shown (to allow countdown to complete if user ignores)
    if (!showWarning.value) {
      resetTimer()
    }
  }

  /**
   * Starts monitoring user activity.
   */
  function startMonitoring() {
    ACTIVITY_EVENTS.forEach(event => {
      document.addEventListener(event, handleActivity, { passive: true })
    })
    resetTimer()
  }

  /**
   * Stops monitoring user activity.
   */
  function stopMonitoring() {
    ACTIVITY_EVENTS.forEach(event => {
      document.removeEventListener(event, handleActivity)
    })

    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
    if (warningTimeoutId) {
      clearTimeout(warningTimeoutId)
      warningTimeoutId = null
    }
    if (countdownInterval) {
      clearInterval(countdownInterval)
      countdownInterval = null
    }
  }

  // Watch for settings changes
  watch(() => settingsStore.inactivityTimeout, () => {
    if (authStore.isAuthenticated) {
      resetTimer()
    }
  })

  // Watch for auth changes
  watch(() => authStore.isAuthenticated, (isAuth) => {
    if (isAuth) {
      resetTimer()
    } else {
      stopMonitoring()
    }
  })

  return {
    showWarning,
    secondsRemaining,
    startMonitoring,
    stopMonitoring,
    stayLoggedIn,
    resetTimer,
  }
}
