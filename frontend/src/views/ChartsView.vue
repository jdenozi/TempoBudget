<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Charts View

  Data visualization dashboard displaying budget analytics including:
  - Expense distribution by category (pie chart)
  - Income distribution (doughnut chart)
  - Monthly evolution (bar chart)
  - Budget vs actual comparison (bar chart)
-->

<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('charts.title') }}</h1>

    <!-- Filters -->
    <n-card :title="t('common.filter')" size="small">
      <n-space :vertical="isMobile" :size="isMobile ? 12 : 16">
        <n-select
          v-model:value="selectedBudget"
          :options="budgetOptions"
          :placeholder="t('budget.selectBudget')"
          :style="{ width: isMobile ? '100%' : '200px' }"
          size="small"
        />

        <n-date-picker
          v-model:value="selectedMonth"
          type="month"
          :style="{ width: isMobile ? '100%' : '200px' }"
          size="small"
        />

        <n-select
          v-model:value="selectedCategories"
          :options="categoryOptions"
          :placeholder="t('charts.filterByCategory')"
          :style="{ width: isMobile ? '100%' : '300px' }"
          size="small"
          multiple
          clearable
        />

        <n-switch v-model:value="includeExceptional">
          <template #checked>{{ t('charts.includeExceptional') }}</template>
          <template #unchecked>{{ t('charts.includeExceptional') }}</template>
        </n-switch>
      </n-space>
    </n-card>

    <!-- Charts Grid -->
    <n-grid :cols="isMobile ? 1 : 2" :x-gap="16" :y-gap="16">
      <!-- Expense Distribution by Category -->
      <n-gi>
        <n-card :title="t('charts.expensesByCategory')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Pie :data="pieChartData" :options="pieChartOptions" />
          </div>
        </n-card>
      </n-gi>

      <!-- Income Distribution -->
      <n-gi>
        <n-card :title="t('charts.incomeVsExpenses')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Doughnut :data="doughnutChartData" :options="doughnutChartOptions" />
          </div>
        </n-card>
      </n-gi>

      <!-- Monthly Evolution -->
      <n-gi :span="isMobile ? 1 : 2">
        <n-card :title="t('charts.monthlyTrend')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Bar :data="barChartData" :options="barChartOptions" />
          </div>
        </n-card>
      </n-gi>

      <!-- Budget vs Actual by Category -->
      <n-gi :span="isMobile ? 1 : 2">
        <n-card :title="budgetVsActualTitle">
          <div :style="{ height: isMobile ? '300px' : '350px', position: 'relative' }">
            <Bar :data="comparisonChartData" :options="comparisonChartOptions" />
          </div>
        </n-card>
      </n-gi>

      <!-- Category Monthly Trend -->
      <n-gi :span="isMobile ? 1 : 2">
        <n-card :title="t('charts.categoryMonthlyTrend')">
          <div :style="{ height: isMobile ? '300px' : '350px', position: 'relative' }">
            <Bar :data="categoryTrendChartData" :options="categoryTrendChartOptions" />
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup lang="ts">
/**
 * Charts view component for budget analytics visualization.
 *
 * Features:
 * - Budget and month filtering
 * - Pie chart for expense distribution
 * - Doughnut chart for income sources
 * - Bar chart for monthly evolution
 * - Bar chart for budget vs actual comparison
 */

