<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('nav.proRecurring') }}</h1>
      <n-space>
        <n-button @click="handleProcess" :loading="processing">{{ t('recurring.processNow') }}</n-button>
        <n-button type="primary" @click="openCreateModal">{{ t('recurring.addRecurring') }}</n-button>
      </n-space>
    </div>

    <n-empty v-if="proStore.proRecurring.length === 0" :description="t('recurring.noRecurring')" />

    <!-- Desktop table -->
    <n-data-table
      v-if="!isMobile && proStore.proRecurring.length > 0"
      :columns="columns"
      :data="proStore.proRecurring"
      :row-key="(row: ProRecurringTransaction) => row.id"
      :pagination="{ pageSize: 20 }"
    />

    <!-- Mobile cards -->
    <n-space v-if="isMobile && proStore.proRecurring.length > 0" vertical>
      <n-card v-for="rec in proStore.proRecurring" :key="rec.id" size="small">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>{{ rec.title }}</span>
            <span :style="{ color: rec.transaction_type === 'income' ? '#18a058' : '#d03050', fontWeight: 'bold' }">
              {{ rec.transaction_type === 'income' ? '+' : '-' }}{{ rec.amount.toFixed(2) }} €
            </span>
          </div>
        </template>
        <n-space size="small" style="margin-bottom: 8px;">
          <n-tag size="tiny" :type="rec.transaction_type === 'income' ? 'success' : 'error'">{{ rec.category_name }}</n-tag>
          <n-tag size="tiny" type="info">{{ frequencyLabel(rec) }}</n-tag>
          <n-tag v-if="rec.client_name" size="tiny">{{ rec.client_name }}</n-tag>
          <n-tag size="tiny" :type="rec.active === 1 ? 'success' : 'default'">{{ rec.active === 1 ? t('common.active') : t('common.inactive') }}</n-tag>
        </n-space>
        <template #action>
          <n-space size="small">
            <n-button size="tiny" @click="handleToggle(rec)">{{ rec.active === 1 ? t('recurring.deactivate') : t('recurring.activate') }}</n-button>
            <n-button size="tiny" @click="openEditModal(rec)">{{ t('common.edit') }}</n-button>
            <n-popconfirm @positive-click="handleDelete(rec.id)">
              <template #trigger>
                <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
              </template>
              {{ t('recurring.deleteRecurringConfirm') }}
            </n-popconfirm>
          </n-space>
        </template>
      </n-card>
    </n-space>

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="editingRec ? t('recurring.editRecurring') : t('recurring.addRecurring')" style="max-width: 600px;">
      <n-form ref="formRef" :model="form" :rules="rules">
        <n-form-item :label="t('transaction.type')" path="transaction_type">
          <n-radio-group v-model:value="form.transaction_type">
            <n-radio-button value="expense">{{ t('transaction.expense') }}</n-radio-button>
            <n-radio-button value="income">{{ t('transaction.income') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('transaction.transactionTitle')" path="title">
          <n-input v-model:value="form.title" />
        </n-form-item>
        <n-form-item :label="t('transaction.amount')" path="amount">
          <n-input-number v-model:value="form.amount" :min="0.01" :precision="2" style="width: 100%;">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('category.title')" path="category_id">
          <n-select v-model:value="form.category_id" :options="filteredCategoryOptions" :placeholder="t('placeholders.selectCategory')" />
        </n-form-item>
        <n-form-item :label="form.transaction_type === 'expense' ? t('pro.transactions.supplier') : t('pro.transactions.client')">
          <n-select v-model:value="form.client_id" :options="clientOptions" clearable />
        </n-form-item>
        <n-form-item :label="t('recurring.frequency')" path="frequency">
          <n-select v-model:value="form.frequency" :options="frequencyOptions" />
        </n-form-item>
        <n-form-item v-if="form.frequency === 'monthly'" :label="t('recurring.dayOfMonth')">
          <n-input-number v-model:value="form.day" :min="1" :max="31" style="width: 100%;" />
        </n-form-item>
        <n-form-item v-if="form.frequency === 'weekly'" :label="t('recurring.dayOfWeek')">
          <n-select v-model:value="form.day" :options="weekdayOptions" />
        </n-form-item>
        <n-form-item :label="t('pro.transactions.paymentMethod')">
          <n-select v-model:value="form.payment_method" :options="paymentMethodOptions" />
        </n-form-item>
        <n-form-item :label="t('transaction.comment')">
          <n-input v-model:value="form.comment" type="textarea" :rows="2" />
        </n-form-item>
        <n-button type="primary" block :loading="saving" @click="handleSubmit">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NSpace, NCard, NButton, NDataTable, NSelect, NTag, NEmpty, NModal,
  NForm, NFormItem, NInput, NInputNumber, NRadioGroup, NRadioButton,
  NPopconfirm, useMessage,
} from 'naive-ui'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProRecurringTransaction } from '@/services/api'

const { t } = useI18n()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const showModal = ref(false)
const saving = ref(false)
const processing = ref(false)
const editingRec = ref<ProRecurringTransaction | null>(null)
const formRef = ref<FormInst | null>(null)

const form = ref({
  transaction_type: 'expense' as 'income' | 'expense',
  title: '',
  amount: null as number | null,
  category_id: null as string | null,
  client_id: null as string | null,
  frequency: 'monthly' as 'daily' | 'weekly' | 'monthly' | 'yearly',
  day: 1 as number | null,
  payment_method: 'cash',
  comment: '',
})

