<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Edit Recurring Transaction Modal

  Modal for editing recurring transaction properties with optional
  effective date for scheduling future changes.
-->

<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      :title="t('recurring.editRecurring')"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '500px' }"
    >
      <n-form :model="formData">
        <n-form-item :label="t('transaction.transactionTitle')">
          <n-input v-model:value="formData.title" :placeholder="t('transaction.transactionTitle')" />
        </n-form-item>

        <n-form-item :label="t('transaction.amount')">
          <n-input-number
            v-model:value="formData.amount"
            :min="0.01"
            :precision="2"
            style="width: 100%;"
          >
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>

        <n-form-item :label="t('category.title')">
          <n-select
            v-model:value="formData.category_id"
            :options="parentCategoryOptions"
            :placeholder="t('placeholders.selectCategory')"
            @update:value="handleCategoryChange"
          />
        </n-form-item>

        <n-form-item v-if="subcategoryOptions.length > 0" :label="t('category.subcategory')">
          <n-select
            v-model:value="formData.subcategory_id"
            :options="subcategoryOptions"
            :placeholder="t('placeholders.selectSubcategory')"
            clearable
          />
        </n-form-item>

        <n-form-item :label="t('recurring.frequency')">
          <n-select
            v-model:value="formData.frequency"
            :options="frequencyOptions"
            :placeholder="t('placeholders.selectFrequency')"
          />
        </n-form-item>

        <n-form-item v-if="formData.frequency === 'monthly'" :label="t('recurring.dayOfMonth')">
          <n-input-number
            v-model:value="formData.day"
            :min="1"
            :max="31"
            style="width: 100%;"
          />
        </n-form-item>

        <n-form-item v-if="formData.frequency === 'weekly'" :label="t('recurring.dayOfWeek')">
          <n-select
            v-model:value="formData.day"
            :options="weekDayOptions"
            :placeholder="t('recurring.dayOfWeek')"
          />
        </n-form-item>

        <n-divider />

        <n-form-item :label="t('recurring.effectiveDate')">
          <n-date-picker
            v-model:value="formData.effective_date_timestamp"
            type="date"
            style="width: 100%;"
            :is-date-disabled="isDateDisabled"
          />
          <template #feedback>
            <span v-if="isFutureDate" style="color: #f0a020;">
              {{ t('recurring.scheduledChange') }} {{ formatDate(formData.effective_date_timestamp) }}
            </span>
            <span v-else style="color: #18a058;">
              {{ t('recurring.immediateChange') }}
            </span>
          </template>
        </n-form-item>

        <n-form-item :label="t('recurring.changeReason') + ' (' + t('common.pending').toLowerCase() + ')'">
          <n-input
            v-model:value="formData.change_reason"
            type="textarea"
            :placeholder="t('placeholders.changeReason')"
            :rows="2"
          />
        </n-form-item>
      </n-form>

      <n-alert v-if="recurring?.pending_version" type="warning" style="margin-bottom: 16px;">
        {{ t('versionHistory.pendingWarning', { date: recurring.pending_version.effective_from }) }}
      </n-alert>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            {{ t('common.save') }}
          </n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  NModal, NCard, NForm, NFormItem, NInput, NInputNumber,
  NSelect, NDatePicker, NDivider, NAlert, NSpace, NButton
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { RecurringTransactionWithCategory, Category, UpdateRecurringTransactionPayload } from '@/services/api'

const { t } = useI18n()

interface Props {
  show: boolean
  isMobile: boolean
  loading: boolean
  recurring: RecurringTransactionWithCategory | null
  categories: Category[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: UpdateRecurringTransactionPayload]
}>()

interface FormData {
  title: string
  amount: number
  category_id: string | null
  subcategory_id: string | null
  frequency: string
  day: number | null
  effective_date_timestamp: number | null
  change_reason: string
}

const formData = ref<FormData>({
  title: '',
  amount: 0,
  category_id: null,
  subcategory_id: null,
  frequency: 'monthly',
  day: 1,
  effective_date_timestamp: Date.now(),
  change_reason: '',
})

/** Frequency options */
const frequencyOptions = computed(() => [
  { label: t('recurring.monthly'), value: 'monthly' },
  { label: t('recurring.weekly'), value: 'weekly' },
  { label: t('recurring.yearly'), value: 'yearly' },
])

/** Week day options */
const weekDayOptions = computed(() => [
  { label: t('days.monday'), value: 0 },
  { label: t('days.tuesday'), value: 1 },
  { label: t('days.wednesday'), value: 2 },
  { label: t('days.thursday'), value: 3 },
  { label: t('days.friday'), value: 4 },
  { label: t('days.saturday'), value: 5 },
  { label: t('days.sunday'), value: 6 },
])

/** Parent category options */
const parentCategoryOptions = computed(() => {
  return props.categories
    .filter(c => !c.parent_id)
    .map(c => ({ label: c.name, value: c.id }))
})

/** Subcategory options based on selected parent */
const subcategoryOptions = computed(() => {
  if (!formData.value.category_id) return []
  return props.categories
    .filter(c => c.parent_id === formData.value.category_id)
    .map(c => ({ label: c.name, value: c.id }))
})

/** Whether the selected date is in the future */
const isFutureDate = computed(() => {
  if (!formData.value.effective_date_timestamp) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return formData.value.effective_date_timestamp > today.getTime()
})

/** Disable dates in the past */
const isDateDisabled = (ts: number) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return ts < today.getTime()
}

/** Format timestamp to date string */
const formatDate = (ts: number | null) => {
  if (!ts) return ''
  return new Date(ts).toLocaleDateString()
}

/** Format timestamp to ISO date string */
const formatDateISO = (ts: number | null) => {
  if (!ts) return undefined
  const date = new Date(ts)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

/** Watch for recurring changes and populate form */
watch(() => props.recurring, (newVal) => {
  if (newVal) {
    // Determine parent and subcategory IDs
    let parentId = newVal.category_id
    let subId: string | null = null

    if (newVal.parent_category_id) {
      // Current category is a subcategory
      parentId = newVal.parent_category_id
      subId = newVal.category_id
    }

    formData.value = {
      title: newVal.title,
      amount: newVal.amount,
      category_id: parentId,
      subcategory_id: subId,
      frequency: newVal.frequency,
      day: newVal.day || 1,
      effective_date_timestamp: Date.now(),
      change_reason: '',
    }
  }
}, { immediate: true })

/** Handle category change - reset subcategory */
const handleCategoryChange = () => {
  formData.value.subcategory_id = null
}

/** Handle form submission */
const handleSubmit = () => {
  // Use subcategory if selected, otherwise use parent
  const categoryId = formData.value.subcategory_id || formData.value.category_id

  const payload: UpdateRecurringTransactionPayload = {
    title: formData.value.title,
    amount: formData.value.amount,
    category_id: categoryId || undefined,
    frequency: formData.value.frequency,
    day: formData.value.day || undefined,
    effective_date: formatDateISO(formData.value.effective_date_timestamp),
    change_reason: formData.value.change_reason || undefined,
  }

  emit('submit', payload)
}
</script>
