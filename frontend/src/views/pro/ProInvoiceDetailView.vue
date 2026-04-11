<template>
  <n-space vertical :size="16">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <n-button text @click="$router.push({ name: 'pro-invoices' })">← {{ t('common.back') }}</n-button>
        <h2 style="margin: 0;">{{ isNew ? t('pro.invoices.addInvoice') : `${t('pro.invoices.editInvoice')} ${invoice?.invoice_number || ''}` }}</h2>
        <n-tag v-if="invoice" :type="statusTagType(invoice.status)" size="small">{{ t(`pro.invoices.${invoice.status}`) }}</n-tag>
      </div>
      <n-space v-if="invoice" :size="8">
        <n-button v-if="invoice.status === 'draft'" type="info" @click="handleStatusChange('sent')">{{ t('pro.invoices.sent') }}</n-button>
        <n-button v-if="invoice.status === 'sent'" type="success" @click="showPayModal = true">{{ t('pro.invoices.paid') }}</n-button>
        <n-button v-if="invoice.status === 'sent'" @click="handleReminder">{{ t('pro.invoices.sendReminder') }}</n-button>
        <n-button v-if="invoice.status !== 'cancelled' && invoice.status !== 'paid'" type="error" quaternary @click="handleStatusChange('cancelled')">{{ t('pro.invoices.cancelled') }}</n-button>
        <n-button type="info" @click="handleDownloadPdf">PDF</n-button>
        <n-button @click="showSettingsModal = true">⚙</n-button>
      </n-space>
    </div>

    <!-- Form -->
    <n-card>
      <n-space vertical :size="16">
        <n-grid :cols="isMobile ? 1 : 3" :x-gap="16" :y-gap="12">
          <n-gi>
            <n-form-item :label="t('pro.invoices.client')">
              <n-select
                v-model:value="form.client_id"
                :options="clientOptions"
                filterable
                :disabled="!isDraft"
              />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item :label="t('pro.invoices.issueDate')">
              <n-date-picker v-model:value="issueDateTs" type="date" :disabled="!isDraft" style="width: 100%;" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item :label="t('pro.invoices.dueDate')">
              <n-date-picker v-model:value="dueDateTs" type="date" :disabled="!isDraft" style="width: 100%;" />
            </n-form-item>
          </n-gi>
        </n-grid>

        <!-- Items -->
        <h3 style="margin: 0;">{{ t('pro.invoices.items') }}</h3>
        <n-space vertical :size="8">
          <n-card v-for="(item, idx) in form.items" :key="idx" size="small">
            <n-grid :cols="isMobile ? 1 : 12" :x-gap="8" :y-gap="8" style="align-items: end;">
              <n-gi :span="isMobile ? 1 : 4">
                <n-form-item :label="t('pro.invoices.description')" :show-feedback="false">
                  <n-input v-model:value="item.description" :disabled="!isDraft" />
                </n-form-item>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 2">
                <n-form-item label="Produit" :show-feedback="false">
                  <n-select
                    v-model:value="item.product_id"
                    :options="productOptions"
                    clearable
                    filterable
                    :disabled="!isDraft"
                    @update:value="(v: string) => onProductSelect(idx, v)"
                  />
                </n-form-item>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 2">
                <n-form-item :label="t('pro.invoices.quantity')" :show-feedback="false">
                  <n-input-number v-model:value="item.quantity" :min="0.01" :step="1" :disabled="!isDraft" style="width: 100%;" />
                </n-form-item>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 2">
                <n-form-item :label="t('pro.invoices.unitPrice')" :show-feedback="false">
                  <n-input-number v-model:value="item.unit_price" :min="0" :step="0.01" :disabled="!isDraft" style="width: 100%;">
                    <template #suffix>€</template>
                  </n-input-number>
                </n-form-item>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 1">
                <div style="text-align: right; font-weight: bold; padding-top: 24px;">
                  {{ (item.quantity * item.unit_price).toFixed(2) }} €
                </div>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 1">
                <n-button v-if="isDraft" text type="error" @click="form.items.splice(idx, 1)" style="padding-top: 24px;">✕</n-button>
              </n-gi>
            </n-grid>
          </n-card>
          <n-button v-if="isDraft" dashed block @click="addItem">{{ t('pro.invoices.addItem') }}</n-button>
        </n-space>

        <!-- Discount + Notes -->
        <n-grid :cols="isMobile ? 1 : 2" :x-gap="16" :y-gap="12">
          <n-gi>
            <n-form-item :label="t('pro.invoices.discount')">
              <n-space :size="8" style="width: 100%;">
                <n-select
                  v-model:value="form.discount_type"
                  :options="[{ label: '-', value: null }, { label: '%', value: 'percentage' }, { label: '€', value: 'fixed' }]"
                  :disabled="!isDraft"
                  style="width: 80px;"
                />
                <n-input-number v-if="form.discount_type" v-model:value="form.discount_value" :min="0" :disabled="!isDraft" style="flex: 1;" />
              </n-space>
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item :label="t('pro.invoices.notes')">
              <n-input v-model:value="form.notes" type="textarea" :rows="2" :disabled="!isDraft" />
            </n-form-item>
          </n-gi>
        </n-grid>

        <!-- Totals -->
        <div style="text-align: right; font-size: 16px;">
          <div>{{ t('pro.invoices.subtotal') }}: <strong>{{ computedSubtotal.toFixed(2) }} €</strong></div>
          <div v-if="form.discount_type" style="color: #f0a020;">
            {{ t('pro.invoices.discount') }}: -{{ computedDiscount.toFixed(2) }} €
          </div>
          <div style="font-size: 20px; margin-top: 4px;">
            {{ t('pro.invoices.total') }}: <strong>{{ computedTotal.toFixed(2) }} €</strong>
          </div>
        </div>

        <n-button v-if="isDraft" type="primary" block @click="handleSave" :loading="saving">
          {{ t('common.save') }}
        </n-button>
      </n-space>
    </n-card>

    <!-- Pay Modal -->
    <n-modal v-model:show="showPayModal" preset="dialog" :title="t('pro.invoices.paid')">
      <n-space vertical :size="12">
        <n-form-item :label="t('pro.invoices.paymentMethod')">
          <n-select v-model:value="payForm.payment_method" :options="paymentMethodOptions" />
        </n-form-item>
        <n-form-item :label="t('pro.invoices.paidDate')">
          <n-date-picker v-model:value="payDateTs" type="date" style="width: 100%;" />
        </n-form-item>
      </n-space>
      <template #action>
        <n-button type="success" @click="handlePay">{{ t('common.confirm') }}</n-button>
      </template>
    </n-modal>

    <!-- Settings Modal -->
    <n-modal v-model:show="showSettingsModal" preset="card" :title="t('pro.invoiceSettings.title')" style="max-width: 500px;">
      <n-space vertical :size="12">
        <n-grid :cols="2" :x-gap="12" :y-gap="12">
          <n-gi><n-form-item :label="t('pro.invoiceSettings.invoicePrefix')"><n-input v-model:value="settingsForm.invoice_prefix" /></n-form-item></n-gi>
          <n-gi><n-form-item :label="t('pro.invoiceSettings.quotePrefix')"><n-input v-model:value="settingsForm.quote_prefix" /></n-form-item></n-gi>
          <n-gi><n-form-item :label="t('pro.invoiceSettings.paymentTerms')"><n-input-number v-model:value="settingsForm.payment_terms_days" :min="0" style="width: 100%;" /></n-form-item></n-gi>
          <n-gi><n-form-item :label="t('pro.invoiceSettings.latePenaltyRate')"><n-input-number v-model:value="settingsForm.late_penalty_rate" :min="0" :step="0.1" style="width: 100%;" /></n-form-item></n-gi>
        </n-grid>
        <n-form-item :label="t('pro.invoiceSettings.bankName')"><n-input v-model:value="settingsForm.bank_name" /></n-form-item>
        <n-form-item :label="t('pro.invoiceSettings.bankIban')"><n-input v-model:value="settingsForm.bank_iban" /></n-form-item>
        <n-form-item :label="t('pro.invoiceSettings.bankBic')"><n-input v-model:value="settingsForm.bank_bic" /></n-form-item>
        <n-form-item :label="t('pro.invoiceSettings.defaultNotes')"><n-input v-model:value="settingsForm.default_notes" type="textarea" :rows="2" /></n-form-item>
        <n-button type="primary" block @click="handleSaveSettings">{{ t('common.save') }}</n-button>
      </n-space>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NSpace, NButton, NCard, NGrid, NGi, NFormItem, NInput, NInputNumber,
  NSelect, NDatePicker, NTag, NModal, useMessage,
} from 'naive-ui'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProInvoice } from '@/services/api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const isNew = computed(() => route.name === 'pro-invoice-new')
const invoice = ref<ProInvoice | null>(null)
const saving = ref(false)
const showPayModal = ref(false)
const showSettingsModal = ref(false)

