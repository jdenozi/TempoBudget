/**
 * URSSAF deadline notifications composable
 *
 * Checks for upcoming deadlines and provides notification data.
 * Notifications are shown for:
 * - 7 days before deadline
 * - 3 days before deadline
 * - 1 day before deadline
 * - On the deadline day
 * - After deadline (overdue)
 */

import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

export interface UrssafDeadline {
  period_label: string
  deadline: string
  days_remaining: number
  total_due: number
  is_projection: boolean
}

export interface UrssafNotification {
  id: string
  type: 'warning' | 'error' | 'info'
  title: string
  message: string
  deadline: UrssafDeadline
  dismissed: boolean
}

const STORAGE_KEY = 'urssaf_dismissed_notifications'

// Get dismissed notification IDs from localStorage
function getDismissedIds(): Set<string> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      // Clean up old entries (older than 90 days)
      const now = Date.now()
      const filtered = Object.entries(parsed)
        .filter(([_, timestamp]) => now - (timestamp as number) < 90 * 24 * 60 * 60 * 1000)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(filtered)))
      return new Set(filtered.map(([id]) => id))
    }
  } catch {
    // Ignore localStorage errors
  }
  return new Set()
}

// Save dismissed notification ID
function saveDismissedId(id: string) {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    const parsed = stored ? JSON.parse(stored) : {}
    parsed[id] = Date.now()
    localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed))
  } catch {
    // Ignore localStorage errors
  }
}

export function useUrssafNotifications() {
  const { t } = useI18n()

  const deadlines = ref<UrssafDeadline[]>([])
  const dismissedIds = ref<Set<string>>(getDismissedIds())

  // Generate notification ID from deadline
  function getNotificationId(deadline: UrssafDeadline, daysThreshold: number): string {
    return `${deadline.deadline}-${daysThreshold}`
  }

  // Check if notification should be shown for a deadline
  function shouldNotify(days: number): { notify: boolean; threshold: number } {
    if (days < 0) return { notify: true, threshold: -1 } // Overdue
    if (days === 0) return { notify: true, threshold: 0 } // Today
    if (days === 1) return { notify: true, threshold: 1 } // Tomorrow
    if (days <= 3) return { notify: true, threshold: 3 } // 3 days
    if (days <= 7) return { notify: true, threshold: 7 } // 7 days
    return { notify: false, threshold: -1 }
  }

  // Active notifications (not dismissed, not projections)
  const notifications = computed<UrssafNotification[]>(() => {
    const result: UrssafNotification[] = []

    for (const deadline of deadlines.value) {
      // Skip projections for notifications
      if (deadline.is_projection) continue

      const { notify, threshold } = shouldNotify(deadline.days_remaining)
      if (!notify) continue

      const id = getNotificationId(deadline, threshold)
      if (dismissedIds.value.has(id)) continue

      let type: 'warning' | 'error' | 'info' = 'info'
      let title = ''
      let message = ''

      if (deadline.days_remaining < 0) {
        type = 'error'
        title = t('pro.urssaf.notifications.overdueTitle')
        message = t('pro.urssaf.notifications.overdueMessage', {
          period: deadline.period_label,
          days: Math.abs(deadline.days_remaining),
          amount: deadline.total_due.toFixed(2),
        })
      } else if (deadline.days_remaining === 0) {
        type = 'error'
        title = t('pro.urssaf.notifications.todayTitle')
        message = t('pro.urssaf.notifications.todayMessage', {
          period: deadline.period_label,
          amount: deadline.total_due.toFixed(2),
        })
      } else if (deadline.days_remaining === 1) {
        type = 'warning'
        title = t('pro.urssaf.notifications.tomorrowTitle')
        message = t('pro.urssaf.notifications.tomorrowMessage', {
          period: deadline.period_label,
          amount: deadline.total_due.toFixed(2),
        })
      } else if (deadline.days_remaining <= 3) {
        type = 'warning'
        title = t('pro.urssaf.notifications.soonTitle')
        message = t('pro.urssaf.notifications.soonMessage', {
          period: deadline.period_label,
          days: deadline.days_remaining,
          amount: deadline.total_due.toFixed(2),
        })
      } else {
        type = 'info'
        title = t('pro.urssaf.notifications.upcomingTitle')
        message = t('pro.urssaf.notifications.upcomingMessage', {
          period: deadline.period_label,
          days: deadline.days_remaining,
          amount: deadline.total_due.toFixed(2),
        })
      }

      result.push({
        id,
        type,
        title,
        message,
        deadline,
        dismissed: false,
      })
    }

    // Sort by urgency (overdue first, then by days remaining)
    return result.sort((a, b) => a.deadline.days_remaining - b.deadline.days_remaining)
  })

  // Dismiss a notification
  function dismiss(notificationId: string) {
    dismissedIds.value.add(notificationId)
    saveDismissedId(notificationId)
  }

  // Update deadlines from API data
  function setDeadlines(data: UrssafDeadline[]) {
    deadlines.value = data
  }

  // Check if there are any urgent notifications (overdue or today)
  const hasUrgentNotifications = computed(() =>
    notifications.value.some(n => n.type === 'error')
  )

  // Count of active notifications
  const notificationCount = computed(() => notifications.value.length)

  return {
    notifications,
    hasUrgentNotifications,
    notificationCount,
    setDeadlines,
    dismiss,
  }
}
