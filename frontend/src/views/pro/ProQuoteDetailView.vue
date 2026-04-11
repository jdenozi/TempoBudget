<template>
  <n-space vertical :size="16">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <n-button text @click="$router.push({ name: 'pro-quotes' })">← {{ t('common.back') }}</n-button>
        <h2 style="margin: 0;">{{ isNew ? t('pro.quotes.addQuote') : `${t('pro.quotes.editQuote')} ${quote?.quote_number || ''}` }}</h2>
        <n-tag v-if="quote" :type="statusTagType(quote.status)" size="small">{{ t(`pro.quotes.${quote.status}`) }}</n-tag>
      </div>
      <n-space v-if="quote" :size="8">
        <n-button v-if="quote.status === 'draft'" type="info" @click="handleStatusChange('sent')">{{ t('pro.quotes.sent') }}</n-button>
        <n-button v-if="quote.status === 'sent'" type="success" @click="handleStatusChange('accepted')">{{ t('pro.quotes.accepted') }}</n-button>
        <n-button v-if="quote.status === 'sent'" type="error" quaternary @click="handleStatusChange('rejected')">{{ t('pro.quotes.rejected') }}</n-button>
        <n-button v-if="quote.status !== 'expired' && quote.status !== 'rejected'" quaternary @click="handleStatusChange('expired')">{{ t('pro.quotes.expired') }}</n-button>
        <n-button v-if="!quote.invoice_id && (quote.status === 'accepted' || quote.status === 'sent')" type="primary" @click="handleConvert">{{ t('pro.quotes.convertToInvoice') }}</n-button>
        <n-button type="info" @click="handleDownloadPdf">PDF</n-button>
      </n-space>
    </div>

    <n-alert v-if="quote?.invoice_id" type="info" :title="t('pro.quotes.linkedInvoice')" style="margin-bottom: 0;">
      <n-button text type="primary" @click="$router.push({ name: 'pro-invoice-detail', params: { id: quote.invoice_id } })">
        {{ t('pro.quotes.linkedInvoice') }} →
      </n-button>
    </n-alert>

    <!-- Form -->
    <n-card>
      <n-space vertical :size="16">
        <n-grid :cols="isMobile ? 1 : 3" :x-gap="16" :y-gap="12">
          <n-gi>
            <n-form-item :label="t('pro.quotes.client')">
              <n-select v-model:value="form.client_id" :options="clientOptions" filterable :disabled="!isDraft" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item :label="t('pro.quotes.issueDate')">
              <n-date-picker v-model:value="issueDateTs" type="date" :disabled="!isDraft" style="width: 100%;" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item :label="t('pro.quotes.validityDate')">
              <n-date-picker v-model:value="validityDateTs" type="date" :disabled="!isDraft" style="width: 100%;" />
            </n-form-item>
          </n-gi>
        </n-grid>

        <!-- Items -->
        <h3 style="margin: 0;">{{ t('pro.quotes.items') }}</h3>
        <n-space vertical :size="8">
          <n-card v-for="(item, idx) in form.items" :key="idx" size="small">
            <n-grid :cols="isMobile ? 1 : 12" :x-gap="8" :y-gap="8" style="align-items: end;">
              <n-gi :span="isMobile ? 1 : 4">
                <n-form-item :label="t('pro.quotes.description')" :show-feedback="false">
                  <n-input v-model:value="item.description" :disabled="!isDraft" />
                </n-form-item>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 2">
                <n-form-item label="Produit" :show-feedback="false">
                  <n-select
                    v-model:value="item.product_id"
                    :options="productOptions"
                    clearable filterable :disabled="!isDraft"
                    @update:value="(v: string) => onProductSelect(idx, v)"
                  />
                </n-form-item>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 2">
                <n-form-item :label="t('pro.quotes.quantity')" :show-feedback="false">
                  <n-input-number v-model:value="item.quantity" :min="0.01" :step="1" :disabled="!isDraft" style="width: 100%;" />
                </n-form-item>
              </n-gi>
              <n-gi :span="isMobile ? 1 : 2">
                <n-form-item :label="t('pro.quotes.unitPrice')" :show-feedback="false">
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
          <n-button v-if="isDraft" dashed block @click="addItem">{{ t('pro.quotes.addItem') }}</n-button>
        </n-space>

        <!-- Discount + Notes -->
        <n-grid :cols="isMobile ? 1 : 2" :x-gap="16" :y-gap="12">
          <n-gi>
            <n-form-item :label="t('pro.quotes.discount')">
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
            <n-form-item :label="t('pro.quotes.notes')">
              <n-input v-model:value="form.notes" type="textarea" :rows="2" :disabled="!isDraft" />
            </n-form-item>
          </n-gi>
        </n-grid>

        <!-- Totals -->
        <div style="text-align: right; font-size: 16px;">
          <div>{{ t('pro.quotes.subtotal') }}: <strong>{{ computedSubtotal.toFixed(2) }} €</strong></div>
          <div v-if="form.discount_type" style="color: #f0a020;">
            {{ t('pro.quotes.discount') }}: -{{ computedDiscount.toFixed(2) }} €
          </div>
          <div style="font-size: 20px; margin-top: 4px;">
            {{ t('pro.quotes.total') }}: <strong>{{ computedTotal.toFixed(2) }} €</strong>
          </div>
        </div>

        <n-button v-if="isDraft" type="primary" block @click="handleSave" :loading="saving">
          {{ t('common.save') }}
        </n-button>
      </n-space>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NSpace, NButton, NCard, NGrid, NGi, NFormItem, NInput, NInputNumber,
  NSelect, NDatePicker, NTag, NAlert, useMessage,
} from 'naive-ui'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProQuote } from '@/services/api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const isNew = computed(() => route.name === 'pro-quote-new')
const quote = ref<ProQuote | null>(null)
const saving = ref(false)

