<template>
  <n-space vertical :size="16">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <h2 style="margin: 0;">{{ t('pro.invoices.title') }}</h2>
      <n-button type="primary" @click="$router.push({ name: 'pro-invoice-new' })">
        {{ t('pro.invoices.addInvoice') }}
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
        :placeholder="t('pro.invoices.client')"
        :style="{ width: isMobile ? '100%' : '200px' }"
      />
      <n-date-picker v-model:value="filterDateRange" type="daterange" clearable :style="{ width: isMobile ? '100%' : '280px' }" />
    </n-space>

    <!-- Stats -->
    <n-grid :cols="isMobile ? 2 : 3" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-statistic :label="t('pro.invoices.totalInvoiced')" :value="stats.totalInvoiced" style="text-align: center;">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic :label="t('pro.invoices.totalPaid')" :value="stats.totalPaid" style="text-align: center;">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic :label="t('pro.invoices.totalUnpaid')" :value="stats.totalUnpaid" style="text-align: center;">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
    </n-grid>

    <!-- Desktop Table -->
    <n-data-table
      v-if="!isMobile"
      :columns="columns"
      :data="proStore.proInvoices"
      :row-key="(row: ProInvoice) => row.id"
      :loading="proStore.loading"
      :pagination="{ pageSize: 20 }"
    />

    <!-- Mobile Cards -->
    <n-space v-else vertical :size="8">
      <n-empty v-if="proStore.proInvoices.length === 0" :description="t('pro.invoices.noInvoices')" />
      <n-card v-for="inv in proStore.proInvoices" :key="inv.id" size="small" @click="$router.push({ name: 'pro-invoice-detail', params: { id: inv.id } })">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong>{{ inv.invoice_number }}</strong>
            <div style="font-size: 12px; color: #999;">{{ inv.client_name }} · {{ inv.issue_date }}</div>
          </div>
          <div style="text-align: right;">
            <div style="font-weight: bold;">{{ inv.total.toFixed(2) }} €</div>
            <n-tag :type="statusTagType(inv.status)" size="small">{{ t(`pro.invoices.${inv.status}`) }}</n-tag>
          </div>
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
import type { ProInvoice } from '@/services/api'

const { t } = useI18n()
const router = useRouter()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const filterStatus = ref<string | null>(null)
const filterClient = ref<string | null>(null)
const filterDateRange = ref<[number, number] | null>(null)

const statusOptions = computed(() => [
  { label: t('pro.invoices.draft'), value: 'draft' },
  { label: t('pro.invoices.sent'), value: 'sent' },
  { label: t('pro.invoices.paid'), value: 'paid' },
  { label: t('pro.invoices.cancelled'), value: 'cancelled' },
])

const clientOptions = computed(() =>
  proStore.proClients.map(c => ({ label: c.name, value: c.id }))
)

function statusTagType(status: string) {
  const map: Record<string, 'default' | 'info' | 'success' | 'error'> = {
    draft: 'default', sent: 'info', paid: 'success', cancelled: 'error',
  }
  return map[status] || 'default'
}

const stats = computed(() => {
  const invoices = proStore.proInvoices
  const totalInvoiced = invoices.filter(i => i.status !== 'cancelled').reduce((s, i) => s + i.total, 0)
  const totalPaid = invoices.filter(i => i.status === 'paid').reduce((s, i) => s + i.total, 0)
  return {
    totalInvoiced: totalInvoiced.toFixed(2),
    totalPaid: totalPaid.toFixed(2),
    totalUnpaid: (totalInvoiced - totalPaid).toFixed(2),
  }
})

const columns = computed<DataTableColumns<ProInvoice>>(() => [
  { title: t('pro.invoices.invoiceNumber'), key: 'invoice_number', width: 140 },
  { title: t('pro.invoices.client'), key: 'client_name' },
  { title: t('pro.invoices.issueDate'), key: 'issue_date', width: 120 },
  { title: t('pro.invoices.dueDate'), key: 'due_date', width: 120 },
  {
    title: t('pro.invoices.totalHT'), key: 'subtotal', width: 100,
    render: (row) => h('span', {}, `${row.subtotal.toFixed(2)} €`),
  },
  ...(proStore.proProfile?.is_subject_to_vat ? [{
    title: t('pro.invoices.tva'), key: 'tva_amount', width: 100,
    render: (row: ProInvoice) => h('span', {}, `${row.tva_amount.toFixed(2)} €`),
  }] : []),
  {
    title: proStore.proProfile?.is_subject_to_vat ? t('pro.invoices.totalTTC') : t('pro.invoices.total'),
    key: 'total', width: 110,
    render: (row) => h('span', { style: 'font-weight: bold' }, `${row.total.toFixed(2)} €`),
  },
  {
    title: t('pro.invoices.status'), key: 'status', width: 120,
    render: (row) => h(NTag, { type: statusTagType(row.status), size: 'small' }, () => t(`pro.invoices.${row.status}`)),
  },
  {
    title: t('common.actions'), key: 'actions', width: 200,
    render: (row) => h(NSpace, { size: 4 }, () => [
      h(NButton, { size: 'small', onClick: () => router.push({ name: 'pro-invoice-detail', params: { id: row.id } }) }, () => t('common.edit')),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleDownloadPdf(row.id, row.invoice_number) }, () => 'PDF'),
      ...(row.status === 'draft' ? [
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('pro.invoices.deleteConfirm'),
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
  await proStore.fetchInvoices(params)
}

async function handleDelete(id: string) {
  await proStore.deleteInvoice(id)
  message.success(t('pro.invoices.invoiceDeleted'))
}

async function handleDownloadPdf(id: string, number: string) {
  try {
    const blob = await proStore.downloadInvoicePdf(id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${number}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    message.error(t('pro.invoices.pdfError'))
    console.error('PDF download error:', e)
  }
}

watch([filterStatus, filterClient, filterDateRange], () => loadData())

onMounted(async () => {
  await Promise.all([loadData(), proStore.fetchClients(), proStore.fetchProfile()])
})
</script>
