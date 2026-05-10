<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('nav.proHistory') }}</h1>
      <n-button type="primary" @click="openCreateModal">{{ t('pro.transactions.addTransaction') }}</n-button>
    </div>

    <!-- Filters -->
    <n-space :vertical="isMobile" :size="isMobile ? 12 : 16">
      <n-date-picker v-model:value="startDate" type="date" :style="{ width: isMobile ? '100%' : '160px' }" :placeholder="t('common.startDate')" clearable />
      <n-date-picker v-model:value="endDate" type="date" :style="{ width: isMobile ? '100%' : '160px' }" :placeholder="t('common.endDate')" clearable />
      <n-select v-model:value="filterClientId" :options="clientOptions" :placeholder="t('pro.transactions.filterByClient')" :style="{ width: isMobile ? '100%' : '200px' }" clearable />
      <n-select v-model:value="filterCategoryId" :options="categoryOptions" :placeholder="t('history.filterByCategory')" :style="{ width: isMobile ? '100%' : '200px' }" clearable />
      <n-select v-model:value="filterPaymentMethod" :options="paymentMethodOptions" :placeholder="t('pro.transactions.filterByPaymentMethod')" :style="{ width: isMobile ? '100%' : '200px' }" clearable />
      <n-select v-model:value="filterProductId" :options="productOptions" :placeholder="t('pro.products.filterByProduct')" :style="{ width: isMobile ? '100%' : '200px' }" clearable />
    </n-space>

    <!-- Summary Stats -->
    <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-card size="small">
          <n-statistic :label="t('budget.income')" :value="totalIncome.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic :label="t('budget.expenses')" :value="totalExpenses.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic :label="t('history.balance')" :value="balance.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic :label="t('history.totalTransactions')" :value="filteredTransactions.length" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Transaction List -->
    <n-empty v-if="filteredTransactions.length === 0" :description="t('pro.transactions.noTransactions')" />

    <!-- Desktop Table -->
    <n-data-table
      v-if="!isMobile && filteredTransactions.length > 0"
      :columns="columns"
      :data="filteredTransactions"
      :row-key="(row: ProTransaction) => row.id"
      :pagination="{ pageSize: 20 }"
    />

    <!-- Mobile Cards -->
    <n-space v-if="isMobile && filteredTransactions.length > 0" vertical>
      <n-card v-for="tx in filteredTransactions" :key="tx.id" size="small">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>{{ tx.title }}</span>
            <span :style="{ color: tx.transaction_type === 'income' ? '#18a058' : '#d03050', fontWeight: 'bold' }">
              {{ tx.transaction_type === 'income' ? '+' : '-' }}{{ tx.amount.toFixed(2) }} €
            </span>
          </div>
        </template>
        <n-space size="small" style="margin-bottom: 8px;">
          <n-tag size="tiny" :type="tx.transaction_type === 'income' ? 'success' : 'error'">{{ tx.category_name }}</n-tag>
          <span style="font-size: 12px; color: rgba(255,255,255,0.5);">{{ tx.date }}</span>
          <n-tag v-if="tx.client_name" size="tiny">{{ tx.client_name }}</n-tag>
          <n-tag v-if="tx.payment_method" size="tiny" type="info">{{ t(`pro.transactions.${tx.payment_method}`) }}</n-tag>
          <n-tag v-if="tx.transaction_type === 'income'" size="tiny" :type="tx.is_declared ? 'success' : 'warning'">
            {{ tx.is_declared ? t('pro.declaration.declared') : t('pro.declaration.undeclared') }}
          </n-tag>
          <n-tag v-if="tx.invoice_id" size="tiny" type="info" style="cursor: pointer;" @click.stop="$router.push({ name: 'pro-invoice-detail', params: { id: tx.invoice_id } })">
            {{ t('pro.transactions.fromInvoice') }}
          </n-tag>
        </n-space>
        <div v-if="tx.items && tx.items.length > 0" style="font-size: 12px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">
          <span v-for="(item, idx) in tx.items" :key="item.id">
            {{ item.product_name }}<span v-if="item.quantity > 1"> x{{ item.quantity }}</span><span v-if="idx < tx.items.length - 1">, </span>
          </span>
        </div>
        <template #action>
          <n-space size="small">
            <template v-if="tx.invoice_id">
              <n-button size="tiny" type="info" @click="$router.push({ name: 'pro-invoice-detail', params: { id: tx.invoice_id } })">{{ t('pro.transactions.viewInvoice') }}</n-button>
            </template>
            <template v-else>
              <n-button size="tiny" @click="openEditModal(tx)">{{ t('common.edit') }}</n-button>
              <n-popconfirm @positive-click="handleDelete(tx.id)">
                <template #trigger>
                  <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
                </template>
                {{ t('transaction.deleteTransactionConfirm') }}
              </n-popconfirm>
            </template>
          </n-space>
        </template>
      </n-card>
    </n-space>

    <!-- Create/Edit Transaction Modal -->
    <n-modal
      v-model:show="showModal"
      preset="card"
      :title="editingTx ? t('transaction.editTransaction') : t('pro.transactions.addTransaction')"
      style="max-width: 640px;"
    >
      <ProTransactionForm :editing-tx="editingTx" @success="handleFormSuccess" />
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, h, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NSpace, NCard, NGrid, NGi, NStatistic, NButton, NDataTable,
  NDatePicker, NSelect, NTag, NEmpty, NModal, NPopconfirm, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProTransaction } from '@/services/api'
