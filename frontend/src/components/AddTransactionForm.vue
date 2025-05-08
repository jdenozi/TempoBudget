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

import { ref, computed } from 'vue'
import {
  NForm, NFormItem, NInput, NInputNumber, NSelect, NRadioGroup,
  NRadioButton, NButton, NDatePicker, NCheckbox, NCollapseTransition,
  NSpace, useMessage
} from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'

const emit = defineEmits(['success'])
const message = useMessage()
const formRef = ref<FormInst | null>(null)

/** Transaction form data */
const transaction = ref({
  type: 'expense',
  budgetId: null,
  category: null,
  amount: null,
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

/** Available budget options */
const budgetOptions = [
  { label: 'Personal Budget', value: 1 },
  { label: 'Couple Budget', value: 2 }
]

/** Available category options */
const categoryOptions = [
  { label: 'Housing', value: 'Housing' },
  { label: 'Groceries', value: 'Groceries' },
  { label: 'Health', value: 'Health' },
  { label: 'Vehicle', value: 'Vehicle' },
  { label: 'Leisure', value: 'Leisure' },
  { label: 'Sports', value: 'Sports' },
  { label: 'Couple', value: 'Couple' },
  { label: 'Savings', value: 'Savings' },
  { label: 'Pets', value: 'Pets' }
]

/** Available frequency options for recurring transactions */
const frequencyOptions = [
  { label: 'Monthly', value: 'monthly' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Yearly', value: 'yearly' }
]

/**
 * Handles form submission.
 * Validates the form and emits success event if valid.
 */
const handleSubmit = () => {
  formRef.value?.validate((errors) => {
    if (!errors) {
      console.log('Transaction:', transaction.value)
      message.success('Transaction saved!')
      emit('success')

      // Reset form
      transaction.value = {
        type: 'expense',
        budgetId: null,
        category: null,
        amount: null,
        title: '',
        date: Date.now(),
        comment: '',
        isRecurring: false,
        recurringFrequency: 'monthly',
        recurringDay: 1
      }
    }
  })
}
</script>