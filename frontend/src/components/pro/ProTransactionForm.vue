<template>
  <n-form ref="formRef" :model="txForm" :rules="formRules">
    <n-form-item :label="t('transaction.type')" path="transaction_type">
      <n-radio-group v-model:value="txForm.transaction_type">
        <n-radio-button value="expense">{{ t('transaction.expense') }}</n-radio-button>
        <n-radio-button value="income">{{ t('transaction.income') }}</n-radio-button>
      </n-radio-group>
    </n-form-item>

    <!-- Product/Service selector (only income, only creation) -->
    <n-form-item v-if="!editingTx && !isExpense" :label="t('pro.products.selectProducts')">
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
    <div v-if="!isExpense && txForm.items.length > 0" style="margin-bottom: 16px;">
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

    <n-form-item :label="t('transaction.transactionTitle')" path="title">
      <n-input v-model:value="txForm.title" :placeholder="autoTitle || ''" />
    </n-form-item>

    <n-form-item v-if="isExpense || txForm.items.length === 0" :label="t('transaction.amount')" path="amount">
      <n-input-number v-model:value="txForm.amount" :min="0.01" :precision="2" style="width: 100%;">
        <template #suffix>€</template>
      </n-input-number>
    </n-form-item>

    <n-form-item :label="t('category.title')" path="category_id">
      <n-select
        v-model:value="txForm.category_id"
        :options="filteredCategoryOptions"
        :placeholder="t('placeholders.selectCategory')"
      />
    </n-form-item>

    <n-form-item :label="isExpense ? t('pro.transactions.supplier') : t('pro.transactions.client')" path="client_id">
      <n-select v-model:value="txForm.client_id" :options="clientOptions" clearable />
    </n-form-item>

    <n-form-item :label="t('transaction.date')" path="date">
      <n-date-picker v-model:value="txForm.date" type="date" style="width: 100%;" />
    </n-form-item>

    <n-form-item :label="t('pro.transactions.paymentMethod')" path="payment_method">
      <n-select v-model:value="txForm.payment_method" :options="paymentMethodOptions" />
    </n-form-item>

    <!-- Discount (income only, creation only) -->
    <template v-if="!editingTx && !isExpense">
      <n-divider style="margin: 8px 0;">{{ t('pro.discount.discount') }}</n-divider>
      <n-form-item :label="t('pro.discount.discount')">
        <n-radio-group v-model:value="discountMode">
          <n-radio-button value="none">{{ t('pro.discount.noDiscount') }}</n-radio-button>
          <n-radio-button value="manual">{{ t('pro.discount.manualDiscount') }}</n-radio-button>
          <n-radio-button value="coupon">{{ t('pro.discount.useCoupon') }}</n-radio-button>
        </n-radio-group>
      </n-form-item>

      <template v-if="discountMode === 'manual'">
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

      <n-form-item v-if="discountMode === 'coupon'" :label="t('pro.discount.selectCoupon')">
        <n-select
          v-model:value="txForm.coupon_id"
          :options="activeCouponOptions"
          clearable
          :placeholder="t('pro.discount.selectCoupon')"
        />
      </n-form-item>
    </template>

    <!-- Gift card payment (income only, creation only) -->
    <template v-if="!editingTx && !isExpense">
      <n-divider style="margin: 8px 0;">{{ t('pro.discount.giftCardPayment') }}</n-divider>
      <n-form-item :label="t('pro.discount.selectGiftCard')">
        <n-select
          v-model:value="txForm.gift_card_id"
          :options="activeGiftCardOptions"
          clearable
          :placeholder="t('pro.discount.selectGiftCard')"
        />
      </n-form-item>
      <n-form-item v-if="txForm.gift_card_id" :label="t('pro.discount.giftCardAmount')">
        <n-input-number
          v-model:value="txForm.gift_card_amount"
          :min="0.01"
          :precision="2"
          :max="selectedGiftCardBalance"
          style="width: 100%;"
        >
          <template #suffix>€</template>
        </n-input-number>
      </n-form-item>
    </template>

    <!-- Summary (income only) -->
    <n-card
      v-if="!editingTx && !isExpense && (discountMode !== 'none' || txForm.gift_card_id)"
      size="small"
      style="margin-bottom: 16px;"
    >
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

    <!-- Project link (income only) -->
    <n-form-item v-if="!isExpense && projectCategoryOptions.length > 0" :label="t('project.linkToProject')">
      <n-select
        v-model:value="txForm.project_category_id"
        :options="projectCategoryOptions"
        clearable
        :placeholder="t('project.linkToProject')"
      />
    </n-form-item>

    <!-- Accounted toggle (income only) -->
    <n-form-item v-if="!isExpense" :label="t('pro.declaration.declared')">
      <n-switch v-model:value="txForm.is_declared">
        <template #checked>{{ t('pro.declaration.declared') }}</template>
        <template #unchecked>{{ t('pro.declaration.undeclared') }}</template>
      </n-switch>
    </n-form-item>

    <!-- Deductible toggle (expense only, only meaningful for non-micro regimes) -->
    <n-form-item v-if="isExpense && showDeductibleToggle" :label="t('pro.transactions.deductible')">
      <n-switch v-model:value="txForm.is_deductible">
        <template #checked>{{ t('pro.transactions.deductible') }}</template>
        <template #unchecked>{{ t('pro.transactions.notDeductible') }}</template>
      </n-switch>
    </n-form-item>

    <n-form-item :label="t('transaction.comment')">
      <n-input v-model:value="txForm.comment" type="textarea" :rows="2" />
    </n-form-item>

    <n-button type="primary" block :loading="loading" @click="handleSubmit">{{ t('common.save') }}</n-button>
  </n-form>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {
  NForm, NFormItem, NCard, NButton, NSelect, NInput, NInputNumber,
  NRadioGroup, NRadioButton, NDatePicker, NDivider, NSwitch, useMessage
} from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useProjectStore } from '@/stores/project'
import type { ProTransaction } from '@/services/api'

