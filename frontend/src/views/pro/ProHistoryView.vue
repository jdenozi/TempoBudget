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
        </n-space>
        <div v-if="tx.items && tx.items.length > 0" style="font-size: 12px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">
          <span v-for="(item, idx) in tx.items" :key="item.id">
            {{ item.product_name }}<span v-if="item.quantity > 1"> x{{ item.quantity }}</span><span v-if="idx < tx.items.length - 1">, </span>
          </span>
        </div>
        <template #action>
          <n-space size="small">
            <n-button size="tiny" @click="openEditModal(tx)">{{ t('common.edit') }}</n-button>
            <n-popconfirm @positive-click="handleDelete(tx.id)">
              <template #trigger>
                <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
              </template>
              {{ t('transaction.deleteTransactionConfirm') }}
            </n-popconfirm>
          </n-space>
        </template>
      </n-card>
    </n-space>

    <!-- Create/Edit Transaction Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="editingTx ? t('transaction.editTransaction') : t('pro.transactions.addTransaction')" style="max-width: 600px;">
      <n-form :model="txForm">
        <n-form-item :label="t('transaction.type')">
          <n-radio-group v-model:value="txForm.transaction_type">
            <n-radio-button value="expense">{{ t('transaction.expense') }}</n-radio-button>
            <n-radio-button value="income">{{ t('transaction.income') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>

        <!-- Product/Service selector (only for creation) -->
        <n-form-item v-if="!editingTx" :label="t('pro.products.selectProducts')">
          <n-select
            v-model:value="selectedProductIds"
            :options="availableProductOptions"
            multiple
            filterable
            clearable
            :placeholder="t('pro.products.selectProducts')"
          />
        </n-form-item>

        <!-- Items list -->
        <div v-if="txForm.items.length > 0" style="margin-bottom: 16px;">
          <n-card v-for="(item, idx) in txForm.items" :key="idx" size="small" style="margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
              <strong style="flex: 1; min-width: 100px;">{{ getProductName(item.product_id) }}</strong>
              <n-input-number
                v-model:value="item.quantity"
                :min="1"
                size="small"
                style="width: 80px;"
                :placeholder="t('pro.products.quantity')"
              />
              <span>×</span>
              <n-input-number
                v-model:value="item.unit_price"
                :min="0"
                :precision="2"
                size="small"
                style="width: 110px;"
              >
                <template #suffix>€</template>
              </n-input-number>
              <span style="min-width: 80px; text-align: right; font-weight: bold;">
                = {{ ((item.quantity || 0) * (item.unit_price || 0)).toFixed(2) }} €
              </span>
              <n-button size="tiny" type="error" @click="removeItem(idx)">×</n-button>
            </div>
          </n-card>
          <div style="text-align: right; font-weight: bold; font-size: 16px; margin-top: 8px;">
            {{ t('pro.products.itemsTotal') }}: {{ itemsTotal.toFixed(2) }} €
          </div>
        </div>

        <n-form-item :label="t('transaction.transactionTitle')">
          <n-input v-model:value="txForm.title" :placeholder="autoTitle || ''" />
        </n-form-item>
        <n-form-item v-if="txForm.items.length === 0" :label="t('transaction.amount')">
          <n-input-number v-model:value="txForm.amount" :min="0.01" :precision="2" style="width: 100%;">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('category.title')">
          <n-select v-model:value="txForm.category_id" :options="filteredCategoryOptions" :placeholder="t('placeholders.selectCategory')" />
        </n-form-item>
        <n-form-item :label="t('pro.transactions.client')">
          <n-select v-model:value="txForm.client_id" :options="clientOptions" clearable />
        </n-form-item>
        <n-form-item :label="t('transaction.date')">
          <n-date-picker v-model:value="txForm.date" type="date" style="width: 100%;" />
        </n-form-item>
        <n-form-item :label="t('pro.transactions.paymentMethod')">
          <n-select v-model:value="txForm.payment_method" :options="paymentMethodOptions" />
        </n-form-item>
        <!-- Discount Section -->
        <n-divider v-if="!editingTx" style="margin: 8px 0;">{{ t('pro.discount.discount') }}</n-divider>
        <n-form-item v-if="!editingTx" :label="t('pro.discount.discount')">
          <n-radio-group v-model:value="discountMode">
            <n-radio-button value="none">{{ t('pro.discount.noDiscount') }}</n-radio-button>
            <n-radio-button value="manual">{{ t('pro.discount.manualDiscount') }}</n-radio-button>
            <n-radio-button value="coupon">{{ t('pro.discount.useCoupon') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>

        <!-- Manual Discount -->
        <template v-if="!editingTx && discountMode === 'manual'">
          <n-form-item :label="t('pro.coupons.discountType')">
            <n-radio-group v-model:value="txForm.discount_type">
              <n-radio-button value="percentage">{{ t('pro.coupons.percentage') }}</n-radio-button>
              <n-radio-button value="fixed">{{ t('pro.coupons.fixed') }}</n-radio-button>
            </n-radio-group>
          </n-form-item>
          <n-form-item :label="t('pro.coupons.discountValue')">
            <n-input-number v-model:value="txForm.discount_value" :min="0.01" :precision="2" style="width: 100%;">
              <template #suffix>{{ txForm.discount_type === 'percentage' ? '%' : '€' }}</template>
            </n-input-number>
          </n-form-item>
        </template>

        <!-- Coupon Select -->
        <n-form-item v-if="!editingTx && discountMode === 'coupon'" :label="t('pro.discount.selectCoupon')">
          <n-select v-model:value="txForm.coupon_id" :options="activeCouponOptions" clearable :placeholder="t('pro.discount.selectCoupon')" />
        </n-form-item>

        <!-- Gift Card Payment -->
        <n-divider v-if="!editingTx" style="margin: 8px 0;">{{ t('pro.discount.giftCardPayment') }}</n-divider>
        <template v-if="!editingTx">
          <n-form-item :label="t('pro.discount.selectGiftCard')">
            <n-select v-model:value="txForm.gift_card_id" :options="activeGiftCardOptions" clearable :placeholder="t('pro.discount.selectGiftCard')" />
          </n-form-item>
          <n-form-item v-if="txForm.gift_card_id" :label="t('pro.discount.giftCardAmount')">
            <n-input-number v-model:value="txForm.gift_card_amount" :min="0.01" :precision="2" :max="selectedGiftCardBalance" style="width: 100%;">
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>
        </template>

        <!-- Summary -->
        <n-card v-if="!editingTx && (discountMode !== 'none' || txForm.gift_card_id)" size="small" style="margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>{{ t('pro.discount.subtotal') }}</span>
            <strong>{{ computedSubtotal.toFixed(2) }} €</strong>
          </div>
          <div v-if="computedDiscount > 0" style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #18a058;">
            <span>{{ t('pro.discount.discount') }}</span>
            <span>-{{ computedDiscount.toFixed(2) }} €</span>
          </div>
          <div v-if="txForm.gift_card_id && (txForm.gift_card_amount || 0) > 0" style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #2080f0;">
            <span>{{ t('pro.discount.giftCardPayment') }}</span>
            <span>-{{ (txForm.gift_card_amount || 0).toFixed(2) }} €</span>
          </div>
          <n-divider style="margin: 4px 0;" />
          <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 16px;">
            <span>{{ t('pro.discount.totalToPay') }}</span>
            <span>{{ computedTotal.toFixed(2) }} €</span>
          </div>
        </n-card>

        <n-form-item :label="t('transaction.comment')">
          <n-input v-model:value="txForm.comment" type="textarea" :rows="2" />
        </n-form-item>
        <n-button type="primary" block @click="handleSubmit">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, h, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  NSpace, NCard, NGrid, NGi, NStatistic, NButton, NDataTable,
  NDatePicker, NSelect, NTag, NEmpty, NModal, NForm, NFormItem,
  NInput, NInputNumber, NRadioGroup, NRadioButton, NPopconfirm,
  NDivider, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProTransaction } from '@/services/api'

const { t } = useI18n()
const route = useRoute()
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
const selectedProductIds = ref<string[]>([])
const discountMode = ref<'none' | 'manual' | 'coupon'>('none')

interface ItemForm {
  product_id: string
  quantity: number
  unit_price: number
}

const txForm = ref({
  transaction_type: 'expense' as 'income' | 'expense',
  title: '',
  amount: null as number | null,
  category_id: null as string | null,
  client_id: null as string | null,
  date: Date.now(),
  payment_method: 'cash',
  comment: '',
  items: [] as ItemForm[],
  discount_type: 'percentage' as 'percentage' | 'fixed',
  discount_value: null as number | null,
  coupon_id: null as string | null,
  gift_card_id: null as string | null,
  gift_card_amount: null as number | null,
})

const clientOptions = computed(() =>
  proStore.proClients.map(c => ({ label: c.name, value: c.id }))
)

const categoryOptions = computed(() =>
  proStore.proCategories.map(c => ({ label: `${c.name} (${c.type})`, value: c.id }))
)

const filteredCategoryOptions = computed(() =>
  proStore.proCategories
    .filter(c => c.type === txForm.value.transaction_type)
    .map(c => ({ label: c.name, value: c.id }))
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

const availableProductOptions = computed(() =>
  proStore.proProducts.map(p => ({ label: `${p.name} — ${p.default_price.toFixed(2)} €`, value: p.id }))
)

const activeCouponOptions = computed(() =>
  proStore.proCoupons
    .filter(c => c.is_active && (c.max_uses === 0 || c.used_count < c.max_uses))
    .map(c => ({
      label: `${c.code} — ${c.name} (${c.discount_type === 'percentage' ? `${c.discount_value}%` : `${c.discount_value.toFixed(2)} €`})`,
      value: c.id,
    }))
)

const activeGiftCardOptions = computed(() =>
  proStore.proGiftCards
    .filter(gc => gc.is_active && gc.remaining_balance > 0)
    .map(gc => ({
      label: `${gc.code} — ${t('pro.discount.balance')}: ${gc.remaining_balance.toFixed(2)} €`,
      value: gc.id,
    }))
)

const selectedGiftCardBalance = computed(() => {
  if (!txForm.value.gift_card_id) return 0
  const gc = proStore.proGiftCards.find(g => g.id === txForm.value.gift_card_id)
  return gc ? gc.remaining_balance : 0
})

const computedSubtotal = computed(() => {
  if (txForm.value.items.length > 0) return itemsTotal.value
  return txForm.value.amount || 0
})

const computedDiscount = computed(() => {
  const sub = computedSubtotal.value
  if (discountMode.value === 'coupon' && txForm.value.coupon_id) {
    const coupon = proStore.proCoupons.find(c => c.id === txForm.value.coupon_id)
    if (!coupon) return 0
    return coupon.discount_type === 'percentage'
      ? sub * coupon.discount_value / 100
      : coupon.discount_value
  }
  if (discountMode.value === 'manual' && txForm.value.discount_value) {
    return txForm.value.discount_type === 'percentage'
      ? sub * txForm.value.discount_value / 100
      : txForm.value.discount_value
  }
  return 0
})

const computedTotal = computed(() => {
  const afterDiscount = Math.max(computedSubtotal.value - computedDiscount.value, 0)
  const gcPayment = txForm.value.gift_card_amount || 0
  return Math.max(afterDiscount - gcPayment, 0)
})

// Watch selectedProductIds to sync items
watch(selectedProductIds, (newIds, oldIds) => {
  const currentIds = txForm.value.items.map(i => i.product_id)
  // Add new items
  for (const id of newIds) {
    if (!currentIds.includes(id)) {
      const product = proStore.proProducts.find(p => p.id === id)
      if (product) {
        txForm.value.items.push({
          product_id: id,
          quantity: 1,
          unit_price: product.default_price,
        })
      }
    }
  }
  // Remove deselected items
  txForm.value.items = txForm.value.items.filter(i => newIds.includes(i.product_id))
})

const itemsTotal = computed(() =>
  txForm.value.items.reduce((sum, i) => sum + (i.quantity || 0) * (i.unit_price || 0), 0)
)

const autoTitle = computed(() => {
  if (txForm.value.items.length === 0) return ''
  return txForm.value.items.map(i => {
    const name = getProductName(i.product_id)
    return i.quantity > 1 ? `${name} x${i.quantity}` : name
  }).join(' + ')
})

function getProductName(productId: string) {
  return proStore.proProducts.find(p => p.id === productId)?.name || '?'
}

function removeItem(idx: number) {
  const removed = txForm.value.items[idx]
  txForm.value.items.splice(idx, 1)
  selectedProductIds.value = selectedProductIds.value.filter(id => id !== removed.product_id)
}

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
  { title: () => t('transaction.transactionTitle'), key: 'title' },
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

function formatDate(ts: number) {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function openCreateModal() {
  editingTx.value = null
  selectedProductIds.value = []
  discountMode.value = 'none'
  txForm.value = {
    transaction_type: 'expense',
    title: '',
    amount: null,
    category_id: null,
    client_id: null,
    date: Date.now(),
    payment_method: 'cash',
    comment: '',
    items: [],
    discount_type: 'percentage',
    discount_value: null,
    coupon_id: null,
    gift_card_id: null,
    gift_card_amount: null,
  }
  showModal.value = true
}

function openEditModal(tx: ProTransaction) {
  editingTx.value = tx
  selectedProductIds.value = []
  discountMode.value = 'none'
  txForm.value = {
    transaction_type: tx.transaction_type,
    title: tx.title,
    amount: tx.amount,
    category_id: tx.category_id,
    client_id: tx.client_id,
    date: new Date(tx.date).getTime(),
    payment_method: tx.payment_method || 'cash',
    comment: tx.comment || '',
    items: [],
    discount_type: 'percentage',
    discount_value: null,
    coupon_id: null,
    gift_card_id: null,
    gift_card_amount: null,
  }
  showModal.value = true
}

async function handleSubmit() {
  const hasItems = txForm.value.items.length > 0
  const title = txForm.value.title || (hasItems ? autoTitle.value : '')
  const amount = hasItems ? itemsTotal.value : txForm.value.amount

  if (!title && !hasItems) return
  if (!amount && !hasItems) return
  if (!txForm.value.category_id) return

  if (editingTx.value) {
    await proStore.updateTransaction(editingTx.value.id, {
      title,
      amount: amount || undefined,
      transaction_type: txForm.value.transaction_type,
      category_id: txForm.value.category_id,
      client_id: txForm.value.client_id || undefined,
      date: formatDate(txForm.value.date),
      payment_method: txForm.value.payment_method,
      comment: txForm.value.comment || undefined,
    })
    message.success(t('transaction.transactionUpdated'))
  } else {
    const data: Record<string, unknown> = {
      title: txForm.value.title || undefined,
      amount: hasItems ? undefined : amount,
      transaction_type: txForm.value.transaction_type,
      category_id: txForm.value.category_id,
      client_id: txForm.value.client_id || undefined,
      date: formatDate(txForm.value.date),
      payment_method: txForm.value.payment_method,
      comment: txForm.value.comment || undefined,
    }
    if (hasItems) {
      data.items = txForm.value.items.map(i => ({
        product_id: i.product_id,
        quantity: i.quantity,
        unit_price: i.unit_price,
      }))
    }
    // Discount
    if (discountMode.value === 'coupon' && txForm.value.coupon_id) {
      data.coupon_id = txForm.value.coupon_id
    } else if (discountMode.value === 'manual' && txForm.value.discount_value) {
      data.discount_type = txForm.value.discount_type
      data.discount_value = txForm.value.discount_value
    }
    // Gift card
    if (txForm.value.gift_card_id && txForm.value.gift_card_amount) {
      data.gift_card_id = txForm.value.gift_card_id
      data.gift_card_amount = txForm.value.gift_card_amount
    }
    await proStore.createTransaction(data as Parameters<typeof proStore.createTransaction>[0])
    message.success(t('transaction.transactionAdded'))
  }

  showModal.value = false
  await proStore.fetchDashboard()
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
    proStore.fetchCoupons(),
    proStore.fetchGiftCards(),
  ])

  // Pre-fill client filter from query param
  if (route.query.client_id && typeof route.query.client_id === 'string') {
    filterClientId.value = route.query.client_id
  }
})
</script>