const rules = computed<FormRules>(() => ({
  transaction_type: { required: true, message: t('errors.required'), trigger: 'change' },
  title: { required: true, message: t('errors.required'), trigger: 'blur' },
  amount: { required: true, type: 'number', min: 0.01, message: t('errors.required'), trigger: 'blur' },
  category_id: { required: true, message: t('errors.required'), trigger: 'change' },
  frequency: { required: true, message: t('errors.required'), trigger: 'change' },
}))

const filteredCategoryOptions = computed(() =>
  proStore.proCategories
    .filter(c => c.type === form.value.transaction_type)
    .map(c => ({ label: c.name, value: c.id }))
)

const clientOptions = computed(() =>
  proStore.proClients.map(c => ({ label: c.name, value: c.id }))
)

const paymentMethodOptions = computed(() => [
  { label: t('pro.transactions.cash'), value: 'cash' },
  { label: t('pro.transactions.bankTransfer'), value: 'bankTransfer' },
  { label: t('pro.transactions.check'), value: 'check' },
  { label: t('pro.transactions.card'), value: 'card' },
  { label: t('pro.transactions.paypal'), value: 'paypal' },
  { label: t('pro.transactions.other'), value: 'other' },
])

const frequencyOptions = computed(() => [
  { label: t('recurring.daily'), value: 'daily' },
  { label: t('recurring.weekly'), value: 'weekly' },
  { label: t('recurring.monthly'), value: 'monthly' },
  { label: t('recurring.yearly'), value: 'yearly' },
])

const weekdayOptions = computed(() => [
  { label: t('days.monday'), value: 0 },
  { label: t('days.tuesday'), value: 1 },
  { label: t('days.wednesday'), value: 2 },
  { label: t('days.thursday'), value: 3 },
  { label: t('days.friday'), value: 4 },
  { label: t('days.saturday'), value: 5 },
  { label: t('days.sunday'), value: 6 },
])

function frequencyLabel(rec: ProRecurringTransaction) {
  const base = t(`recurring.${rec.frequency}`)
  if (rec.frequency === 'monthly' && rec.day != null) return `${base} (${rec.day})`
  if (rec.frequency === 'weekly' && rec.day != null) {
    const wd = weekdayOptions.value.find(o => o.value === rec.day)
    return `${base} (${wd?.label ?? rec.day})`
  }
  return base
}

const columns: DataTableColumns<ProRecurringTransaction> = [
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
  { title: () => t('recurring.frequency'), key: 'frequency', render: (row) => frequencyLabel(row) },
  {
    title: () => t('common.status'),
    key: 'active',
    width: 100,
    render: (row) => h(NTag, { size: 'small', type: row.active === 1 ? 'success' : 'default' }, () => row.active === 1 ? t('common.active') : t('common.inactive')),
  },
  {
    title: () => t('common.actions'),
    key: 'actions',
    width: 220,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', onClick: () => handleToggle(row) }, () => row.active === 1 ? t('recurring.deactivate') : t('recurring.activate')),
        h(NButton, { size: 'small', onClick: () => openEditModal(row) }, () => t('common.edit')),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('recurring.deleteRecurringConfirm'),
        }),
      ])
    },
  },
]

function resetForm() {
  editingRec.value = null
  form.value = {
    transaction_type: 'expense',
    title: '',
    amount: null,
    category_id: null,
    client_id: null,
    frequency: 'monthly',
    day: 1,
    payment_method: 'cash',
    comment: '',
  }
}

function openCreateModal() {
  resetForm()
  showModal.value = true
}

function openEditModal(rec: ProRecurringTransaction) {
  editingRec.value = rec
  form.value = {
    transaction_type: rec.transaction_type,
    title: rec.title,
    amount: rec.amount,
    category_id: rec.category_id,
    client_id: rec.client_id,
    frequency: rec.frequency,
    day: rec.day,
    payment_method: rec.payment_method || 'cash',
    comment: rec.comment || '',
  }
  showModal.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  if (!form.value.category_id || !form.value.amount) return

  saving.value = true
  try {
    if (editingRec.value) {
      await proStore.updateRecurring(editingRec.value.id, {
        client_id: form.value.client_id,
        category_id: form.value.category_id,
        title: form.value.title,
        amount: form.value.amount,
        transaction_type: form.value.transaction_type,
        frequency: form.value.frequency,
        day: form.value.day,
        payment_method: form.value.payment_method,
        comment: form.value.comment || undefined,
      })
      message.success(t('recurring.recurringUpdated'))
    } else {
      await proStore.createRecurring({
        client_id: form.value.client_id ?? undefined,
        category_id: form.value.category_id,
        title: form.value.title,
        amount: form.value.amount,
        transaction_type: form.value.transaction_type,
        frequency: form.value.frequency,
        day: form.value.day,
        payment_method: form.value.payment_method,
        comment: form.value.comment || undefined,
      })
      message.success(t('recurring.recurringAdded'))
    }
    showModal.value = false
    resetForm()
  } catch (e) {
    console.error(e)
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

async function handleToggle(rec: ProRecurringTransaction) {
  await proStore.toggleRecurring(rec.id)
}

async function handleDelete(id: string) {
  await proStore.deleteRecurring(id)
  message.success(t('recurring.recurringDeleted'))
}

async function handleProcess() {
  processing.value = true
  try {
    const created = await proStore.processRecurring()
    if (created.length > 0) {
      message.success(t('recurring.processedCount', { count: created.length }))
    } else {
      message.info(t('recurring.nothingToProcess'))
    }
  } catch (e) {
    console.error(e)
    message.error(t('errors.generic'))
  } finally {
    processing.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    proStore.fetchRecurring(),
    proStore.fetchCategories(),
    proStore.fetchClients(),
  ])
})
</script>
