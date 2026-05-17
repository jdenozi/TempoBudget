<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Admin Quotes View

  Quote management for prospects.
-->

<template>
  <n-space vertical size="large">
    <n-flex justify="space-between" align="center" wrap>
      <h1 class="page-title">{{ t('admin.quotes') }}</h1>
      <n-button type="primary" @click="showCreateModal = true">
        {{ t('admin.createQuote') }}
      </n-button>
    </n-flex>

    <n-spin :show="loading">
      <n-data-table
        :columns="columns"
        :data="quotes"
        :pagination="pagination"
        :row-key="(row) => row.id"
      />
    </n-spin>

    <!-- Create/Edit Quote Modal -->
    <n-modal v-model:show="showCreateModal" @after-leave="resetForm">
      <n-card
        :title="editingQuote ? t('admin.editQuote') : t('admin.createQuote')"
        :bordered="false"
        size="huge"
        class="quote-modal"
      >
        <n-form ref="formRef" :model="quoteForm" :rules="rules">
          <n-form-item :label="t('admin.prospectName')" path="prospect_name">
            <n-input v-model:value="quoteForm.prospect_name" />
          </n-form-item>
          <n-form-item :label="t('admin.prospectEmail')" path="prospect_email">
            <n-input v-model:value="quoteForm.prospect_email" />
          </n-form-item>
          <n-form-item :label="t('admin.prospectCompany')">
            <n-input v-model:value="quoteForm.prospect_company" />
          </n-form-item>
          <n-grid :cols="2" :x-gap="16">
            <n-gi>
              <n-form-item :label="t('admin.planType')" path="plan_type">
                <n-select
                  v-model:value="quoteForm.plan_type"
                  :options="planOptions"
                />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item :label="t('admin.quantity')" path="quantity">
                <n-input-number v-model:value="quoteForm.quantity" :min="1" style="width: 100%;" />
              </n-form-item>
            </n-gi>
          </n-grid>
          <n-form-item :label="t('admin.unitPrice')" path="unit_price">
            <n-input-number
              v-model:value="quoteForm.unit_price"
              :min="0"
              :precision="2"
              style="width: 100%;"
            >
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>
          <n-form-item v-if="!editingQuote" :label="t('admin.validDays')">
            <n-input-number v-model:value="quoteForm.valid_days" :min="1" :max="365" style="width: 100%;" />
          </n-form-item>
          <n-form-item v-if="editingQuote" :label="t('admin.status')">
            <n-select
              v-model:value="quoteForm.status"
              :options="statusOptions"
            />
          </n-form-item>
          <n-form-item :label="t('admin.notes')">
            <n-input v-model:value="quoteForm.notes" type="textarea" :rows="3" />
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showCreateModal = false">{{ t('common.cancel') }}</n-button>
            <n-button type="primary" :loading="saving" @click="handleSave">
              {{ editingQuote ? t('common.save') : t('common.create') }}
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NSpace, NFlex, NCard, NButton, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NGrid, NGi, NTag, NIcon, NSpin,
  useMessage, type DataTableColumns, type FormInst, type FormRules
} from 'naive-ui'
import { CreateOutline, TrashOutline, DownloadOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { adminAPI, type AdminQuote } from '@/services/api'

const { t, locale } = useI18n()
const message = useMessage()

const loading = ref(false)
const saving = ref(false)
const quotes = ref<AdminQuote[]>([])
const showCreateModal = ref(false)
const editingQuote = ref<AdminQuote | null>(null)
const formRef = ref<FormInst | null>(null)

const pagination = {
  pageSize: 20,
}

const planOptions = [
  { label: t('subscription.monthly'), value: 'monthly' },
  { label: t('subscription.annual'), value: 'annual' },
]

const statusOptions = [
  { label: t('admin.statusDraft'), value: 'draft' },
  { label: t('admin.statusSent'), value: 'sent' },
  { label: t('admin.statusAccepted'), value: 'accepted' },
  { label: t('admin.statusExpired'), value: 'expired' },
]

const quoteForm = ref({
  prospect_name: '',
  prospect_email: '',
  prospect_company: '',
  plan_type: 'monthly' as 'monthly' | 'annual',
  quantity: 1,
  unit_price: 5.99,
  valid_days: 30,
  notes: '',
  status: 'draft' as 'draft' | 'sent' | 'accepted' | 'expired',
})

const rules: FormRules = {
  prospect_name: [{ required: true, message: t('admin.prospectNameRequired') }],
  prospect_email: [
    { required: true, message: t('admin.prospectEmailRequired') },
    { type: 'email', message: t('admin.invalidEmail') },
  ],
  plan_type: [{ required: true }],
  quantity: [{ required: true, type: 'number', min: 1 }],
  unit_price: [{ required: true, type: 'number', min: 0 }],
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'accepted':
      return 'success'
    case 'sent':
      return 'info'
    case 'expired':
      return 'error'
    default:
      return 'default'
  }
}

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    style: 'currency',
    currency: 'EUR',
  }).format(value)
}

