/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Date utility functions
 */

/**
 * Formats a timestamp to a local date string (YYYY-MM-DD).
 * Unlike toISOString(), this preserves the local timezone.
 * @param timestamp - Unix timestamp in milliseconds
 * @returns Date string in YYYY-MM-DD format
 */
export function formatDateLocal(timestamp: number): string {
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Parses a date string and returns a timestamp at noon local time.
 * Using noon avoids timezone edge cases when the date picker returns midnight.
 * @param dateString - Date string in YYYY-MM-DD format
 * @returns Unix timestamp in milliseconds
 */
export function parseDateToTimestamp(dateString: string): number {
  const [year, month, day] = dateString.split('-').map(Number)
  return new Date(year, month - 1, day, 12, 0, 0).getTime()
}
