/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Mobile Detection Composable
 *
 * Provides reactive mobile viewport detection with automatic
 * resize listener management.
 */

import { ref, onMounted, onUnmounted } from 'vue'

const MOBILE_BREAKPOINT = 768

/**
 * Detects whether the viewport is mobile-sized.
 * @param breakpoint - Custom breakpoint in pixels (default: 768)
 * @returns Reactive `isMobile` ref
 */
export function useMobileDetect(breakpoint = MOBILE_BREAKPOINT) {
  const isMobile = ref(false)

  const checkMobile = () => {
    isMobile.value = window.innerWidth < breakpoint
  }

  onMounted(() => {
    checkMobile()
    window.addEventListener('resize', checkMobile)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', checkMobile)
  })

  return { isMobile }
}
