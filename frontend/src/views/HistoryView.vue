<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Transaction History View

  Displays all transactions for a selected budget with summary statistics.
  Supports filtering by budget and transaction deletion.
-->

<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('history.title') }}</h1>

    <!-- Budget Selector -->
    <n-select
      v-model:value="selectedBudgetId"
      :options="budgetOptions"
      placeholder="Select a budget"
      :style="{ width: isMobile ? '100%' : '300px' }"
      @update:value="loadTransactions"
    />

    <!-- Date Range Filter -->
    <n-space :vertical="isMobile" align="center" v-if="selectedBudgetId">
      <span>{{ t('common.period') }} :</span>
      <n-date-picker
        v-model:value="startDate"
        type="date"
        :style="{ width: isMobile ? '100%' : '160px' }"
        :placeholder="t('common.startDate')"
        clearable
      />
      <span>{{ t('common.to').toLowerCase() }}</span>
      <n-date-picker
        v-model:value="endDate"
        type="date"
        :style="{ width: isMobile ? '100%' : '160px' }"
        :placeholder="t('common.endDate')"
        clearable
      />
    </n-space>

    <!-- Category / Subcategory Filter -->
    <n-space :vertical="isMobile" align="center" v-if="selectedBudgetId">
      <n-select
        v-model:value="filterCategoryId"
        :options="filterCategoryOptions"
        :placeholder="t('history.filterByCategory')"
        :style="{ width: isMobile ? '100%' : '220px' }"
        clearable
        @update:value="handleFilterCategoryChange"
      />
      <n-select
        v-if="filterSubcategoryOptions.length > 0"
        v-model:value="filterSubcategoryId"
        :options="filterSubcategoryOptions"
        :placeholder="t('history.filterBySubcategory')"
        :style="{ width: isMobile ? '100%' : '220px' }"
        clearable
      />
    </n-space>

    <!-- Loading State -->
    <div v-if="budgetStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <template v-else-if="selectedBudgetId">
      <!-- Summary Statistics -->
      <n-card size="small">
        <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
          <n-gi>
            <n-statistic :label="t('transaction.transactions')" :value="filteredTransactions.length" />
          </n-gi>
          <n-gi>
            <n-statistic :label="t('budget.totalIncome')" :value="totalIncome.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic :label="t('budget.totalExpenses')" :value="totalExpenses.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic :label="t('budget.balance')" :value="(totalIncome - totalExpenses).toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
        </n-grid>
      </n-card>

      <!-- Mobile View: Cards -->
      <n-space v-if="isMobile && filteredTransactions.length > 0" vertical>
        <n-card
          v-for="transaction in filteredTransactions"
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
              <n-text depth="3">Category:</n-text> {{ getCategoryName(transaction.category_id) }}
            </div>
            <div>
              <n-text depth="3">Date:</n-text> {{ formatDate(transaction.date) }}
            </div>
            <div v-if="transaction.comment">
              <n-text depth="3">Comment:</n-text> {{ transaction.comment }}
            </div>
          </n-space>

          <template #footer>
            <n-space>
              <n-button size="small" type="info" @click="openEditModal(transaction)">
                Edit
              </n-button>
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
      <n-card v-else-if="!isMobile && filteredTransactions.length > 0">
        <n-data-table
          :columns="columns"
          :data="filteredTransactions"
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

    <!-- Edit Transaction Modal -->
    <n-modal
      v-model:show="showEditModal"
      preset="card"
      title="Edit Transaction"
      :style="{ width: isMobile ? '90%' : '500px' }"
    >
      <n-form>
        <n-form-item label="Title">
          <n-input v-model:value="editForm.title" placeholder="Transaction title" />
        </n-form-item>

        <n-form-item label="Type">
          <n-radio-group v-model:value="editForm.transaction_type">
            <n-radio-button value="expense">Expense</n-radio-button>
            <n-radio-button value="income">Income</n-radio-button>
          </n-radio-group>
        </n-form-item>

        <n-form-item label="Category">
          <n-select
            v-model:value="editForm.category_id"
            :options="parentCategoryOptions"
            placeholder="Select category"
            @update:value="handleCategoryChange"
          />
        </n-form-item>

        <n-form-item v-if="subcategoryOptions.length > 0" label="Subcategory">
          <n-select
            v-model:value="editForm.subcategory_id"
            :options="subcategoryOptions"
            placeholder="Select subcategory (optional)"
            clearable
          />
        </n-form-item>

        <n-form-item label="Amount">
          <n-input-number
            v-model:value="editForm.amount"
            :min="0.01"
            :precision="2"
            placeholder="0.00"
            style="width: 100%"
          >
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>

        <n-form-item label="Date">
          <n-date-picker
            v-model:value="editForm.date"
            type="date"
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="Comment">
          <n-input
            v-model:value="editForm.comment"
            type="textarea"
            placeholder="Optional comment"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showEditModal = false">Cancel</n-button>
          <n-button type="primary" @click="handleSaveEdit">Save</n-button>
        </n-space>
      </template>
    </n-modal>
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
  NSelect, NGrid, NGi, NStatistic, NSpin, NEmpty, NModal, NForm,
  NFormItem, NInput, NInputNumber, NRadioGroup, NRadioButton, NDatePicker,
  useMessage
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { DataTableColumns } from 'naive-ui'
import { useBudgetStore } from '@/stores/budget'
import type { Transaction } from '@/services/api'
import { formatDateLocal, parseDateToTimestamp } from '@/utils/date'

