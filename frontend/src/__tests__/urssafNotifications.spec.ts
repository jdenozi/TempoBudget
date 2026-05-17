/**
 * Tests for URSSAF notifications logic
 */
import { describe, it, expect, beforeEach } from 'vitest'

// Extracted notification logic for testing
interface UrssafDeadline {
  period_label: string
  deadline: string
  days_remaining: number
  total_due: number
  is_projection: boolean
}

function shouldNotify(days: number): { notify: boolean; threshold: number } {
  if (days < 0) return { notify: true, threshold: -1 } // Overdue
  if (days === 0) return { notify: true, threshold: 0 } // Today
  if (days === 1) return { notify: true, threshold: 1 } // Tomorrow
  if (days <= 3) return { notify: true, threshold: 3 } // 3 days
  if (days <= 7) return { notify: true, threshold: 7 } // 7 days
  return { notify: false, threshold: -1 }
}

function getNotificationId(deadline: UrssafDeadline, threshold: number): string {
  return `${deadline.deadline}-${threshold}`
}

describe('UrssafNotifications', () => {
  describe('shouldNotify', () => {
    it('notifies for overdue deadlines', () => {
      const result = shouldNotify(-5)
      expect(result.notify).toBe(true)
      expect(result.threshold).toBe(-1)
    })

    it('notifies for deadline today', () => {
      const result = shouldNotify(0)
      expect(result.notify).toBe(true)
      expect(result.threshold).toBe(0)
    })

    it('notifies for deadline tomorrow', () => {
      const result = shouldNotify(1)
      expect(result.notify).toBe(true)
      expect(result.threshold).toBe(1)
    })

    it('notifies for 2 days remaining (within 3 day threshold)', () => {
      const result = shouldNotify(2)
      expect(result.notify).toBe(true)
      expect(result.threshold).toBe(3)
    })

    it('notifies for 3 days remaining', () => {
      const result = shouldNotify(3)
      expect(result.notify).toBe(true)
      expect(result.threshold).toBe(3)
    })

    it('notifies for 5 days remaining (within 7 day threshold)', () => {
      const result = shouldNotify(5)
      expect(result.notify).toBe(true)
      expect(result.threshold).toBe(7)
    })

    it('notifies for 7 days remaining', () => {
      const result = shouldNotify(7)
      expect(result.notify).toBe(true)
      expect(result.threshold).toBe(7)
    })

    it('does not notify for 8 days remaining', () => {
      const result = shouldNotify(8)
      expect(result.notify).toBe(false)
    })

    it('does not notify for 30 days remaining', () => {
      const result = shouldNotify(30)
      expect(result.notify).toBe(false)
    })
  })

  describe('getNotificationId', () => {
    it('creates unique ID based on deadline and threshold', () => {
      const deadline: UrssafDeadline = {
        period_label: 'Q1 2024',
        deadline: '2024-04-30',
        days_remaining: 5,
        total_due: 1500,
        is_projection: false,
      }

      const id = getNotificationId(deadline, 7)
      expect(id).toBe('2024-04-30-7')
    })

    it('creates different IDs for different thresholds', () => {
      const deadline: UrssafDeadline = {
        period_label: 'Q1 2024',
        deadline: '2024-04-30',
        days_remaining: 5,
        total_due: 1500,
        is_projection: false,
      }

      const id7 = getNotificationId(deadline, 7)
      const id3 = getNotificationId(deadline, 3)

      expect(id7).not.toBe(id3)
    })
  })

  describe('notification filtering', () => {
    const mockDeadlines: UrssafDeadline[] = [
      {
        period_label: 'Projection Q2',
        deadline: '2024-07-31',
        days_remaining: 5,
        total_due: 1500,
        is_projection: true,
      },
      {
        period_label: 'Q1 2024',
        deadline: '2024-04-30',
        days_remaining: 3,
        total_due: 2000,
        is_projection: false,
      },
      {
        period_label: 'Q4 2023',
        deadline: '2024-01-31',
        days_remaining: -10,
        total_due: 1800,
        is_projection: false,
      },
    ]

    it('filters out projections', () => {
      const notifications = mockDeadlines.filter(d => !d.is_projection)
      expect(notifications).toHaveLength(2)
      expect(notifications.every(n => !n.is_projection)).toBe(true)
    })

    it('identifies overdue deadlines', () => {
      const overdue = mockDeadlines.filter(d => d.days_remaining < 0)
      expect(overdue).toHaveLength(1)
      expect(overdue[0]?.period_label).toBe('Q4 2023')
    })

    it('sorts by days remaining (urgent first)', () => {
      const sorted = [...mockDeadlines]
        .filter(d => !d.is_projection)
        .sort((a, b) => a.days_remaining - b.days_remaining)

      expect(sorted[0]?.days_remaining).toBe(-10) // Overdue first
      expect(sorted[1]?.days_remaining).toBe(3)
    })
  })

  describe('notification types', () => {
    it('returns error type for overdue', () => {
      const type = getNotificationType(-5)
      expect(type).toBe('error')
    })

    it('returns error type for today', () => {
      const type = getNotificationType(0)
      expect(type).toBe('error')
    })

    it('returns warning type for tomorrow', () => {
      const type = getNotificationType(1)
      expect(type).toBe('warning')
    })

    it('returns warning type for 2-3 days', () => {
      expect(getNotificationType(2)).toBe('warning')
      expect(getNotificationType(3)).toBe('warning')
    })

    it('returns info type for 4-7 days', () => {
      expect(getNotificationType(5)).toBe('info')
      expect(getNotificationType(7)).toBe('info')
    })
  })
})

// Helper function for tests
function getNotificationType(daysRemaining: number): 'error' | 'warning' | 'info' {
  if (daysRemaining < 0) return 'error'
  if (daysRemaining === 0) return 'error'
  if (daysRemaining <= 3) return 'warning'
  return 'info'
}