const isDraft = computed(() => isNew.value || invoice.value?.status === 'draft')

interface ItemForm {
  product_id: string | null
  description: string
  quantity: number
  unit_price: number
}

const form = ref({
  client_id: null as string | null,
  issue_date: new Date().toISOString().slice(0, 10),
  due_date: '',
  discount_type: null as string | null,
  discount_value: 0,
  notes: '',
  items: [] as ItemForm[],
})

const issueDateTs = computed({
  get: () => form.value.issue_date ? new Date(form.value.issue_date).getTime() : null,
  set: (v) => { if (v) form.value.issue_date = new Date(v).toISOString().slice(0, 10) },
})
const dueDateTs = computed({
  get: () => form.value.due_date ? new Date(form.value.due_date).getTime() : null,
  set: (v) => { if (v) form.value.due_date = new Date(v).toISOString().slice(0, 10) },
})

const payForm = ref({ payment_method: 'bankTransfer' })
const payDateTs = ref(Date.now())

const settingsForm = ref({
  invoice_prefix: 'F', quote_prefix: 'D',
  payment_terms_days: 30, late_penalty_rate: 3.0,
  bank_name: '', bank_iban: '', bank_bic: '', default_notes: '',
})

const clientOptions = computed(() => proStore.proClients.map(c => ({ label: c.name, value: c.id })))
const productOptions = computed(() => proStore.proProducts.map(p => ({ label: `${p.name} (${p.default_price.toFixed(2)} €)`, value: p.id })))
const paymentMethodOptions = [
  { label: 'Virement', value: 'bankTransfer' },
  { label: 'Espèces', value: 'cash' },
  { label: 'Chèque', value: 'check' },
  { label: 'Carte', value: 'card' },
  { label: 'PayPal', value: 'paypal' },
]

