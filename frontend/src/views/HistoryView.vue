<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Transaction History View

  Displays all transactions for a selected budget with summary statistics.
  Supports filtering by budget and transaction deletion.
-->

<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">Transaction History</h1>

    <!-- Budget Selector -->
    <n-select
      v-model:value="selectedBudgetId"
      :options="budgetOptions"
      placeholder="Select a budget"
      :style="{ width: isMobile ? '100%' : '300px' }"
      @update:value="loadTransactions"
    />

    <!-- Loading State -->
    <div v-if="budgetStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <template v-else-if="selectedBudgetId">
      <!-- Summary Statistics -->
      <n-card size="small">
        <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
          <n-gi>
            <n-statistic label="Transactions" :value="budgetStore.transactions.length" />
          </n-gi>
          <n-gi>
            <n-statistic label="Total Income">
              <template #prefix>€</template>
              {{ totalIncome.toFixed(2) }}
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic label="Total Expenses">
              <template #prefix>€</template>
              {{ totalExpenses.toFixed(2) }}
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic label="Balance">
              <template #prefix>€</template>
              {{ (totalIncome - totalExpenses).toFixed(2) }}
            </n-statistic>
          </n-gi>
        </n-grid>
      </n-card>

      <!-- Mobile View: Cards -->
      <n-space v-if="isMobile && budgetStore.transactions.length > 0" vertical>
        <n-card
          v-for="transaction in budgetStore.transactions"
          :key="transaction.id"
          size="small"
        >
          <template #header>
            <n-space justify="space-between">
              <strong>{{ transaction.title }}</strong>
              <n-tag :type="transaction.transaction_type === 'expense' ? 'error' : 'success'" size="small">
                {{ transaction.transaction_type === 'expense' ? '-' : '+' }}{{ transaction.amount.toFixed(2) }} €
              </n-tag>
            </n-space>
          </template>

          <n-space vertical size="small">
            <div>
              <n-text depth="3">Date:</n-text> {{ formatDate(transaction.date) }}
            </div>
            <div v-if="transaction.comment">
              <n-text depth="3">Comment:</n-text> {{ transaction.comment }}
            </div>
          </n-space>

          <template #footer>
            <n-space>
              <n-popconfirm @positive-click="handleDelete(transaction.id)">
                <template #trigger>
                  <n-button size="small" type="error">
                    Delete
                  </n-button>
                </template>
                Delete this transaction?
              </n-popconfirm>
            </n-space>
          </template>
        </n-card>
      </n-space>

      <!-- Desktop View: Table -->
      <n-card v-else-if="!isMobile && budgetStore.transactions.length > 0">
        <n-data-table
          :columns="columns"
          :data="budgetStore.transactions"
          :pagination="pagination"
        />
      </n-card>

      <!-- Empty State: No Transactions -->
      <n-empty
        v-else
        description="No transactions"
      />
    </template>

    <!-- Empty State: No Budget Selected -->
    <n-empty
      v-else-if="!budgetStore.loading"
      description="Select a budget"
    />
  </n-space>
</template>

<script setup lang="ts">
/**
 * Transaction history view component.
 *
 * Features:
 * - Budget selection dropdown
 * - Summary statistics (total income, expenses, balance)
 * - Responsive card (mobile) / table (desktop) layout
 * - Transaction deletion with confirmation
 */

import { ref, h, computed, onMounted, onUnmounted } from 'vue'
import {
  NSpace, NCard, NTag, NText, NButton, NDataTable, NPopconfirm,
  NSelect, NGrid, NGi, NStatistic, NSpin, NEmpty, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useBudgetStore } from '@/stores/budget'
import type { Transaction } from '@/services/api'

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
    await loadTransactions()
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
 * Loads transactions for the selected budget.
 */
const loadTransactions = async () => {
  if (!selectedBudgetId.value) return

  try {
    await budgetStore.fetchTransactions(selectedBudgetId.value)
  } catch (error) {
    console.error('Error loading transactions:', error)
    message.error('Error loading data')
  }
}

/** Total income amount */
const totalIncome = computed(() => {
  return budgetStore.transactions
    .filter(t => t.transaction_type === 'income')
    .reduce((sum, t) => sum + t.amount, 0)
})

/** Total expenses amount */
const totalExpenses = computed(() => {
  return budgetStore.transactions
    .filter(t => t.transaction_type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0)
})

/**
 * Formats a date string for display.
 * @param dateString - ISO date string
 */
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

/**
 * Deletes a transaction.
 * @param id - Transaction ID
 */
const handleDelete = async (id: string) => {
  try {
    await budgetStore.deleteTransaction(id)
    message.success('Transaction deleted')
  } catch (error) {
    console.error('Error deleting transaction:', error)
    message.error('Error deleting')
  }
}

/** Table pagination configuration */
const pagination = {
  pageSize: 20,
}

/** Table columns definition */
const columns: DataTableColumns<Transaction> = [
  {
    title: 'Date',
    key: 'date',
    render: (row) => formatDate(row.date),
    sorter: (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  },
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
    sorter: (a, b) => a.amount - b.amount,
  },
  {
    title: 'Comment',
    key: 'comment',
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: 'Actions',
    key: 'actions',
    render: (row) => {
      return h(NPopconfirm, {
        onPositiveClick: () => handleDelete(row.id),
      }, {
        default: () => 'Delete this transaction?',
        trigger: () => h(NButton, {
          size: 'small',
          type: 'error',
        }, { default: () => 'Delete' }),
      })
    },
  },
]
</script>