interface Props {
  editingTx?: ProTransaction | null
}

const props = withDefaults(defineProps<Props>(), {
  editingTx: null,
})

const emit = defineEmits<{
  (e: 'success'): void
}>()

const { t } = useI18n()
const proStore = useProStore()
const projectStore = useProjectStore()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
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
  project_category_id: null as string | null,
  is_declared: false,
  is_deductible: true,
})

const showDeductibleToggle = computed(() => (proStore.proProfile?.legal_form ?? 'micro') !== 'micro')

const isExpense = computed(() => txForm.value.transaction_type === 'expense')

const clientOptions = computed(() =>
  proStore.proClients.map(c => ({ label: c.name, value: c.id }))
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

const projectCategoryOptions = computed(() => {
  const options: { type: 'group'; label: string; key: string; children: { label: string; value: string }[] }[] = []
  for (const project of projectStore.projects.filter(p => p.status === 'active' && p.mode === 'pro')) {
    if (project.categories.length > 0) {
      options.push({
        type: 'group',
        label: project.name,
        key: project.id,
        children: project.categories.map(c => ({
          label: `${c.name} (${c.remaining.toFixed(2)} € restant)`,
          value: c.id,
        })),
      })
    }
  }
  return options
})

const selectedGiftCardBalance = computed(() => {
  if (!txForm.value.gift_card_id) return 0
  const gc = proStore.proGiftCards.find(g => g.id === txForm.value.gift_card_id)
  return gc ? gc.remaining_balance : 0
})

const itemsTotal = computed(() =>
  txForm.value.items.reduce((sum, i) => sum + (i.quantity || 0) * (i.unit_price || 0), 0)
)

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

const autoTitle = computed(() => {
  if (txForm.value.items.length === 0) return ''
  return txForm.value.items.map(i => {
    const name = getProductName(i.product_id)
    return i.quantity > 1 ? `${name} x${i.quantity}` : name
  }).join(' + ')
})

// Sync items with the multi-select of products
watch(selectedProductIds, (newIds) => {
  const currentIds = txForm.value.items.map(i => i.product_id)
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
  txForm.value.items = txForm.value.items.filter(i => newIds.includes(i.product_id))
})

// Reset income-only state when switching to expense to avoid stale payload
watch(() => txForm.value.transaction_type, (newType) => {
  // Reset category since it's filtered by type
  txForm.value.category_id = null
  if (newType === 'expense') {
    selectedProductIds.value = []
    txForm.value.items = []
    discountMode.value = 'none'
    txForm.value.discount_value = null
    txForm.value.coupon_id = null
    txForm.value.gift_card_id = null
    txForm.value.gift_card_amount = null
    txForm.value.project_category_id = null
    txForm.value.is_declared = false
  }
})

const formRules = computed<FormRules>(() => ({
  transaction_type: { required: true, message: t('errors.required'), trigger: 'change' },
  title: {
    required: !autoTitle.value,
    message: t('errors.required'),
    trigger: 'blur',
  },
  amount: {
    required: txForm.value.items.length === 0,
    type: 'number',
    min: 0.01,
    message: t('errors.required'),
    trigger: 'blur',
  },
  category_id: { required: true, message: t('errors.required'), trigger: 'change' },
  date: { required: true, type: 'number', message: t('errors.required'), trigger: 'change' },
  payment_method: {
    required: true,
    message: t('pro.transactions.paymentMethodRequired'),
    trigger: 'change',
  },
  client_id: {
    required: true,
    message: isExpense.value
      ? t('pro.transactions.supplierRequired')
      : t('pro.transactions.clientRequired'),
    trigger: 'change',
  },
}))

function getProductName(productId: string) {
  return proStore.proProducts.find(p => p.id === productId)?.name || '?'
}

function removeItem(idx: number) {
  const removed = txForm.value.items[idx]
  txForm.value.items.splice(idx, 1)
  if (removed) {
    selectedProductIds.value = selectedProductIds.value.filter(id => id !== removed.product_id)
  }
}

function formatDate(ts: number) {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function resetForm() {
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
    project_category_id: null,
    is_declared: false,
    is_deductible: true,
  }
}

function loadFromTx(tx: ProTransaction) {
  selectedProductIds.value = []
  discountMode.value = 'none'
  txForm.value = {
    transaction_type: tx.transaction_type as 'income' | 'expense',
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
    project_category_id: tx.project_category_id || null,
    is_declared: tx.is_declared === 1,
    is_deductible: tx.is_deductible !== 0,
  }
}

watch(
  () => props.editingTx,
  (tx) => {
    if (tx) loadFromTx(tx)
    else resetForm()
  },
  { immediate: true },
)

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  const hasItems = !isExpense.value && txForm.value.items.length > 0
  const title = txForm.value.title || (hasItems ? autoTitle.value : '')
  const amount = hasItems ? itemsTotal.value : txForm.value.amount

  if (!title && !hasItems) return
  if (!amount && !hasItems) return
  if (!txForm.value.category_id) return

  loading.value = true
  try {
    if (props.editingTx) {
      await proStore.updateTransaction(props.editingTx.id, {
        title,
        amount: amount || undefined,
        transaction_type: txForm.value.transaction_type,
        category_id: txForm.value.category_id,
        client_id: txForm.value.client_id || undefined,
        date: formatDate(txForm.value.date),
        payment_method: txForm.value.payment_method,
        comment: txForm.value.comment || undefined,
        project_category_id: txForm.value.project_category_id,
        is_declared: !isExpense.value ? (txForm.value.is_declared ? 1 : 0) : undefined,
        is_deductible: isExpense.value ? (txForm.value.is_deductible ? 1 : 0) : undefined,
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
        project_category_id: txForm.value.project_category_id,
        is_declared: !isExpense.value && txForm.value.is_declared ? 1 : 0,
        is_deductible: isExpense.value ? (txForm.value.is_deductible ? 1 : 0) : 1,
      }
      if (hasItems) {
        data.items = txForm.value.items.map(i => ({
          product_id: i.product_id,
          quantity: i.quantity,
          unit_price: i.unit_price,
        }))
      }
      if (!isExpense.value) {
        if (discountMode.value === 'coupon' && txForm.value.coupon_id) {
          data.coupon_id = txForm.value.coupon_id
        } else if (discountMode.value === 'manual' && txForm.value.discount_value) {
          data.discount_type = txForm.value.discount_type
          data.discount_value = txForm.value.discount_value
        }
        if (txForm.value.gift_card_id && txForm.value.gift_card_amount) {
          data.gift_card_id = txForm.value.gift_card_id
          data.gift_card_amount = txForm.value.gift_card_amount
        }
      }
      await proStore.createTransaction(data as Parameters<typeof proStore.createTransaction>[0])
      message.success(t('transaction.transactionAdded'))
    }

    await proStore.fetchDashboard()
    emit('success')
    if (!props.editingTx) resetForm()
  } catch (error) {
    console.error('Error saving pro transaction:', error)
    message.error(t('errors.generic'))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Ensure all reference data is loaded for the form (idempotent — store-cached)
  await Promise.all([
    proStore.fetchClients(),
    proStore.fetchCategories(),
    proStore.fetchProducts(),
    proStore.fetchCoupons(),
    proStore.fetchGiftCards(),
    projectStore.fetchProjects(),
  ])
})
</script>