function statusTagType(status: string) {
  const map: Record<string, 'default' | 'info' | 'success' | 'error'> = { draft: 'default', sent: 'info', paid: 'success', cancelled: 'error' }
  return map[status] || 'default'
}

const computedSubtotal = computed(() => form.value.items.reduce((s, i) => s + i.quantity * i.unit_price, 0))
const computedDiscount = computed(() => {
  if (form.value.discount_type === 'percentage') return computedSubtotal.value * (form.value.discount_value || 0) / 100
  if (form.value.discount_type === 'fixed') return form.value.discount_value || 0
  return 0
})
const computedTotal = computed(() => Math.max(computedSubtotal.value - computedDiscount.value, 0))

function addItem() {
  form.value.items.push({ product_id: null, description: '', quantity: 1, unit_price: 0 })
}

function onProductSelect(idx: number, productId: string) {
  const product = proStore.proProducts.find(p => p.id === productId)
  if (product) {
    form.value.items[idx].description = product.name
    form.value.items[idx].unit_price = product.default_price
  }
}

async function handleSave() {
  if (!form.value.client_id || form.value.items.length === 0) {
    message.warning(t('errors.required'))
    return
  }
  saving.value = true
  try {
    const data = {
      client_id: form.value.client_id,
      issue_date: form.value.issue_date,
      due_date: form.value.due_date,
      discount_type: form.value.discount_type as 'percentage' | 'fixed' | undefined,
      discount_value: form.value.discount_value,
      notes: form.value.notes || undefined,
      items: form.value.items.map(i => ({
        product_id: i.product_id || undefined,
        description: i.description,
        quantity: i.quantity,
        unit_price: i.unit_price,
      })),
    }
    if (isNew.value) {
      const inv = await proStore.createInvoice(data)
      message.success(t('pro.invoices.invoiceCreated'))
      router.replace({ name: 'pro-invoice-detail', params: { id: inv.id } })
    } else {
      await proStore.updateInvoice(invoice.value!.id, data)
      message.success(t('pro.invoices.invoiceUpdated'))
      await loadInvoice()
    }
  } finally {
    saving.value = false
  }
}

