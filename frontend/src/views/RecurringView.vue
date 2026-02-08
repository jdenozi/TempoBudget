<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Recurring Transactions View

  Displays and manages recurring transaction templates for a selected budget.
  Supports toggling active status, editing, viewing version history, and deletion.
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

    <!-- Date Range Filter -->
    <n-space :vertical="isMobile" align="center" v-if="selectedBudgetId">
      <span>Période :</span>
      <n-date-picker
        v-model:value="startDate"
        type="date"
        :style="{ width: isMobile ? '100%' : '160px' }"
        placeholder="Date début"
        clearable
      />
      <span>à</span>
      <n-date-picker
        v-model:value="endDate"
        type="date"
        :style="{ width: isMobile ? '100%' : '160px' }"
        placeholder="Date fin"
        clearable
      />
    </n-space>

    <!-- Projections Summary -->
    <n-card v-if="startDate && endDate && budgetStore.recurringTransactions.length > 0" size="small">
      <n-space :vertical="isMobile" justify="space-around">
        <n-statistic label="Revenus projetés">
          <template #default>
            <span style="color: #18a058;">{{ projectedIncome.toFixed(2) }} €</span>
          </template>
        </n-statistic>
        <n-statistic label="Dépenses projetées">
          <template #default>
            <span style="color: #d03050;">{{ projectedExpenses.toFixed(2) }} €</span>
          </template>
        </n-statistic>
        <n-statistic label="Solde net">
          <template #default>
            <span :style="{ color: netBalance >= 0 ? '#18a058' : '#d03050', fontWeight: 'bold' }">
              {{ netBalance >= 0 ? '+' : '' }}{{ netBalance.toFixed(2) }} €
            </span>
          </template>
        </n-statistic>
      </n-space>
    </n-card>

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
            <div>
              <strong>{{ recurring.title }}</strong>
              <n-tag
                v-if="recurring.pending_version"
                type="warning"
                size="tiny"
                style="margin-left: 8px;"
              >
                Pending
              </n-tag>
            </div>
            <n-tag
              :type="recurring.transaction_type === 'expense' ? 'error' : 'success'"
              size="small"
            >
              {{ recurring.transaction_type === 'expense' ? '-' : '+' }}{{ recurring.amount.toFixed(2) }} €
            </n-tag>
          </n-space>
        </template>

        <n-space vertical size="small">
          <div>
            <n-text depth="3">Category:</n-text>
            {{ getCategoryDisplay(recurring) }}
          </div>
          <div><n-text depth="3">Frequency:</n-text> {{ getFrequencyLabel(recurring.frequency) }}</div>
          <div v-if="recurring.day"><n-text depth="3">Day:</n-text> {{ recurring.day }}</div>
          <div>
            <n-text depth="3">Status:</n-text>
            <n-tag :type="recurring.active ? 'success' : 'default'" size="small" style="margin-left: 8px;">
              {{ recurring.active ? 'Active' : 'Inactive' }}
            </n-tag>
          </div>
          <div v-if="recurring.pending_version" style="font-size: 12px; color: #f0a020;">
            Change scheduled for {{ recurring.pending_version.effective_from }}
          </div>
        </n-space>

        <template #footer>
          <n-space>
            <n-button size="small" @click="openEditModal(recurring)">
              Edit
            </n-button>
            <n-button size="small" @click="openHistoryModal(recurring.id)">
              History
            </n-button>
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

    <!-- Edit Modal -->
    <EditRecurringModal
      v-model:show="showEditModal"
      :is-mobile="isMobile"
      :loading="isEditing"
      :recurring="editingRecurring"
      :categories="budgetStore.categories"
      @submit="handleEditSubmit"
    />

    <!-- History Modal -->
    <RecurringVersionHistory
      v-model:show="showHistoryModal"
      :is-mobile="isMobile"
      :recurring-id="historyRecurringId"
      :categories="budgetStore.categories"
      @cancel-version="handleCancelVersion"
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
 * - Edit recurring transactions with effective dates
 * - View version history
 * - Delete recurring transactions with confirmation
 */

import { ref, h, computed, onMounted, onUnmounted } from 'vue'
import {
  NSpace, NCard, NTag, NText, NButton, NDataTable, NPopconfirm,
  NSelect, NSpin, NEmpty, NDatePicker, NStatistic, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useBudgetStore } from '@/stores/budget'
import type { RecurringTransactionWithCategory, UpdateRecurringTransactionPayload } from '@/services/api'
import EditRecurringModal from '@/components/modals/EditRecurringModal.vue'
import RecurringVersionHistory from '@/components/modals/RecurringVersionHistory.vue'

const message = useMessage()
const budgetStore = useBudgetStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Currently selected budget ID */
const selectedBudgetId = ref<string | null>(null)

/** Date range for projections */
const startDate = ref<number | null>(null)
const endDate = ref<number | null>(null)

/** Edit modal state */
const showEditModal = ref(false)
const editingRecurring = ref<RecurringTransactionWithCategory | null>(null)
const isEditing = ref(false)

/** History modal state */
const showHistoryModal = ref(false)
const historyRecurringId = ref<string | null>(null)

/**
 * Checks if the viewport is mobile-sized.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // Set default date range to current month
  const now = new Date()
  startDate.value = new Date(now.getFullYear(), now.getMonth(), 1).getTime()
  endDate.value = new Date(now.getFullYear(), now.getMonth() + 1, 0).getTime()

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
 * Loads recurring transactions and categories for the selected budget.
 */
const loadRecurring = async () => {
  if (!selectedBudgetId.value) return

  try {
    await Promise.all([
      budgetStore.fetchRecurringTransactions(selectedBudgetId.value),
      budgetStore.fetchCategories(selectedBudgetId.value),
    ])
  } catch (error) {
    console.error('Error loading recurring:', error)
    message.error('Error loading data')
  }
}

