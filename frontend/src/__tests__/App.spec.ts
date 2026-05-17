/**
 * Basic app mounting test
 * Note: Full component tests require Pinia and Router setup
 */
import { describe, it, expect } from 'vitest'

describe('App', () => {
  it('app module can be imported', async () => {
    // Just verify the module doesn't throw on import
    // Full mounting tests require router and pinia mocking
    const module = await import('../App.vue')
    expect(module.default).toBeDefined()
  })
})