import { ref, computed, onMounted, watch } from 'vue'
import { NSpace, NCard, NSelect, NDatePicker, NGrid, NGi, NSwitch } from 'naive-ui'
import { Pie, Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { useI18n } from 'vue-i18n'
import { useBudgetStore } from '@/stores/budget'
import { useMobileDetect } from '@/composables/useMobileDetect'
import { CHART_COLORS, INCOME_COLORS, usePieChartOptions, useBarChartOptions } from '@/composables/useChartOptions'

// Register Chart.js components
ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

const { t, locale } = useI18n()
const budgetStore = useBudgetStore()
const { isMobile } = useMobileDetect()

/** Selected budget ID */
const selectedBudget = ref<string | null>(null)

/** Selected month timestamp */
const selectedMonth = ref(Date.now())

/** Category filter */
const selectedCategories = ref<string[]>([])

/** Include exceptional (non-budgeted) transactions */
const includeExceptional = ref(true)

/** Budget vs Actual title */
const budgetVsActualTitle = computed(() => `${t('budget.title')} vs ${t('budget.spent')}`)

onMounted(async () => {
  await budgetStore.fetchBudgets()
  if (budgetStore.budgets.length > 0) {
    selectedBudget.value = budgetStore.budgets[0].id
  }
})

// Watch budget selection and load data
watch(selectedBudget, async (budgetId) => {
  if (budgetId) {
    await Promise.all([
      budgetStore.fetchCategories(budgetId),
      budgetStore.fetchTransactions(budgetId)
    ])
  }
}, { immediate: true })

/** Budget options for the selector */
const budgetOptions = computed(() =>
  budgetStore.budgets.map(b => ({ label: b.name, value: b.id }))
)

/** Category options for multi-select filter */
const categoryOptions = computed(() =>
  budgetStore.categories
    .filter(c => !c.parent_id)
    .map(c => ({ label: c.name, value: c.id }))
)

/** Selected month as Date */
const selectedMonthDate = computed(() => new Date(selectedMonth.value))

/** Filter transactions by selected month, categories, and exceptional toggle */
const filteredTransactions = computed(() => {
  const month = selectedMonthDate.value.getMonth()
  const year = selectedMonthDate.value.getFullYear()

  let transactions = budgetStore.transactions.filter(t => {
    const date = new Date(t.date)
    return date.getMonth() === month && date.getFullYear() === year
  })

  // Filter by categories (if any selected)
  if (selectedCategories.value.length > 0) {
    const subcategoryIds = budgetStore.categories
      .filter(c => c.parent_id && selectedCategories.value.includes(c.parent_id))
      .map(c => c.id)
    const allIds = [...selectedCategories.value, ...subcategoryIds]
    transactions = transactions.filter(t => allIds.includes(t.category_id))
  }

  // Exclude exceptional if toggle is off
  if (!includeExceptional.value) {
    transactions = transactions.filter(t => t.is_budgeted === 1)
  }

  return transactions
})

/** Expenses by category for the selected month */
const expensesByCategory = computed(() => {
  const expenses: Record<string, number> = {}
  filteredTransactions.value
    .filter(t => t.transaction_type === 'expense')
    .forEach(t => {
      const category = budgetStore.categories.find(c => c.id === t.category_id)
      const name = category?.name || 'Other'
      expenses[name] = (expenses[name] || 0) + t.amount
    })
  return expenses
})

/** Income by category for the selected month */
const incomeByCategory = computed(() => {
  const income: Record<string, number> = {}
  filteredTransactions.value
    .filter(t => t.transaction_type === 'income')
    .forEach(t => {
      const category = budgetStore.categories.find(c => c.id === t.category_id)
      const name = category?.name || 'Other'
      income[name] = (income[name] || 0) + t.amount
    })
  return income
})

/** Monthly data for the last 6 months */
const monthlyData = computed(() => {
  const months: { month: string; income: number; expenses: number }[] = []
  const now = new Date(selectedMonth.value)
  const localeStr = locale.value === 'fr' ? 'fr-FR' : 'en-US'

  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const monthName = date.toLocaleString(localeStr, { month: 'long' })
    const monthNum = date.getMonth()
    const yearNum = date.getFullYear()

    const monthTransactions = budgetStore.transactions.filter(t => {
      const tDate = new Date(t.date)
      return tDate.getMonth() === monthNum && tDate.getFullYear() === yearNum
    })

    const income = monthTransactions
      .filter(t => t.transaction_type === 'income')
      .reduce((sum, t) => sum + t.amount, 0)
    const expenses = monthTransactions
      .filter(t => t.transaction_type === 'expense')
      .reduce((sum, t) => sum + t.amount, 0)

    months.push({ month: monthName, income, expenses })
  }
  return months
})

/** Budget vs Actual comparison data */
const budgetVsActual = computed(() => {
  const categories = budgetStore.categories.map(c => c.name)
  const budget = budgetStore.categories.map(c => c.amount)
  const actual = budgetStore.categories.map(c => {
    return filteredTransactions.value
      .filter(t => t.category_id === c.id && t.transaction_type === 'expense')
      .reduce((sum, t) => sum + t.amount, 0)
  })
  return { categories, budget, actual }
})

/** Color palette for charts */
const colors = CHART_COLORS

/** Pie chart data for expense distribution */
const pieChartData = computed(() => ({
  labels: Object.keys(expensesByCategory.value),
  datasets: [{
    data: Object.values(expensesByCategory.value),
    backgroundColor: colors,
    borderWidth: 2,
    borderColor: '#fff'
  }]
}))

/** Pie chart options */
const pieChartOptions = usePieChartOptions(isMobile)