/**
 * Counts occurrences of a recurring transaction within a date range.
 * @param recurring - The recurring transaction
 * @param start - Start date
 * @param end - End date
 * @returns Number of occurrences
 */
const countOccurrences = (
  recurring: RecurringTransactionWithCategory,
  start: Date,
  end: Date
): number => {
  if (!recurring.active) return 0

  let count = 0

  if (recurring.frequency === 'monthly') {
    const recurringDay = recurring.day || 1
    const current = new Date(start.getFullYear(), start.getMonth(), 1)

    while (current <= end) {
      const lastDayOfMonth = new Date(current.getFullYear(), current.getMonth() + 1, 0).getDate()
      const targetDay = Math.min(recurringDay, lastDayOfMonth)
      const targetDate = new Date(current.getFullYear(), current.getMonth(), targetDay)

      if (targetDate >= start && targetDate <= end) {
        count++
      }
      current.setMonth(current.getMonth() + 1)
    }
  } else if (recurring.frequency === 'weekly') {
    const recurringDayOfWeek = (recurring.day || 1) % 7
    const current = new Date(start)

    while (current.getDay() !== recurringDayOfWeek && current <= end) {
      current.setDate(current.getDate() + 1)
    }

    while (current <= end) {
      count++
      current.setDate(current.getDate() + 7)
    }
  } else if (recurring.frequency === 'yearly') {
    // For yearly, use the creation month and specified day
    const createdAt = new Date(recurring.created_at)
    const recurringMonth = createdAt.getMonth()
    const recurringDay = recurring.day || 1

    let year = start.getFullYear()
    while (year <= end.getFullYear()) {
      const lastDayOfTargetMonth = new Date(year, recurringMonth + 1, 0).getDate()
      const targetDay = Math.min(recurringDay, lastDayOfTargetMonth)
      const targetDate = new Date(year, recurringMonth, targetDay)

      if (targetDate >= start && targetDate <= end) {
        count++
      }
      year++
    }
  }

  return count
}

/** Projected income for the selected period */
const projectedIncome = computed(() => {
  if (!startDate.value || !endDate.value) return 0

  const start = new Date(startDate.value)
  const end = new Date(endDate.value)

  return budgetStore.recurringTransactions
    .filter(r => r.transaction_type === 'income')
    .reduce((sum, r) => sum + (r.amount * countOccurrences(r, start, end)), 0)
})

/** Projected expenses for the selected period */
const projectedExpenses = computed(() => {
  if (!startDate.value || !endDate.value) return 0

  const start = new Date(startDate.value)
  const end = new Date(endDate.value)

  return budgetStore.recurringTransactions
    .filter(r => r.transaction_type === 'expense')
    .reduce((sum, r) => sum + (r.amount * countOccurrences(r, start, end)), 0)
})

/** Net balance for the selected period */
const netBalance = computed(() => projectedIncome.value - projectedExpenses.value)

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
 * Returns the category display string.
 * @param recurring - The recurring transaction
 */
const getCategoryDisplay = (recurring: RecurringTransactionWithCategory) => {
  if (recurring.parent_category_name) {
    return `${recurring.parent_category_name} > ${recurring.category_name}`
  }
  return recurring.category_name
}

/**
 * Opens the edit modal for a recurring transaction.
 * @param recurring - The recurring transaction to edit
 */
const openEditModal = (recurring: RecurringTransactionWithCategory) => {
  editingRecurring.value = recurring
  showEditModal.value = true
}

/**
 * Opens the history modal for a recurring transaction.
 * @param id - The recurring transaction ID
 */
const openHistoryModal = (id: string) => {
  historyRecurringId.value = id
  showHistoryModal.value = true
}

/**
 * Handles the edit form submission.
 * @param data - The update payload
 */
const handleEditSubmit = async (data: UpdateRecurringTransactionPayload) => {
  if (!editingRecurring.value) return

  isEditing.value = true
  try {
    await budgetStore.updateRecurringTransaction(editingRecurring.value.id, data)
    message.success('Recurring transaction updated')
    showEditModal.value = false
    editingRecurring.value = null
  } catch (error) {
    console.error('Error updating recurring:', error)
    message.error('Error updating')
  } finally {
    isEditing.value = false
  }
}

/**
 * Handles canceling a scheduled version.
 * @param versionId - The version ID to cancel
 * @param recurringId - The parent recurring transaction ID
 */
const handleCancelVersion = async (versionId: string, recurringId: string) => {
  try {
    await budgetStore.cancelRecurringVersion(versionId, recurringId)
    message.success('Scheduled change cancelled')
  } catch (error) {
    console.error('Error cancelling version:', error)
    message.error('Error cancelling')
  }
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
const columns: DataTableColumns<RecurringTransactionWithCategory> = [
  {
    title: 'Title',
    key: 'title',
    render: (row) => {
      if (row.pending_version) {
        return h('div', { style: { display: 'flex', alignItems: 'center', gap: '8px' } }, [
          h('span', row.title),
          h(NTag, { type: 'warning', size: 'tiny' }, { default: () => 'Pending' }),
        ])
      }
      return row.title
    },
  },
  {
    title: 'Category',
    key: 'category',
    render: (row) => getCategoryDisplay(row),
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
    width: 280,
    render: (row) => {
      return h('div', { style: { display: 'flex', gap: '8px', flexWrap: 'wrap' } }, [
        h(NButton, {
          size: 'small',
          onClick: () => openEditModal(row),
        }, { default: () => 'Edit' }),
        h(NButton, {
          size: 'small',
          onClick: () => openHistoryModal(row.id),
        }, { default: () => 'History' }),
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
