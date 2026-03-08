/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Chart Options Composable
 *
 * Provides reusable Chart.js option builders for consistent
 * chart styling across personal and pro modes.
 */

import type { Ref } from 'vue'

/** Shared color palette for charts */
export const CHART_COLORS = [
  '#5470c6',
  '#91cc75',
  '#fac858',
  '#ee6666',
  '#73c0de',
  '#3ba272',
  '#fc8452',
  '#9a60b4',
  '#ea7ccc'
]

/** Income-focused color palette */
export const INCOME_COLORS = ['#18a058', '#91cc75', '#73c0de', '#fac858', '#ee6666']

/** Euro currency tooltip formatter */
function euroTooltipLabel(context: any) {
  const label = context.label || context.dataset?.label || ''
  const value = context.parsed?.y ?? context.parsed ?? 0
  return `${label}: ${Number(value).toFixed(2)} €`
}

/** Euro tooltip with percentage */
function euroPercentTooltipLabel(context: any) {
  const label = context.label || ''
  const value = context.parsed || 0
  const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
  const percentage = ((value / total) * 100).toFixed(2)
  return `${label}: ${Number(value).toFixed(2)} € (${percentage}%)`
}

/**
 * Returns responsive Pie/Doughnut chart options.
 */
export function usePieChartOptions(isMobile: Ref<boolean>, { showPercentage = true } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: isMobile.value ? 'bottom' as const : 'right' as const,
        labels: {
          boxWidth: 15,
          padding: 10,
          font: {
            size: isMobile.value ? 10 : 12
          }
        }
      },
      tooltip: {
        callbacks: {
          label: showPercentage ? euroPercentTooltipLabel : euroTooltipLabel
        }
      }
    }
  }
}

/**
 * Returns responsive Bar chart options with euro-formatted axes.
 */
export function useBarChartOptions(isMobile: Ref<boolean>, { rotateLabels = false } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            size: isMobile.value ? 10 : 12
          }
        }
      },
      tooltip: {
        callbacks: {
          label: euroTooltipLabel
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => `${value} €`,
          font: {
            size: isMobile.value ? 9 : 11
          }
        }
      },
      x: {
        ticks: {
          font: {
            size: isMobile.value ? 9 : 11
          },
          maxRotation: (rotateLabels || isMobile.value) ? 45 : 0,
          minRotation: (rotateLabels || isMobile.value) ? 45 : 0
        }
      }
    }
  }
}
