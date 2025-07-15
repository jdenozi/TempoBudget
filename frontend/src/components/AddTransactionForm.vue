<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Add Transaction Form Component

  A comprehensive form for creating new transactions with support for:
  - Income and expense types
  - Budget and category selection
  - Amount, title, and date entry
  - Optional recurring transaction configuration
  - Comments/notes
-->

<template>
  <n-form ref="formRef" :model="transaction" :rules="rules">
    <!-- Transaction Type -->
    <n-form-item label="Type" path="type">
      <n-radio-group v-model:value="transaction.type" size="small">
        <n-radio-button value="expense">
          <span style="color: #d03050;">Expense</span>
        </n-radio-button>
        <n-radio-button value="income">
          <span style="color: #18a058;">Income</span>
        </n-radio-button>
      </n-radio-group>
    </n-form-item>

    <!-- Budget Selection -->
    <n-form-item label="Budget" path="budgetId">
      <n-select
        v-model:value="transaction.budgetId"
        :options="budgetOptions"
        placeholder="Select budget"
        size="small"
      />
    </n-form-item>

    <!-- Category Selection -->
    <n-form-item label="Category" path="category">
      <n-select
        v-model:value="transaction.category"
        :options="categoryOptions"
        placeholder="Select category"
        filterable
        tag
        size="small"
      />
    </n-form-item>

    <!-- Amount -->
    <n-form-item label="Amount" path="amount">
      <n-input-number
        v-model:value="transaction.amount"
        style="width: 100%;"
        :min="0.01"
        :precision="2"
        size="small"
      >
        <template #suffix>€</template>
      </n-input-number>
    </n-form-item>

    <!-- Title -->
    <n-form-item label="Title" path="title">
      <n-input
        v-model:value="transaction.title"
        placeholder="e.g., Groceries"
        size="small"
      />
    </n-form-item>

    <!-- Date -->
    <n-form-item label="Date" path="date">
      <n-date-picker
        v-model:value="transaction.date"
        type="date"
        style="width: 100%;"
        size="small"
      />
    </n-form-item>

    <!-- Recurring Option -->
    <n-form-item label="Recurring">
      <n-checkbox v-model:checked="transaction.isRecurring">
        Recurring transaction
      </n-checkbox>
    </n-form-item>

    <n-collapse-transition :show="transaction.isRecurring">
      <n-space vertical>
        <n-form-item label="Frequency">
          <n-select
            v-model:value="transaction.recurringFrequency"
            :options="frequencyOptions"
            size="small"
          />
        </n-form-item>

        <n-form-item label="Day of month" v-if="transaction.recurringFrequency === 'monthly'">
          <n-input-number
            v-model:value="transaction.recurringDay"
            :min="1"
            :max="31"
            style="width: 100%;"
            size="small"
          />
        </n-form-item>
      </n-space>
    </n-collapse-transition>

    <!-- Comment -->
    <n-form-item label="Comment">
      <n-input
        v-model:value="transaction.comment"
        type="textarea"
        placeholder="Notes..."
        :rows="2"
        size="small"
      />
    </n-form-item>

    <!-- Submit Button -->
    <n-button
      type="primary"
      @click="handleSubmit"
      block
      size="medium"
      style="margin-top: 16px;"
    >
      Save
    </n-button>
  </n-form>
</template>

<script setup lang="ts">
/**
 * Transaction creation form component.
 *
 * Emits:
 * - success: When a transaction is successfully created
 *
 * Features:
 * - Form validation
 * - Support for recurring transactions
 * - Dynamic category selection with tagging
 */

import { ref, computed, watch, onMounted } from 'vue'
import {
  NForm, NFormItem, NInput, NInputNumber, NSelect, NRadioGroup,
  NRadioButton, NButton, NDatePicker, NCheckbox, NCollapseTransition,
  NSpace, useMessage
} from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { useBudgetStore } from '@/stores/budget'
import { recurringAPI } from '@/services/api'

const emit = defineEmits(['success'])
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const budgetStore = useBudgetStore()
const loading = ref(false)

/** Transaction form data */
const transaction = ref({
  type: 'expense',
  budgetId: null as string | null,
  category: null as string | null,
  amount: null as number | null,
  title: '',
  date: Date.now(),
  comment: '',
  isRecurring: false,
  recurringFrequency: 'monthly',
  recurringDay: 1
})

/** Form validation rules */
const rules: FormRules = {
  budgetId: {
    required: true,
    message: 'Budget is required',
    trigger: 'change'
  },
  category: {
    required: true,
    message: 'Category is required',
    trigger: 'change'
  },
  amount: {
    required: true,
    type: 'number',
    message: 'Amount is required',
    trigger: 'blur'
  },
  title: {
    required: true,
    message: 'Title is required',
    trigger: 'blur'
  }
}

/** Available budget options from API */
const budgetOptions = computed(() =>
  budgetStore.budgets.map(b => ({ label: b.name, value: b.id }))
)

/** Available category options from API */
const categoryOptions = computed(() =>
  budgetStore.categories.map(c => ({ label: c.name, value: c.id }))
)

/** Available frequency options for recurring transactions */
const frequencyOptions = [
  { label: 'Monthly', value: 'monthly' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Yearly', value: 'yearly' }
]

// Load budgets on mount
onMounted(async () => {
  await budgetStore.fetchBudgets()
  if (budgetStore.budgets.length > 0) {
    transaction.value.budgetId = budgetStore.budgets[0].id
  }
})

// Load categories when budget changes
watch(() => transaction.value.budgetId, async (budgetId) => {
  if (budgetId) {
    await budgetStore.fetchCategories(budgetId)
    transaction.value.category = null
  }
})

/**
 * Handles form submission.
 * Validates the form and creates transaction via API.
 */
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  if (!transaction.value.budgetId || !transaction.value.category || !transaction.value.amount) {
    return
  }

  loading.value = true
  try {
    const dateString = new Date(transaction.value.date).toISOString().split('T')[0]

    if (transaction.value.isRecurring) {
      await recurringAPI.create({
        budget_id: transaction.value.budgetId,
        category_id: transaction.value.category,
        title: transaction.value.title,
        amount: transaction.value.amount,
        transaction_type: transaction.value.type,
        frequency: transaction.value.recurringFrequency,
        day: transaction.value.recurringFrequency === 'monthly'
          ? transaction.value.recurringDay
          : undefined,
      })
      message.success('Recurring transaction created!')
    } else {
      await budgetStore.createTransaction({
        budget_id: transaction.value.budgetId,
        category_id: transaction.value.category,
        title: transaction.value.title,
        amount: transaction.value.amount,
        transaction_type: transaction.value.type,
        date: dateString,
        comment: transaction.value.comment || undefined,
      })
      message.success('Transaction saved!')
    }

    emit('success')

    // Reset form
    transaction.value = {
      type: 'expense',
      budgetId: budgetStore.budgets[0]?.id ?? null,
      category: null,
      amount: null,
      title: '',
      date: Date.now(),
      comment: '',
      isRecurring: false,
      recurringFrequency: 'monthly',
      recurringDay: 1
    }
  } catch (error) {
    console.error('Error creating transaction:', error)
    message.error('Error creating transaction')
  } finally {
    loading.value = false
  }
}
</script>