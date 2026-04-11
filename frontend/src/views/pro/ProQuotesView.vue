<template>
  <n-space vertical :size="16">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <h2 style="margin: 0;">{{ t('pro.quotes.title') }}</h2>
      <n-button type="primary" @click="$router.push({ name: 'pro-quote-new' })">
        {{ t('pro.quotes.addQuote') }}
      </n-button>
    </div>

    <!-- Filters -->
    <n-space :vertical="isMobile" :size="12">
      <n-select
        v-model:value="filterStatus"
        :options="statusOptions"
        clearable
        :placeholder="t('common.status')"
        :style="{ width: isMobile ? '100%' : '160px' }"
      />
      <n-select
        v-model:value="filterClient"
        :options="clientOptions"
        clearable
        filterable
        :placeholder="t('pro.quotes.client')"
        :style="{ width: isMobile ? '100%' : '200px' }"
      />
      <n-date-picker v-model:value="filterDateRange" type="daterange" clearable :style="{ width: isMobile ? '100%' : '280px' }" />
    </n-space>

    <!-- Stats -->
    <n-grid :cols="isMobile ? 1 : 2" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-statistic :label="t('pro.quotes.totalQuoted')" :value="stats.totalQuoted" style="text-align: center;">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Devis acceptés" :value="stats.totalAccepted" style="text-align: center;">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
    </n-grid>

    <!-- Desktop Table -->
    <n-data-table
      v-if="!isMobile"
      :columns="columns"
      :data="proStore.proQuotes"
      :row-key="(row: ProQuote) => row.id"
      :loading="proStore.loading"
      :pagination="{ pageSize: 20 }"
    />

    <!-- Mobile Cards -->
    <n-space v-else vertical :size="8">
      <n-empty v-if="proStore.proQuotes.length === 0" :description="t('pro.quotes.noQuotes')" />
      <n-card v-for="q in proStore.proQuotes" :key="q.id" size="small" @click="$router.push({ name: 'pro-quote-detail', params: { id: q.id } })">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong>{{ q.quote_number }}</strong>
            <div style="font-size: 12px; color: #999;">{{ q.client_name }} · {{ q.issue_date }}</div>
          </div>
          <div style="text-align: right;">
            <div style="font-weight: bold;">{{ q.total.toFixed(2) }} €</div>
            <n-tag :type="statusTagType(q.status)" size="small">{{ t(`pro.quotes.${q.status}`) }}</n-tag>
          </div>
        </div>
        <div v-if="!q.invoice_id && (q.status === 'accepted' || q.status === 'sent')" style="margin-top: 8px;">
          <n-button size="small" type="primary" @click.stop="handleConvert(q.id)">{{ t('pro.quotes.convertToInvoice') }}</n-button>
        </div>
      </n-card>
    </n-space>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, h } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NSpace, NButton, NSelect, NDatePicker, NGrid, NGi, NStatistic,
  NDataTable, NCard, NEmpty, NTag, NPopconfirm, useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProQuote } from '@/services/api'

const { t } = useI18n()
const router = useRouter()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const filterStatus = ref<string | null>(null)
const filterClient = ref<string | null>(null)
const filterDateRange = ref<[number, number] | null>(null)

const statusOptions = computed(() => [
  { label: t('pro.quotes.draft'), value: 'draft' },
  { label: t('pro.quotes.sent'), value: 'sent' },
  { label: t('pro.quotes.accepted'), value: 'accepted' },
  { label: t('pro.quotes.rejected'), value: 'rejected' },
  { label: t('pro.quotes.expired'), value: 'expired' },
])

const clientOptions = computed(() => proStore.proClients.map(c => ({ label: c.name, value: c.id })))

function statusTagType(status: string) {
  const map: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
    draft: 'default', sent: 'info', accepted: 'success', rejected: 'error', expired: 'warning',
  }
  return map[status] || 'default'
}

const stats = computed(() => {
  const quotes = proStore.proQuotes
  const totalQuoted = quotes.filter(q => q.status !== 'rejected').reduce((s, q) => s + q.total, 0)
  const totalAccepted = quotes.filter(q => q.status === 'accepted').reduce((s, q) => s + q.total, 0)
  return {
    totalQuoted: totalQuoted.toFixed(2),
    totalAccepted: totalAccepted.toFixed(2),
  }
})

async function handleConvert(id: string) {
  const inv = await proStore.convertQuoteToInvoice(id)
  message.success(t('pro.quotes.converted'))
  router.push({ name: 'pro-invoice-detail', params: { id: inv.id } })
}

const columns = computed<DataTableColumns<ProQuote>>(() => [
  { title: t('pro.quotes.quoteNumber'), key: 'quote_number', width: 140 },
  { title: t('pro.quotes.client'), key: 'client_name' },
  { title: t('pro.quotes.issueDate'), key: 'issue_date', width: 120 },
  { title: t('pro.quotes.validityDate'), key: 'validity_date', width: 120 },
  {
    title: t('pro.quotes.total'), key: 'total', width: 120,
    render: (row) => h('span', { style: 'font-weight: bold' }, `${row.total.toFixed(2)} €`),
  },
  {
    title: t('pro.quotes.status'), key: 'status', width: 120,
    render: (row) => h(NTag, { type: statusTagType(row.status), size: 'small' }, () => t(`pro.quotes.${row.status}`)),
  },
  {
    title: t('common.actions'), key: 'actions', width: 280,
    render: (row) => h(NSpace, { size: 4 }, () => [
      h(NButton, { size: 'small', onClick: () => router.push({ name: 'pro-quote-detail', params: { id: row.id } }) }, () => t('common.edit')),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleDownloadPdf(row.id, row.quote_number) }, () => 'PDF'),
      ...(!row.invoice_id && (row.status === 'accepted' || row.status === 'sent') ? [
        h(NButton, { size: 'small', type: 'primary', onClick: () => handleConvert(row.id) }, () => t('pro.quotes.convertToInvoice')),
      ] : []),
      ...(row.status === 'draft' ? [
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('pro.quotes.deleteConfirm'),
        }),
      ] : []),
    ]),
  },
])

async function loadData() {
  const params: Record<string, string> = {}
  if (filterStatus.value) params.status = filterStatus.value
  if (filterClient.value) params.client_id = filterClient.value
  if (filterDateRange.value) {
    params.start_date = new Date(filterDateRange.value[0]).toISOString().slice(0, 10)
    params.end_date = new Date(filterDateRange.value[1]).toISOString().slice(0, 10)
  }
  await proStore.fetchQuotes(params)
}

async function handleDelete(id: string) {
  await proStore.deleteQuote(id)
  message.success(t('pro.quotes.quoteDeleted'))
}

async function handleDownloadPdf(id: string, number: string) {
  const blob = await proStore.downloadQuotePdf(id)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${number}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

watch([filterStatus, filterClient, filterDateRange], () => loadData())

onMounted(async () => {
  await Promise.all([loadData(), proStore.fetchClients()])
})
</script>
