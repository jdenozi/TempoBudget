/**
 * Storybook preview configuration for Tempo Budget frontend.
 *
 * This file sets up global decorators, parameters, and the Naive UI
 * provider for all stories.
 */

import type { Preview } from '@storybook/vue3'
import { setup } from '@storybook/vue3'
import { createPinia } from 'pinia'
import naive from 'naive-ui'

// Create Pinia instance for stores
const pinia = createPinia()

// Setup global Vue plugins
setup((app) => {
  app.use(pinia)
  app.use(naive)
})

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    docs: {
      toc: true,
    },
  },
  tags: ['autodocs'],
}

export default preview