import ProTransactionForm from '@/components/pro/ProTransactionForm.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const startDate = ref<number | null>(null)
const endDate = ref<number | null>(null)
const filterClientId = ref<string | null>(null)
const filterCategoryId = ref<string | null>(null)
const filterPaymentMethod = ref<string | null>(null)
const filterProductId = ref<string | null>(null)
const showModal = ref(false)
const editingTx = ref<ProTransaction | null>(null)

const clientOptions = computed(() =>
  proStore.proClients.map(c => ({ label: c.name, value: c.id }))
)

const categoryOptions = computed(() =>
  proStore.proCategories.map(c => ({ label: `${c.name} (${c.type})`, value: c.id }))
)

const paymentMethodOptions = computed(() => [
  { label: t('pro.transactions.cash'), value: 'cash' },
  { label: t('pro.transactions.bankTransfer'), value: 'bankTransfer' },
  { label: t('pro.transactions.check'), value: 'check' },
  { label: t('pro.transactions.card'), value: 'card' },
  { label: t('pro.transactions.paypal'), value: 'paypal' },
  { label: t('pro.transactions.other'), value: 'other' },
])

const productOptions = computed(() =>
  proStore.proProducts.map(p => ({ label: `${p.name} (${p.default_price.toFixed(2)} €)`, value: p.id }))
)

// Refetch when product filter changes (backend filter)
watch(filterProductId, async () => {
  const params: Record<string, string> = {}
  if (filterProductId.value) params.product_id = filterProductId.value
  await proStore.fetchTransactions(params)
})

const filteredTransactions = computed(() => {
  let txs = proStore.proTransactions
  if (startDate.value != null) {
    const start = new Date(startDate.value).toISOString().split('T')[0]!
    txs = txs.filter(tx => tx.date >= start)
  }
  if (endDate.value != null) {
    const end = new Date(endDate.value).toISOString().split('T')[0]!
    txs = txs.filter(tx => tx.date <= end)
  }
  if (filterClientId.value) {
    txs = txs.filter(tx => tx.client_id === filterClientId.value)
  }
  if (filterCategoryId.value) {
    txs = txs.filter(tx => tx.category_id === filterCategoryId.value)
  }
  if (filterPaymentMethod.value) {
    txs = txs.filter(tx => tx.payment_method === filterPaymentMethod.value)
  }
  return txs
})

const totalIncome = computed(() =>
  filteredTransactions.value.filter(tx => tx.transaction_type === 'income').reduce((s, tx) => s + tx.amount, 0)
)
const totalExpenses = computed(() =>
  filteredTransactions.value.filter(tx => tx.transaction_type === 'expense').reduce((s, tx) => s + tx.amount, 0)
)
const balance = computed(() => totalIncome.value - totalExpenses.value)

const columns: DataTableColumns<ProTransaction> = [
  { title: () => t('transaction.date'), key: 'date', width: 110 },
  {
    title: () => t('transaction.transactionTitle'),
    key: 'title',
    render(row) {
      const children = [h('span', {}, row.title)]
      if (row.invoice_id) {
        children.push(
          h(NTag, {
            size: 'tiny',
            type: 'info',
            style: 'margin-left: 8px; cursor: pointer;',
            onClick: (e: Event) => {
              e.stopPropagation()
              router.push({ name: 'pro-invoice-detail', params: { id: row.invoice_id! } })
            },
          }, () => t('pro.transactions.fromInvoice'))
        )
      }
      return h('span', { style: 'display: flex; align-items: center;' }, children)
    },
  },
  { title: () => t('category.title'), key: 'category_name' },
  { title: () => t('pro.transactions.client'), key: 'client_name' },
  {
    title: () => t('transaction.amount'),
    key: 'amount',
    width: 120,
    render(row) {
      const color = row.transaction_type === 'income' ? '#18a058' : '#d03050'
      const prefix = row.transaction_type === 'income' ? '+' : '-'
      return h('span', { style: { color, fontWeight: 'bold' } }, `${prefix}${row.amount.toFixed(2)} €`)
    },
  },
  {
    title: () => t('pro.transactions.paymentMethod'),
    key: 'payment_method',
    width: 120,
    render(row) {
      if (!row.payment_method) return ''
      return h(NTag, { size: 'small', type: 'info' }, () => t(`pro.transactions.${row.payment_method}`))
    },
  },
  {
    title: () => t('common.actions'),
    key: 'actions',
    width: 150,
    render(row) {
      if (row.invoice_id) {
        return h(NButton, {
          size: 'small',
          type: 'info',
          onClick: () => router.push({ name: 'pro-invoice-detail', params: { id: row.invoice_id! } }),
        }, () => t('pro.transactions.viewInvoice'))
      }
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', onClick: () => openEditModal(row) }, () => t('common.edit')),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('transaction.deleteTransactionConfirm'),
        }),
      ])
    },
  },
]

function openCreateModal() {
  editingTx.value = null
  showModal.value = true
}

function openEditModal(tx: ProTransaction) {
  editingTx.value = tx
  showModal.value = true
}

function handleFormSuccess() {
  showModal.value = false
  editingTx.value = null
}

async function handleDelete(id: string) {
  await proStore.deleteTransaction(id)
  message.success(t('transaction.transactionDeleted'))
  await proStore.fetchDashboard()
}

onMounted(async () => {
  await Promise.all([
    proStore.fetchTransactions(),
    proStore.fetchClients(),
    proStore.fetchCategories(),
    proStore.fetchProducts(),
  ])

  // Pre-fill client filter from query param
  if (route.query.client_id && typeof route.query.client_id === 'string') {
    filterClientId.value = route.query.client_id
  }
})
</script>
