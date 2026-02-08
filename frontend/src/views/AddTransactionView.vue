<template>
  <n-drawer-content :title="t('transaction.addTransaction')" closable>
    <n-form ref="formRef" :model="transaction" :rules="rules">
      <n-form-item :label="t('transaction.type')" path="type">
        <n-radio-group v-model:value="transaction.type">
          <n-space>
            <n-radio value="expense">
              <n-tag type="error">{{ t('transaction.expense') }}</n-tag>
            </n-radio>
            <n-radio value="income">
              <n-tag type="success">{{ t('transaction.income') }}</n-tag>
            </n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>

      <n-form-item :label="t('category.title')" path="categoryId">
        <n-select
          v-model:value="transaction.categoryId"
          :options="categoryOptions"
          :placeholder="t('placeholders.selectCategory')"
        />
      </n-form-item>

      <n-form-item :label="t('transaction.amount')" path="amount">
        <n-input-number
          v-model:value="transaction.amount"
          :min="0"
          :precision="2"
          class="full-width"
        >
          <template #suffix>€</template>
        </n-input-number>
      </n-form-item>

      <n-form-item :label="t('transaction.transactionTitle')" path="title">
        <n-input v-model:value="transaction.title" :placeholder="t('transaction.transactionTitle')" />
      </n-form-item>

      <n-form-item :label="t('transaction.date')" path="date">
        <n-date-picker
          v-model:value="transaction.date"
          type="date"
          class="full-width"
        />
      </n-form-item>

      <n-form-item :label="t('transaction.comment')">
        <n-input
          v-model:value="transaction.comment"
          type="textarea"
          :placeholder="t('transaction.comment')"
          :rows="3"
        />
      </n-form-item>

      <n-form-item>
        <n-checkbox v-model:checked="transaction.isRecurring">
          {{ t('recurring.title') }}
        </n-checkbox>
      </n-form-item>

      <n-collapse-transition :show="transaction.isRecurring">
        <n-space vertical>
          <n-form-item :label="t('recurring.frequency')" path="recurringFrequency">
            <n-select
              v-model:value="transaction.recurringFrequency"
              :options="frequencyOptions"
              :placeholder="t('placeholders.selectFrequency')"
            />
          </n-form-item>

          <n-form-item v-if="transaction.recurringFrequency === 'monthly'" :label="t('recurring.dayOfMonth')">
            <n-input-number
              v-model:value="transaction.recurringDay"
              :min="1"
              :max="31"
              class="full-width"
            />
          </n-form-item>
        </n-space>
      </n-collapse-transition>
    </n-form>

    <template #footer>
      <n-space justify="end">
        <n-button @click="emit('close')">{{ t('common.cancel') }}</n-button>
        <n-button type="primary" :loading="loading" @click="handleSubmit">
          {{ t('common.add') }}
        </n-button>
      </n-space>
    </template>
  </n-drawer-content>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { FormInst, FormRules } from 'naive-ui'
import {
  NDrawerContent, NForm, NFormItem, NInput, NInputNumber, NSelect,
  NDatePicker, NCheckbox, NRadioGroup, NRadio, NTag, NButton,
  NSpace, NCollapseTransition, useMessage
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useBudgetStore } from '@/stores/budget'
import { recurringAPI } from '@/services/api'
import { formatDateLocal } from '@/utils/date'

const { t } = useI18n()

type TransactionType = 'expense' | 'income'
type RecurringFrequency = 'monthly' | 'weekly' | 'yearly'

interface TransactionForm {
  type: TransactionType
  categoryId: string | null
  amount: number
  title: string
  date: number
  comment: string
  isRecurring: boolean
  recurringFrequency: RecurringFrequency
  recurringDay: number
}

const frequencyOptions = computed(() => [
  { label: t('recurring.monthly'), value: 'monthly' },
  { label: t('recurring.weekly'), value: 'weekly' },
  { label: t('recurring.yearly'), value: 'yearly' },
])

const createInitialForm = (categoryId: string | null = null): TransactionForm => ({
  type: 'expense',
  categoryId,
  amount: 0,
  title: '',
  date: Date.now(),
  comment: '',
  isRecurring: false,
  recurringFrequency: 'monthly',
  recurringDay: 1,
})

const emit = defineEmits<{
  close: []
  success: []
}>()

const message = useMessage()
const budgetStore = useBudgetStore()

const loading = ref(false)
const formRef = ref<FormInst | null>(null)
const transaction = ref<TransactionForm>(createInitialForm())

const rules = computed<FormRules>(() => ({
  categoryId: {
    required: true,
    message: t('errors.required'),
    trigger: 'change',
  },
  amount: {
    required: true,
    type: 'number',
    trigger: 'blur',
    validator: (_rule, value: number) => {
      if (!value || value <= 0) {
        return new Error(t('errors.required'))
      }
      return true
    },
  },
  title: {
    required: true,
    message: t('errors.required'),
    trigger: 'blur',
  },
  date: {
    required: true,
    type: 'number',
    message: t('errors.required'),
    trigger: 'change',
  },
}))

const categoryOptions = computed(() =>
  budgetStore.categories.map(c => ({
    label: c.name,
    value: c.id,
  }))
)

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  if (!budgetStore.currentBudget) {
    message.error(t('budget.noBudgets'))
    return
  }

  loading.value = true
  try {
    const dateString = formatDateLocal(transaction.value.date)

    if (transaction.value.isRecurring) {
      await recurringAPI.create({
        budget_id: budgetStore.currentBudget.id,
        category_id: transaction.value.categoryId!,
        title: transaction.value.title,
        amount: transaction.value.amount,
        transaction_type: transaction.value.type,
        frequency: transaction.value.recurringFrequency,
        day: transaction.value.recurringFrequency === 'monthly'
          ? transaction.value.recurringDay
          : undefined,
      })
      message.success(t('transaction.transactionAdded'))
    } else {
      await budgetStore.createTransaction({
        budget_id: budgetStore.currentBudget.id,
        category_id: transaction.value.categoryId!,
        title: transaction.value.title,
        amount: transaction.value.amount,
        transaction_type: transaction.value.type,
        date: dateString,
        comment: transaction.value.comment || undefined,
      })
      message.success(t('transaction.transactionAdded'))
    }

    transaction.value = createInitialForm(budgetStore.categories[0]?.id ?? null)
    emit('success')
    emit('close')
  } catch (error) {
    console.error('Error creating transaction:', error)
    message.error(t('errors.generic'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (budgetStore.categories.length > 0) {
    transaction.value.categoryId = budgetStore.categories[0].id
  }
})
</script>

<style scoped>
.full-width {
  width: 100%;
}
</style>
