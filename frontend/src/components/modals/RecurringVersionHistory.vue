<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Recurring Transaction Version History

  Displays the version history timeline for a recurring transaction,
  showing all changes with their effective dates.
-->

<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      :title="t('versionHistory.title')"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '600px', maxHeight: '80vh', overflow: 'auto' }"
    >
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <n-spin size="large" />
      </div>

      <n-empty v-else-if="versions.length === 0" :description="t('versionHistory.noHistory')" />

      <n-timeline v-else>
        <n-timeline-item
          v-for="version in versions"
          :key="version.id"
          :type="getVersionType(version)"
          :title="getVersionTitle(version)"
          :time="formatDate(version.effective_from)"
        >
          <n-space vertical size="small">
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
              <span><strong>{{ t('transaction.amount') }}:</strong> {{ version.amount.toFixed(2) }} €</span>
              <span><strong>{{ t('category.title') }}:</strong> {{ getCategoryName(version.category_id) }}</span>
              <span><strong>{{ t('recurring.frequency') }}:</strong> {{ getFrequencyLabel(version.frequency) }}</span>
              <span v-if="version.day"><strong>{{ t('recurring.day') }}:</strong> {{ version.day }}</span>
            </div>

            <div v-if="version.change_reason" style="color: #888; font-style: italic;">
              "{{ version.change_reason }}"
            </div>

            <div v-if="version.effective_until" style="font-size: 12px; color: #888;">
              {{ t('versionHistory.until') }} {{ formatDate(version.effective_until) }}
            </div>

            <n-button
              v-if="isFutureVersion(version) && !version.effective_until"
              size="tiny"
              type="error"
              @click="handleCancel(version.id)"
            >
              {{ t('versionHistory.cancelChange') }}
            </n-button>
          </n-space>
        </n-timeline-item>
      </n-timeline>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">{{ t('common.close') }}</n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  NModal, NCard, NTimeline, NTimelineItem, NSpace, NButton, NSpin, NEmpty
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { RecurringTransactionVersion, Category } from '@/services/api'
import { recurringAPI } from '@/services/api'

const { t, locale } = useI18n()

interface Props {
  show: boolean
  isMobile: boolean
  recurringId: string | null
  categories: Category[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'cancel-version': [versionId: string, recurringId: string]
}>()

const loading = ref(false)
const versions = ref<RecurringTransactionVersion[]>([])

/** Load versions when modal opens */
watch(() => [props.show, props.recurringId], async ([show, id]) => {
  if (show && id) {
    loading.value = true
    try {
      versions.value = await recurringAPI.getVersions(id as string)
    } catch (error) {
      console.error('Error loading versions:', error)
      versions.value = []
    } finally {
      loading.value = false
    }
  }
}, { immediate: true })

/** Get today's date string */
const getToday = () => {
  const today = new Date()
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
}

/** Check if version is in the future */
const isFutureVersion = (version: RecurringTransactionVersion) => {
  return version.effective_from > getToday()
}

/** Check if version is currently active */
const isActiveVersion = (version: RecurringTransactionVersion) => {
  const today = getToday()
  return version.effective_from <= today && !version.effective_until
}

/** Get timeline item type based on version status */
const getVersionType = (version: RecurringTransactionVersion): 'success' | 'warning' | 'default' => {
  if (isFutureVersion(version)) return 'warning'
  if (isActiveVersion(version)) return 'success'
  return 'default'
}

/** Get version title based on status */
const getVersionTitle = (version: RecurringTransactionVersion) => {
  if (isFutureVersion(version)) return `${t('versionHistory.scheduled')}: ${version.title}`
  if (isActiveVersion(version)) return `${t('versionHistory.current')}: ${version.title}`
  return version.title
}

/** Format date string */
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/** Get frequency label */
const getFrequencyLabel = (frequency: string) => {
  const labels: Record<string, string> = {
    monthly: t('recurring.monthly'),
    weekly: t('recurring.weekly'),
    yearly: t('recurring.yearly'),
  }
  return labels[frequency] || frequency
}

/** Get category name by ID */
const getCategoryName = (categoryId: string) => {
  const category = props.categories.find(c => c.id === categoryId)
  if (!category) return t('versionHistory.unknown')

  if (category.parent_id) {
    const parent = props.categories.find(c => c.id === category.parent_id)
    if (parent) return `${parent.name} > ${category.name}`
  }

  return category.name
}

/** Handle cancel version */
const handleCancel = (versionId: string) => {
  if (props.recurringId) {
    emit('cancel-version', versionId, props.recurringId)
  }
}
</script>
