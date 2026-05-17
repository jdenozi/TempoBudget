/**
 * Composable for generating user avatars using DiceBear API.
 * No uploads needed - avatars are generated from the user's name.
 */

export type AvatarStyle = 'initials' | 'bottts' | 'avataaars' | 'lorelei' | 'micah' | 'notionists'

const DEFAULT_STYLE: AvatarStyle = 'initials'

/**
 * Generate a DiceBear avatar URL.
 * @param seed - The seed for avatar generation (usually user name or email)
 * @param style - The avatar style to use
 * @param size - The size in pixels (default 80)
 */
export function getAvatarUrl(seed: string, style: AvatarStyle = DEFAULT_STYLE, size: number = 80): string {
  if (!seed || seed.trim() === '') {
    seed = 'User'
  }
  const encodedSeed = encodeURIComponent(seed.trim())
  return `https://api.dicebear.com/7.x/${style}/svg?seed=${encodedSeed}&size=${size}&backgroundColor=1a1a2e,2a2a3e,3a3a4e`
}

/**
 * Get available avatar styles with labels.
 */
export function getAvatarStyles(): { value: AvatarStyle; label: string }[] {
  return [
    { value: 'initials', label: 'Initiales' },
    { value: 'bottts', label: 'Robots' },
    { value: 'avataaars', label: 'Avatars' },
    { value: 'lorelei', label: 'Lorelei' },
    { value: 'micah', label: 'Micah' },
    { value: 'notionists', label: 'Notionists' },
  ]
}

export function useAvatar() {
  return {
    getAvatarUrl,
    getAvatarStyles,
  }
}
