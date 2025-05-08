<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Recurring Transactions View

  Displays and manages recurring transaction templates for a selected budget.
  Supports toggling active status and deletion of recurring transactions.
-->

<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">Recurring Transactions</h1>

    <!-- Budget Selector -->
    <n-select
      v-model:value="selectedBudgetId"
      :options="budgetOptions"
      placeholder="Select a budget"
      :style="{ width: isMobile ? '100%' : '300px' }"
      @update:value="loadRecurring"
    />

    <!-- Loading State -->
    <div v-if="budgetStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <!-- Mobile View: Cards -->
    <n-space v-else-if="isMobile && budgetStore.recurringTransactions.length > 0" vertical>
      <n-card
        v-for="recurring in budgetStore.recurringTransactions"
        :key="recurring.id"
        size="small"
      >
        <template #header>
          <n-space justify="space-between" align="center">
            <strong>{{ recurring.title }}</strong>
            <n-tag
              :type="recurring.transaction_type === 'expense' ? 'error' : 'success'"
              size="small"
            >
              {{ recurring.transaction_type === 'expense' ? '-' : '+' }}{{ recurring.amount.toFixed(2) }} €
            </n-tag>
          </n-space>
        </template>

        <n-space vertical size="small">
          <div><n-text depth="3">Frequency:</n-text> {{ getFrequencyLabel(recurring.frequency) }}</div>
          <div v-if="recurring.day"><n-text depth="3">Day:</n-text> {{ recurring.day }}</div>
          <div>
            <n-text depth="3">Status:</n-text>
            <n-tag :type="recurring.active ? 'success' : 'default'" size="small" style="margin-left: 8px;">
              {{ recurring.active ? 'Active' : 'Inactive' }}
            </n-tag>
          </div>
        </n-space>

        <template #footer>
          <n-space>
            <n-button
              size="small"
              :type="recurring.active ? 'default' : 'success'"
              @click="handleToggle(recurring.id)"
            >
              {{ recurring.active ? 'Deactivate' : 'Activate' }}
            </n-button>
            <n-popconfirm @positive-click="handleDelete(recurring.id)">
              <template #trigger>
                <n-button size="small" type="error">
                  Delete
                </n-button>
              </template>
              Delete this recurring transaction?
            </n-popconfirm>
          </n-space>
        </template>
      </n-card>
    </n-space>

    <!-- Desktop View: Table -->
    <n-card v-else-if="!isMobile && budgetStore.recurringTransactions.length > 0">
      <n-data-table
        :columns="columns"
        :data="budgetStore.recurringTransactions"
        :pagination="pagination"
      />
    </n-card>

    <!-- Empty States -->
    <n-empty
      v-else-if="!budgetStore.loading && selectedBudgetId"
      description="No recurring transactions"
    />

    <n-empty
      v-else-if="!budgetStore.loading && !selectedBudgetId"
      description="Select a budget"
    />
  </n-space>
</template>

<script setup lang="ts">
/**
 * Recurring transactions management view.
 *
 * Features:
 * - Budget selection dropdown
 * - Responsive card (mobile) / table (desktop) layout
 * - Toggle active status for recurring transactions
 * - Delete recurring transactions with confirmation
 */

import { ref, h, computed, onMounted, onUnmounted } from 'vue'
import {
  NSpace, NCard, NTag, NText, NButton, NDataTable, NPopconfirm,
  NSelect, NSpin, NEmpty, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useBudgetStore } from '@/stores/budget'
import type { RecurringTransaction } from '@/services/api'

const message = useMessage()
const budgetStore = useBudgetStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Currently selected budget ID */
const selectedBudgetId = ref<string | null>(null)

/**
 * Checks if the viewport is mobile-sized.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // Load budgets if not already loaded
  if (budgetStore.budgets.length === 0) {
    await budgetStore.fetchBudgets()
  }

  // Select the first budget by default
  if (budgetStore.budgets.length > 0) {
    selectedBudgetId.value = budgetStore.budgets[0].id
    await loadRecurring()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

/** Budget options for the selector */
const budgetOptions = computed(() => {
  return budgetStore.budgets.map(b => ({
    label: b.name,
    value: b.id,
  }))
})

/**
 * Loads recurring transactions for the selected budget.
 */
const loadRecurring = async () => {
  if (!selectedBudgetId.value) return

  try {
    await budgetStore.fetchRecurringTransactions(selectedBudgetId.value)
  } catch (error) {
    console.error('Error loading recurring:', error)
    message.error('Error loading data')
  }
}

/**
 * Returns a human-readable label for the frequency.
 * @param frequency - The frequency value
 */
const getFrequencyLabel = (frequency: string) => {
  const labels: Record<string, string> = {
    monthly: 'Monthly',
    weekly: 'Weekly',
    yearly: 'Yearly',
  }
  return labels[frequency] || frequency
}

/**
 * Toggles the active status of a recurring transaction.
 * @param id - Recurring transaction ID
 */
const handleToggle = async (id: string) => {
  try {
    await budgetStore.toggleRecurringTransaction(id)
    message.success('Status updated')
  } catch (error) {
    console.error('Error toggling recurring:', error)
    message.error('Error updating status')
  }
}

/**
 * Deletes a recurring transaction.
 * @param id - Recurring transaction ID
 */
const handleDelete = async (id: string) => {
  try {
    await budgetStore.deleteRecurringTransaction(id)
    message.success('Recurring transaction deleted')
  } catch (error) {
    console.error('Error deleting recurring:', error)
    message.error('Error deleting')
  }
}

/** Table pagination configuration */
const pagination = {
  pageSize: 10,
}

/** Table columns definition */
const columns: DataTableColumns<RecurringTransaction> = [
  {
    title: 'Title',
    key: 'title',
  },
  {
    title: 'Amount',
    key: 'amount',
    render: (row) => {
      const sign = row.transaction_type === 'expense' ? '-' : '+'
      const color = row.transaction_type === 'expense' ? '#d03050' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } },
        `${sign}${row.amount.toFixed(2)} €`
      )
    },
  },
  {
    title: 'Frequency',
    key: 'frequency',
    render: (row) => getFrequencyLabel(row.frequency),
  },
  {
    title: 'Day',
    key: 'day',
    render: (row) => row.day || '-',
  },
  {
    title: 'Status',
    key: 'active',
    render: (row) => {
      return h(NTag, {
        type: row.active ? 'success' : 'default',
        size: 'small',
      }, { default: () => row.active ? 'Active' : 'Inactive' })
    },
  },
  {
    title: 'Actions',
    key: 'actions',
    render: (row) => {
      return h('div', { style: { display: 'flex', gap: '8px' } }, [
        h(NButton, {
          size: 'small',
          type: row.active ? 'default' : 'success',
          onClick: () => handleToggle(row.id),
        }, { default: () => row.active ? 'Deactivate' : 'Activate' }),
        h(NPopconfirm, {
          onPositiveClick: () => handleDelete(row.id),
        }, {
          default: () => 'Delete this recurring transaction?',
          trigger: () => h(NButton, {
            size: 'small',
            type: 'error',
          }, { default: () => 'Delete' }),
        }),
      ])
    },
  },
]
</script>