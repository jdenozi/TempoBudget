/**
 * Storybook main configuration for Tempo Budget frontend.
 *
 * This file configures Storybook to work with Vue 3, Vite, and the project's
 * component library (Naive UI).
 */

import type { StorybookConfig } from '@storybook/vue3-vite'

const config: StorybookConfig = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: [
    '@storybook/addon-onboarding',
    '@storybook/addon-essentials',
    '@chromatic-com/storybook',
    '@storybook/addon-interactions',
    '@storybook/addon-links',
  ],
  framework: {
    name: '@storybook/vue3-vite',
    options: {},
  },
  docs: {},
  viteFinal: async (config) => {
    // Add any custom Vite configuration here
    return config
  },
}

export default config