const isDraft = computed(() => isNew.value || quote.value?.status === 'draft')

interface ItemForm {
  product_id: string | null
  description: string
  quantity: number
  unit_price: number
}

const form = ref({
  client_id: null as string | null,
  issue_date: new Date().toISOString().slice(0, 10),
  validity_date: '',
  discount_type: null as string | null,
  discount_value: 0,
  notes: '',
  items: [] as ItemForm[],
})

const issueDateTs = computed({
  get: () => form.value.issue_date ? new Date(form.value.issue_date).getTime() : null,
  set: (v) => { if (v) form.value.issue_date = new Date(v).toISOString().slice(0, 10) },
})
const validityDateTs = computed({
  get: () => form.value.validity_date ? new Date(form.value.validity_date).getTime() : null,
  set: (v) => { if (v) form.value.validity_date = new Date(v).toISOString().slice(0, 10) },
})

const clientOptions = computed(() => proStore.proClients.map(c => ({ label: c.name, value: c.id })))
const productOptions = computed(() => proStore.proProducts.map(p => ({ label: `${p.name} (${p.default_price.toFixed(2)} €)`, value: p.id })))

function statusTagType(status: string) {
  const map: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
    draft: 'default', sent: 'info', accepted: 'success', rejected: 'error', expired: 'warning',
  }
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
      validity_date: form.value.validity_date,
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
      const q = await proStore.createQuote(data)
      message.success(t('pro.quotes.quoteCreated'))
      router.replace({ name: 'pro-quote-detail', params: { id: q.id } })
    } else {
      await proStore.updateQuote(quote.value!.id, data)
      message.success(t('pro.quotes.quoteUpdated'))
      await loadQuote()
    }
  } finally {
    saving.value = false
  }
}

async function handleStatusChange(status: string) {
  await proStore.updateQuoteStatus(quote.value!.id, { status })
  message.success(t('pro.quotes.statusUpdated'))
  await loadQuote()
}

async function handleConvert() {
  const inv = await proStore.convertQuoteToInvoice(quote.value!.id)
  message.success(t('pro.quotes.converted'))
  router.push({ name: 'pro-invoice-detail', params: { id: inv.id } })
}

async function handleDownloadPdf() {
  const blob = await proStore.downloadQuotePdf(quote.value!.id)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${quote.value!.quote_number}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

async function loadQuote() {
  const id = route.params.id as string
  quote.value = await proStore.fetchQuote(id)
  form.value = {
    client_id: quote.value.client_id,
    issue_date: quote.value.issue_date,
    validity_date: quote.value.validity_date,
    discount_type: quote.value.discount_type,
    discount_value: quote.value.discount_value,
    notes: quote.value.notes || '',
    items: quote.value.items.map(i => ({
      product_id: i.product_id,
      description: i.description,
      quantity: i.quantity,
      unit_price: i.unit_price,
    })),
  }
}

onMounted(async () => {
  await Promise.all([proStore.fetchClients(), proStore.fetchProducts()])
  if (!isNew.value) {
    await loadQuote()
  } else {
    // Default validity: 30 days from now
    const validity = new Date()
    validity.setDate(validity.getDate() + 30)
    form.value.validity_date = validity.toISOString().slice(0, 10)
    addItem()
  }
})
</script>