/** Doughnut chart data for income distribution */
const doughnutChartData = computed(() => ({
  labels: Object.keys(incomeByCategory.value),
  datasets: [{
    data: Object.values(incomeByCategory.value),
    backgroundColor: INCOME_COLORS,
    borderWidth: 2,
    borderColor: '#fff'
  }]
}))

/** Doughnut chart options */
const doughnutChartOptions = usePieChartOptions(isMobile, { showPercentage: false })

/** Bar chart data for monthly evolution */
const barChartData = computed(() => ({
  labels: monthlyData.value.map(d => d.month),
  datasets: [
    {
      label: t('budget.income'),
      data: monthlyData.value.map(d => d.income),
      backgroundColor: '#18a058',
      borderRadius: 4
    },
    {
      label: t('budget.expenses'),
      data: monthlyData.value.map(d => d.expenses),
      backgroundColor: '#d03050',
      borderRadius: 4
    }
  ]
}))

/** Bar chart options for monthly evolution */
const barChartOptions = useBarChartOptions(isMobile)

/** Comparison chart data for budget vs actual */
const comparisonChartData = computed(() => ({
  labels: budgetVsActual.value.categories,
  datasets: [
    {
      label: t('budget.title'),
      data: budgetVsActual.value.budget,
      backgroundColor: '#5470c6',
      borderRadius: 4
    },
    {
      label: t('budget.spent'),
      data: budgetVsActual.value.actual,
      backgroundColor: '#91cc75',
      borderRadius: 4
    }
  ]
}))

/** Comparison chart options */
const comparisonChartOptions = useBarChartOptions(isMobile, { rotateLabels: true })

/** Category monthly trend data — last 6 months, per selected or top 5 categories */
const categoryTrendData = computed(() => {
  const now = new Date(selectedMonth.value)
  const localeStr = locale.value === 'fr' ? 'fr-FR' : 'en-US'

  // Build 6-month labels
  const monthLabels: string[] = []
  const monthKeys: { month: number; year: number }[] = []
  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
    monthLabels.push(date.toLocaleString(localeStr, { month: 'long' }))
    monthKeys.push({ month: date.getMonth(), year: date.getFullYear() })
  }

  // Determine which categories to show
  let targetCategoryIds: string[]
  if (selectedCategories.value.length > 0) {
    targetCategoryIds = [...selectedCategories.value]
  } else {
    // Top 5 by total expense amount across all 6 months
    const totals: Record<string, number> = {}
    const parentCategories = budgetStore.categories.filter(c => !c.parent_id)
    for (const cat of parentCategories) {
      const subcatIds = budgetStore.categories
        .filter(c => c.parent_id === cat.id)
        .map(c => c.id)
      const allIds = [cat.id, ...subcatIds]
      totals[cat.id] = budgetStore.transactions
        .filter(t => {
          if (t.transaction_type !== 'expense') return false
          if (!includeExceptional.value && t.is_budgeted !== 1) return false
          const d = new Date(t.date)
          return monthKeys.some(mk => mk.month === d.getMonth() && mk.year === d.getFullYear())
            && allIds.includes(t.category_id)
        })
        .reduce((sum, t) => sum + t.amount, 0)
    }
    targetCategoryIds = Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .filter(([, v]) => v > 0)
      .map(([id]) => id)
  }

  // Build datasets
  const datasets = targetCategoryIds.map((catId, idx) => {
    const cat = budgetStore.categories.find(c => c.id === catId)
    const subcatIds = budgetStore.categories
      .filter(c => c.parent_id === catId)
      .map(c => c.id)
    const allIds = [catId, ...subcatIds]

    const data = monthKeys.map(mk => {
      return budgetStore.transactions
        .filter(t => {
          if (t.transaction_type !== 'expense') return false
          if (!includeExceptional.value && t.is_budgeted !== 1) return false
          const d = new Date(t.date)
          return d.getMonth() === mk.month && d.getFullYear() === mk.year
            && allIds.includes(t.category_id)
        })
        .reduce((sum, t) => sum + t.amount, 0)
    })

    return {
      label: cat?.name || 'Other',
      data,
      backgroundColor: colors[idx % colors.length],
      borderRadius: 4,
    }
  })

  return { labels: monthLabels, datasets }
})

/** Category trend chart data */
const categoryTrendChartData = computed(() => ({
  labels: categoryTrendData.value.labels,
  datasets: categoryTrendData.value.datasets,
}))

/** Category trend chart options */
const categoryTrendChartOptions = useBarChartOptions(isMobile)
</script>