async function handleStatusChange(status: string) {
  await proStore.updateInvoiceStatus(invoice.value!.id, { status })
  message.success(t('pro.invoices.statusUpdated'))
  await loadInvoice()
}

async function handlePay() {
  await proStore.updateInvoiceStatus(invoice.value!.id, {
    status: 'paid',
    payment_method: payForm.value.payment_method,
    paid_date: new Date(payDateTs.value).toISOString().slice(0, 10),
  })
  showPayModal.value = false
  message.success(t('pro.invoices.statusUpdated'))
  await loadInvoice()
}

async function handleReminder() {
  await proStore.markInvoiceReminder(invoice.value!.id)
  message.success(t('pro.invoices.reminderSent'))
  await loadInvoice()
}

async function handleDownloadPdf() {
  const blob = await proStore.downloadInvoicePdf(invoice.value!.id)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${invoice.value!.invoice_number}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleSaveSettings() {
  await proStore.updateInvoiceSettings(settingsForm.value)
  showSettingsModal.value = false
  message.success(t('pro.invoiceSettings.settingsUpdated'))
}

async function loadInvoice() {
  const id = route.params.id as string
  invoice.value = await proStore.fetchInvoice(id)
  form.value = {
    client_id: invoice.value.client_id,
    issue_date: invoice.value.issue_date,
    due_date: invoice.value.due_date,
    discount_type: invoice.value.discount_type,
    discount_value: invoice.value.discount_value,
    notes: invoice.value.notes || '',
    items: invoice.value.items.map(i => ({
      product_id: i.product_id,
      description: i.description,
      quantity: i.quantity,
      unit_price: i.unit_price,
    })),
  }
}

onMounted(async () => {
  await Promise.all([proStore.fetchClients(), proStore.fetchProducts(), proStore.fetchInvoiceSettings()])
  // Init settings form
  if (proStore.invoiceSettings) {
    const s = proStore.invoiceSettings
    settingsForm.value = {
      invoice_prefix: s.invoice_prefix, quote_prefix: s.quote_prefix,
      payment_terms_days: s.payment_terms_days, late_penalty_rate: s.late_penalty_rate,
      bank_name: s.bank_name || '', bank_iban: s.bank_iban || '',
      bank_bic: s.bank_bic || '', default_notes: s.default_notes || '',
    }
  }
  if (!isNew.value) {
    await loadInvoice()
  } else {
    // Set default due_date from settings
    const days = proStore.invoiceSettings?.payment_terms_days || 30
    const due = new Date()
    due.setDate(due.getDate() + days)
    form.value.due_date = due.toISOString().slice(0, 10)
    form.value.notes = proStore.invoiceSettings?.default_notes || ''
    addItem()
  }
})
</script>