const columns = computed<DataTableColumns<AdminQuote>>(() => [
  {
    title: t('admin.prospect'),
    key: 'prospect_name',
    render: (row) => h('div', [
      h('div', { style: { fontWeight: 500 } }, row.prospect_name),
      h('div', { style: { fontSize: '12px', color: 'var(--n-text-color-3)' } }, row.prospect_email),
    ]),
  },
  {
    title: t('admin.plan'),
    key: 'plan_type',
    width: 100,
    render: (row) => row.plan_type === 'annual' ? t('subscription.annual') : t('subscription.monthly'),
  },
  {
    title: t('admin.total'),
    key: 'total',
    width: 100,
    render: (row) => formatCurrency(row.total),
  },
  {
    title: t('admin.status'),
    key: 'status',
    width: 100,
    render: (row) => h(NTag, { type: getStatusType(row.status), size: 'small' }, () => t(`admin.status${row.status.charAt(0).toUpperCase() + row.status.slice(1)}`)),
  },
  {
    title: t('admin.validUntil'),
    key: 'valid_until',
    width: 120,
    render: (row) => formatDate(row.valid_until),
  },
  {
    title: t('common.actions'),
    key: 'actions',
    width: 150,
    render: (row) => h(NSpace, { size: 'small' }, () => [
      h(NButton, {
        size: 'small',
        quaternary: true,
        onClick: () => handleEdit(row)
      }, { icon: () => h(NIcon, { component: CreateOutline }) }),
      h(NButton, {
        size: 'small',
        quaternary: true,
        onClick: () => handleDownloadPdf(row.id)
      }, { icon: () => h(NIcon, { component: DownloadOutline }) }),
      h(NButton, {
        size: 'small',
        quaternary: true,
        type: 'error',
        onClick: () => handleDelete(row.id)
      }, { icon: () => h(NIcon, { component: TrashOutline }) }),
    ]),
  },
])

const resetForm = () => {
  editingQuote.value = null
  quoteForm.value = {
    prospect_name: '',
    prospect_email: '',
    prospect_company: '',
    plan_type: 'monthly',
    quantity: 1,
    unit_price: 5.99,
    valid_days: 30,
    notes: '',
    status: 'draft',
  }
}

const handleEdit = (quote: AdminQuote) => {
  editingQuote.value = quote
  quoteForm.value = {
    prospect_name: quote.prospect_name,
    prospect_email: quote.prospect_email,
    prospect_company: quote.prospect_company || '',
    plan_type: quote.plan_type,
    quantity: quote.quantity,
    unit_price: quote.unit_price,
    valid_days: 30,
    notes: quote.notes || '',
    status: quote.status,
  }
  showCreateModal.value = true
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    if (editingQuote.value) {
      const updated = await adminAPI.updateQuote(editingQuote.value.id, {
        prospect_name: quoteForm.value.prospect_name,
        prospect_email: quoteForm.value.prospect_email,
        prospect_company: quoteForm.value.prospect_company || undefined,
        plan_type: quoteForm.value.plan_type,
        quantity: quoteForm.value.quantity,
        unit_price: quoteForm.value.unit_price,
        notes: quoteForm.value.notes || undefined,
        status: quoteForm.value.status,
      })
      const index = quotes.value.findIndex(q => q.id === updated.id)
      if (index !== -1) quotes.value[index] = updated
      message.success(t('admin.quoteUpdated'))
    } else {
      const created = await adminAPI.createQuote({
        prospect_name: quoteForm.value.prospect_name,
        prospect_email: quoteForm.value.prospect_email,
        prospect_company: quoteForm.value.prospect_company || undefined,
        plan_type: quoteForm.value.plan_type,
        quantity: quoteForm.value.quantity,
        unit_price: quoteForm.value.unit_price,
        valid_days: quoteForm.value.valid_days,
        notes: quoteForm.value.notes || undefined,
      })
      quotes.value.unshift(created)
      message.success(t('admin.quoteCreated'))
    }
    showCreateModal.value = false
  } catch (error) {
    console.error('Error saving quote:', error)
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await adminAPI.deleteQuote(id)
    quotes.value = quotes.value.filter(q => q.id !== id)
    message.success(t('admin.quoteDeleted'))
  } catch (error) {
    console.error('Error deleting quote:', error)
    message.error(t('errors.generic'))
  }
}

const handleDownloadPdf = async (id: string) => {
  try {
    const blob = await adminAPI.downloadQuotePdf(id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `devis-${id.slice(0, 8)}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error downloading PDF:', error)
    message.error(t('errors.generic'))
  }
}

onMounted(async () => {
  loading.value = true
  try {
    quotes.value = await adminAPI.getQuotes()
  } catch (error) {
    console.error('Error loading quotes:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title {
  margin: 0;
  font-size: clamp(20px, 5vw, 28px);
}

.quote-modal {
  width: 500px;
  max-width: 95vw;
}
</style>