const message = useMessage()
const { t } = useI18n()
const budgetStore = useBudgetStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Currently selected budget ID */
const selectedBudgetId = ref<string | null>(null)

/** Date range filter */
const startDate = ref<number | null>(null)
const endDate = ref<number | null>(null)

/** Category filter */
const filterCategoryId = ref<string | null>(null)
const filterSubcategoryId = ref<string | null>(null)

/** Edit modal state */
const showEditModal = ref(false)
const editingTransaction = ref<Transaction | null>(null)
const editForm = ref({
  title: '',
  amount: 0,
  transaction_type: 'expense' as 'expense' | 'income',
  date: null as number | null,
  comment: '',
  category_id: null as string | null,
  subcategory_id: null as string | null
})

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
 * Loads transactions and categories for the selected budget.
 */
const loadTransactions = async () => {
  if (!selectedBudgetId.value) return

  try {
    await Promise.all([
      budgetStore.fetchTransactions(selectedBudgetId.value),
      budgetStore.fetchCategories(selectedBudgetId.value)
    ])
  } catch (error) {
    console.error('Error loading transactions:', error)
    message.error('Error loading data')
  }
}

/** Parent category options (categories without parent) */
const parentCategoryOptions = computed(() => {
  return budgetStore.categories
    .filter(c => !c.parent_id)
    .map(c => ({ label: c.name, value: c.id }))
})

/** Subcategory options based on selected parent category */
const subcategoryOptions = computed(() => {
  if (!editForm.value.category_id) return []
  return budgetStore.categories
    .filter(c => c.parent_id === editForm.value.category_id)
    .map(c => ({ label: c.name, value: c.id }))
})

/** Category options for the filter dropdown */
const filterCategoryOptions = computed(() => {
  return budgetStore.categories
    .filter(c => !c.parent_id)
    .map(c => ({ label: c.name, value: c.id }))
})

/** Subcategory options for the filter dropdown based on selected filter category */
const filterSubcategoryOptions = computed(() => {
  if (!filterCategoryId.value) return []
  return budgetStore.categories
    .filter(c => c.parent_id === filterCategoryId.value)
    .map(c => ({ label: c.name, value: c.id }))
})

/** Reset subcategory filter when parent category filter changes */
const handleFilterCategoryChange = () => {
  filterSubcategoryId.value = null
}

/** Get category name by ID */
const getCategoryName = (categoryId: string): string => {
  const category = budgetStore.categories.find(c => c.id === categoryId)
  if (!category) return ''

  if (category.parent_id) {
    const parent = budgetStore.categories.find(c => c.id === category.parent_id)
    return parent ? `${parent.name} > ${category.name}` : category.name
  }
  return category.name
}

