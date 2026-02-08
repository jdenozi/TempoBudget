/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Internationalization (i18n) configuration.
 *
 * Supports French (fr) and English (en) locales.
 * Default locale is French. User preference is stored in localStorage.
 */

import { createI18n } from 'vue-i18n'
import fr from './locales/fr.json'
import en from './locales/en.json'

export type Locale = 'fr' | 'en'

export const SUPPORTED_LOCALES: { code: Locale; name: string }[] = [
  { code: 'fr', name: 'Français' },
  { code: 'en', name: 'English' },
]

const LOCALE_STORAGE_KEY = 'tempo-locale'

/**
 * Gets the saved locale from localStorage or returns the default.
 */
function getSavedLocale(): Locale {
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (saved && ['fr', 'en'].includes(saved)) {
    return saved as Locale
  }
  // Try to detect browser language
  const browserLang = navigator.language.split('-')[0]
  if (browserLang === 'en') {
    return 'en'
  }
  return 'fr' // Default to French
}

/**
 * Saves the locale preference to localStorage.
 */
export function saveLocale(locale: Locale): void {
  localStorage.setItem(LOCALE_STORAGE_KEY, locale)
}

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: getSavedLocale(),
  fallbackLocale: 'fr',
  messages: {
    fr,
    en,
  },
})

export default i18n
