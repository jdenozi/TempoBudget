/**
 * Tests for useAvatar composable
 */
import { describe, it, expect } from 'vitest'
import { getAvatarUrl, type AvatarStyle } from '../composables/useAvatar'

describe('useAvatar', () => {
  describe('getAvatarUrl', () => {
    it('returns a valid DiceBear URL with default style', () => {
      const url = getAvatarUrl('test-seed')
      expect(url).toContain('https://api.dicebear.com/7.x/initials/svg')
      expect(url).toContain('seed=test-seed')
    })

    it('encodes special characters in seed', () => {
      const url = getAvatarUrl('John Doe')
      expect(url).toContain('seed=John%20Doe')
    })

    it('uses custom style when provided', () => {
      const styles: AvatarStyle[] = ['bottts', 'avataaars', 'lorelei', 'micah', 'notionists']

      styles.forEach(style => {
        const url = getAvatarUrl('test', style)
        expect(url).toContain(`/7.x/${style}/svg`)
      })
    })

    it('uses custom size when provided', () => {
      const url = getAvatarUrl('test', 'initials', 120)
      expect(url).toContain('size=120')
    })

    it('includes background color options', () => {
      const url = getAvatarUrl('test')
      expect(url).toContain('backgroundColor=')
    })

    it('trims whitespace from seed', () => {
      const url = getAvatarUrl('  test  ')
      expect(url).toContain('seed=test')
    })

    it('handles empty seed gracefully', () => {
      const url = getAvatarUrl('')
      expect(url).toContain('seed=')
      expect(url).toBeDefined()
    })
  })
})
