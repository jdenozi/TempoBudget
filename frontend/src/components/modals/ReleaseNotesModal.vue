<template>
  <n-modal
    :show="show"
    preset="card"
    :title="t('common.releaseNotes')"
    :style="{ width: isMobile ? '92vw' : '640px', maxHeight: '85vh' }"
    @update:show="(v: boolean) => emit('update:show', v)"
  >
    <n-flex v-if="loading" justify="center" style="padding: 40px;">
      <n-spin size="large" />
    </n-flex>

    <n-alert v-else-if="error" type="warning" :title="t('common.releaseNotesError')">
      <a :href="githubReleasesUrl" target="_blank" rel="noopener">{{ githubReleasesUrl }}</a>
    </n-alert>

    <n-empty v-else-if="releases.length === 0" :description="t('common.releaseNotesEmpty')" />

    <div v-else class="release-list">
      <div v-for="release in releases" :key="release.id" class="release-item">
        <n-flex justify="space-between" align="center" :wrap="true" :size="8" class="release-header">
          <n-flex align="center" :size="8">
            <strong class="release-title">{{ release.name || release.tag_name }}</strong>
            <n-tag size="small" type="info">{{ release.tag_name }}</n-tag>
            <n-tag v-if="release.prerelease" size="small" type="warning">pre-release</n-tag>
          </n-flex>
          <n-text depth="3" class="release-date">{{ formatDate(release.published_at) }}</n-text>
        </n-flex>
        <div class="release-body" v-html="renderBody(release.body)" />
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NFlex, NSpin, NAlert, NEmpty, NTag, NText } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useMobileDetect } from '@/composables/useMobileDetect'

interface GitHubRelease {
  id: number
  name: string | null
  tag_name: string
  body: string | null
  published_at: string
  prerelease: boolean
  html_url: string
}

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ (e: 'update:show', value: boolean): void }>()

const { t, locale } = useI18n()
const { isMobile } = useMobileDetect()

const githubReleasesUrl = 'https://github.com/jdenozi/TempoBudget/releases'
const releases = ref<GitHubRelease[]>([])
const loading = ref(false)
const error = ref(false)
let fetched = false

const fetchReleases = async () => {
  if (fetched) return
  loading.value = true
  error.value = false
  try {
    const res = await fetch('https://api.github.com/repos/jdenozi/TempoBudget/releases?per_page=30', {
      headers: { Accept: 'application/vnd.github+json' },
    })
    if (!res.ok) throw new Error(`GitHub API ${res.status}`)
    releases.value = await res.json()
    fetched = true
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

watch(() => props.show, (open) => {
  if (open) fetchReleases()
})

const formatDate = (iso: string) => {
  try {
    return new Date(iso).toLocaleDateString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  } catch {
    return iso
  }
}

const escapeHtml = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

const renderBody = (body: string | null): string => {
  if (!body) return `<p class="release-empty">—</p>`
  const lines = body.split(/\r?\n/)
  const out: string[] = []
  let inList = false
  const closeList = () => {
    if (inList) { out.push('</ul>'); inList = false }
  }
  for (const raw of lines) {
    const line = raw.trim()
    if (!line) { closeList(); continue }
    const h2 = line.match(/^##\s+(.*)$/)
    if (h2) { closeList(); out.push(`<h4>${escapeHtml(h2[1]!)}</h4>`); continue }
    const h3 = line.match(/^###\s+(.*)$/)
    if (h3) { closeList(); out.push(`<h5>${escapeHtml(h3[1]!)}</h5>`); continue }
    const bullet = line.match(/^[-*]\s+(.*)$/)
    if (bullet) {
      if (!inList) { out.push('<ul>'); inList = true }
      const content = escapeHtml(bullet[1]!).replace(
        /(https?:\/\/\S+)/g,
        '<a href="$1" target="_blank" rel="noopener">$1</a>',
      )
      out.push(`<li>${content}</li>`)
      continue
    }
    closeList()
    const linked = escapeHtml(line).replace(
      /(https?:\/\/\S+)/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>',
    )
    out.push(`<p>${linked}</p>`)
  }
  closeList()
  return out.join('\n')
}
</script>

<style scoped>
.release-list {
  max-height: 65vh;
  overflow-y: auto;
  padding-right: 4px;
}
.release-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--n-border-color);
}
.release-item:last-child {
  border-bottom: none;
}
.release-header {
  margin-bottom: 8px;
}
.release-title {
  font-size: 15px;
}
.release-date {
  font-size: 12px;
}
.release-body :deep(h4) {
  font-size: 13px;
  margin: 10px 0 4px;
  color: var(--n-text-color-2);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.release-body :deep(h5) {
  font-size: 13px;
  margin: 8px 0 4px;
}
.release-body :deep(ul) {
  margin: 0 0 8px;
  padding-left: 20px;
}
.release-body :deep(li) {
  margin: 2px 0;
  line-height: 1.45;
}
.release-body :deep(p) {
  margin: 4px 0;
  line-height: 1.45;
}
.release-body :deep(a) {
  color: var(--n-primary-color, #63e2b7);
  text-decoration: none;
}
.release-body :deep(a:hover) {
  text-decoration: underline;
}
.release-empty {
  color: var(--n-text-color-3);
}
</style>
