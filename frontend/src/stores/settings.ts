/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Settings Store
 *
 * Pinia store for managing user preferences.
 * Settings are persisted in localStorage.
 *
 * State:
 * - inactivityTimeout: Time in minutes before auto-logout (0 = disabled)
 */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

/** Available inactivity timeout options in minutes */
export const INACTIVITY_OPTIONS = [
  { label: 'Never', value: 0 },
  { label: '5 minutes', value: 5 },
  { label: '15 minutes', value: 15 },
  { label: '30 minutes', value: 30 },
  { label: '1 hour', value: 60 },
  { label: '2 hours', value: 120 },
] as const

const SETTINGS_KEY = 'app_settings'

interface Settings {
  inactivityTimeout: number
}

const defaultSettings: Settings = {
  inactivityTimeout: 30, // 30 minutes by default
}

export const useSettingsStore = defineStore('settings', () => {
  /** Inactivity timeout in minutes (0 = disabled) */
  const inactivityTimeout = ref(defaultSettings.inactivityTimeout)

  /**
   * Initializes settings from localStorage.
   */
  function init() {
    const saved = localStorage.getItem(SETTINGS_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as Partial<Settings>
        if (typeof parsed.inactivityTimeout === 'number') {
          inactivityTimeout.value = parsed.inactivityTimeout
        }
      } catch {
        // Invalid JSON, use defaults
      }
    }
  }

  /**
   * Saves current settings to localStorage.
   */
  function save() {
    const settings: Settings = {
      inactivityTimeout: inactivityTimeout.value,
    }
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  }

  /**
   * Sets the inactivity timeout.
   * @param minutes - Timeout in minutes (0 to disable)
   */
  function setInactivityTimeout(minutes: number) {
    inactivityTimeout.value = minutes
    save()
  }

  // Auto-save when settings change
  watch(inactivityTimeout, save)

  return {
    inactivityTimeout,
    init,
    setInactivityTimeout,
  }
})