/** Transactions filtered by date range and category */
const filteredTransactions = computed(() => {
  let transactions = budgetStore.transactions

  // Filter by date range
  if (startDate.value && endDate.value) {
    const start = new Date(startDate.value)
    start.setHours(0, 0, 0, 0)
    const end = new Date(endDate.value)
    end.setHours(23, 59, 59, 999)

    transactions = transactions.filter(t => {
      const transactionDate = new Date(t.date)
      return transactionDate >= start && transactionDate <= end
    })
  }

  // Filter by category / subcategory
  if (filterSubcategoryId.value) {
    transactions = transactions.filter(t => t.category_id === filterSubcategoryId.value)
  } else if (filterCategoryId.value) {
    const subcategoryIds = budgetStore.categories
      .filter(c => c.parent_id === filterCategoryId.value)
      .map(c => c.id)
    transactions = transactions.filter(t =>
      t.category_id === filterCategoryId.value || subcategoryIds.includes(t.category_id)
    )
  }

  return transactions
})

/** Total income amount */
const totalIncome = computed(() => {
  return filteredTransactions.value
    .filter(t => t.transaction_type === 'income')
    .reduce((sum, t) => sum + t.amount, 0)
})

/** Total expenses amount */
const totalExpenses = computed(() => {
  return filteredTransactions.value
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

/**
 * Opens the edit modal for a transaction.
 * @param transaction - Transaction to edit
 */
const openEditModal = (transaction: Transaction) => {
  editingTransaction.value = transaction

  // Find if the category is a subcategory
  const category = budgetStore.categories.find(c => c.id === transaction.category_id)
  let parentCategoryId = transaction.category_id
  let subcategoryId: string | null = null

  if (category?.parent_id) {
    // It's a subcategory
    parentCategoryId = category.parent_id
    subcategoryId = transaction.category_id
  }

  editForm.value = {
    title: transaction.title,
    amount: transaction.amount,
    transaction_type: transaction.transaction_type as 'expense' | 'income',
    date: parseDateToTimestamp(transaction.date),
    comment: transaction.comment || '',
    category_id: parentCategoryId,
    subcategory_id: subcategoryId
  }
  showEditModal.value = true
}

/**
 * Saves the edited transaction.
 */
const handleSaveEdit = async () => {
  if (!editingTransaction.value || !editForm.value.date || !editForm.value.category_id) return

  try {
    const dateStr = formatDateLocal(editForm.value.date)
    // Use subcategory if selected, otherwise use parent category
    const categoryId = editForm.value.subcategory_id || editForm.value.category_id

    await budgetStore.updateTransaction(editingTransaction.value.id, {
      title: editForm.value.title,
      amount: editForm.value.amount,
      transaction_type: editForm.value.transaction_type,
      date: dateStr,
      comment: editForm.value.comment || undefined,
      category_id: categoryId
    })
    message.success('Transaction updated')
    showEditModal.value = false
    editingTransaction.value = null
  } catch (error) {
    console.error('Error updating transaction:', error)
    message.error('Error updating')
  }
}

/** Reset subcategory when parent category changes */
const handleCategoryChange = () => {
  editForm.value.subcategory_id = null
}

/** Table pagination configuration */
const pagination = {
  pageSize: 20,
}

/** Table columns definition */
const columns = computed<DataTableColumns<Transaction>>(() => [
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
    title: 'Category',
    key: 'category_id',
    render: (row) => getCategoryName(row.category_id),
    ellipsis: {
      tooltip: true,
    },
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
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'info',
            onClick: () => openEditModal(row),
          }, { default: () => 'Edit' }),
          h(NPopconfirm, {
            onPositiveClick: () => handleDelete(row.id),
          }, {
            default: () => 'Delete this transaction?',
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error',
            }, { default: () => 'Delete' }),
          }),
        ],
      })
    },
  },
])
</script>