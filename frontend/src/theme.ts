import type { GlobalThemeOverrides } from 'naive-ui'

const ACCENT = '#10b981'
const ACCENT_HOVER = '#34d399'
const ACCENT_PRESSED = '#059669'

export const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: ACCENT,
    primaryColorHover: ACCENT_HOVER,
    primaryColorPressed: ACCENT_PRESSED,
    primaryColorSuppl: ACCENT_HOVER,

    infoColor: '#3b82f6',
    infoColorHover: '#60a5fa',
    infoColorPressed: '#2563eb',
    infoColorSuppl: '#60a5fa',

    successColor: '#22c55e',
    successColorHover: '#4ade80',
    successColorPressed: '#16a34a',
    successColorSuppl: '#4ade80',

    warningColor: '#f59e0b',
    warningColorHover: '#fbbf24',
    warningColorPressed: '#d97706',
    warningColorSuppl: '#fbbf24',

    errorColor: '#ef4444',
    errorColorHover: '#f87171',
    errorColorPressed: '#dc2626',
    errorColorSuppl: '#f87171',

    borderRadius: '8px',
    borderRadiusSmall: '6px',

    fontFamily:
      'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontFamilyMono: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',

    fontWeightStrong: '600',
  },
  Card: {
    borderRadius: '12px',
    paddingMedium: '18px 22px',
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusSmall: '6px',
    borderRadiusTiny: '4px',
    fontWeight: '500',
    fontWeightStrong: '600',
  },
  Modal: {
    peers: {
      Card: {
        borderRadius: '14px',
      },
    },
  },
  Tag: {
    borderRadius: '6px',
  },
  Input: {
    borderRadius: '8px',
  },
  Menu: {
    borderRadius: '8px',
    itemHeight: '42px',
  },
  Progress: {
    railHeight: '10px',
  },
  DataTable: {
    borderRadius: '10px',
  },
  Drawer: {
    bodyPadding: '20px',
  },
}
