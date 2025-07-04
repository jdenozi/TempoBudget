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
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">Charts</h1>

    <!-- Filters -->
    <n-card title="Filters" size="small">
      <n-space :vertical="isMobile" :size="isMobile ? 12 : 16">
        <n-select
          v-model:value="selectedBudget"
          :options="budgetOptions"
          placeholder="Select a budget"
          :style="{ width: isMobile ? '100%' : '200px' }"
          size="small"
        />

        <n-date-picker
          v-model:value="selectedMonth"
          type="month"
          :style="{ width: isMobile ? '100%' : '200px' }"
          size="small"
        />
      </n-space>
    </n-card>

    <!-- Charts Grid -->
    <n-grid :cols="isMobile ? 1 : 2" :x-gap="16" :y-gap="16">
      <!-- Expense Distribution by Category -->
      <n-gi>
        <n-card title="Expense Distribution">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Pie :data="pieChartData" :options="pieChartOptions" />
          </div>
        </n-card>
      </n-gi>

      <!-- Income Distribution -->
      <n-gi>
        <n-card title="Income Distribution">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Doughnut :data="doughnutChartData" :options="doughnutChartOptions" />
          </div>
        </n-card>
      </n-gi>

      <!-- Monthly Evolution -->
      <n-gi :span="isMobile ? 1 : 2">
        <n-card title="Last 6 Months Evolution">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Bar :data="barChartData" :options="barChartOptions" />
          </div>
        </n-card>
      </n-gi>

      <!-- Budget vs Actual by Category -->
      <n-gi :span="isMobile ? 1 : 2">
        <n-card title="Budget vs Actual">
          <div :style="{ height: isMobile ? '300px' : '350px', position: 'relative' }">
            <Bar :data="comparisonChartData" :options="comparisonChartOptions" />
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

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { NSpace, NCard, NSelect, NDatePicker, NGrid, NGi } from 'naive-ui'
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
import { useBudgetStore } from '@/stores/budget'

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

const budgetStore = useBudgetStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Selected budget ID */
const selectedBudget = ref<string | null>(null)

/** Selected month timestamp */
const selectedMonth = ref(Date.now())

/**
 * Checks if the viewport is mobile-sized.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  await budgetStore.fetchBudgets()
  if (budgetStore.budgets.length > 0) {
    selectedBudget.value = budgetStore.budgets[0].id
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
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

/** Selected month as Date */
const selectedMonthDate = computed(() => new Date(selectedMonth.value))

/** Filter transactions by selected month */
const filteredTransactions = computed(() => {
  const month = selectedMonthDate.value.getMonth()
  const year = selectedMonthDate.value.getFullYear()
  return budgetStore.transactions.filter(t => {
    const date = new Date(t.date)
    return date.getMonth() === month && date.getFullYear() === year
  })
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

  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const monthName = date.toLocaleString('en-US', { month: 'long' })
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
const colors = [
  '#5470c6',
  '#91cc75',
  '#fac858',
  '#ee6666',
  '#73c0de',
  '#3ba272',
  '#fc8452',
  '#9a60b4',
  '#ea7ccc'
]

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
const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: isMobile.value ? 'bottom' : 'right',
      labels: {
        boxWidth: 15,
        padding: 10,
        font: {
          size: isMobile.value ? 10 : 12
        }
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const label = context.label || ''
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const percentage = ((value / total) * 100).toFixed(1)
          return `${label}: ${value.toFixed(2)} € (${percentage}%)`
        }
      }
    }
  }
}

/** Doughnut chart data for income distribution */
const doughnutChartData = computed(() => ({
  labels: Object.keys(incomeByCategory.value),
  datasets: [{
    data: Object.values(incomeByCategory.value),
    backgroundColor: ['#18a058', '#91cc75', '#73c0de', '#fac858', '#ee6666'],
    borderWidth: 2,
    borderColor: '#fff'
  }]
}))

/** Doughnut chart options */
const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: isMobile.value ? 'bottom' : 'right',
      labels: {
        boxWidth: 15,
        padding: 10,
        font: {
          size: isMobile.value ? 10 : 12
        }
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const label = context.label || ''
          const value = context.parsed || 0
          return `${label}: ${value.toFixed(2)} €`
        }
      }
    }
  }
}

/** Bar chart data for monthly evolution */
const barChartData = computed(() => ({
  labels: monthlyData.value.map(d => d.month),
  datasets: [
    {
      label: 'Income',
      data: monthlyData.value.map(d => d.income),
      backgroundColor: '#18a058',
      borderRadius: 4
    },
    {
      label: 'Expenses',
      data: monthlyData.value.map(d => d.expenses),
      backgroundColor: '#d03050',
      borderRadius: 4
    }
  ]
}))

/** Bar chart options for monthly evolution */
const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        font: {
          size: isMobile.value ? 10 : 12
        }
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const label = context.dataset.label || ''
          const value = context.parsed.y || 0
          return `${label}: ${value.toFixed(2)} €`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: any) => `${value} €`,
        font: {
          size: isMobile.value ? 9 : 11
        }
      }
    },
    x: {
      ticks: {
        font: {
          size: isMobile.value ? 9 : 11
        }
      }
    }
  }
}

/** Comparison chart data for budget vs actual */
const comparisonChartData = computed(() => ({
  labels: budgetVsActual.value.categories,
  datasets: [
    {
      label: 'Planned Budget',
      data: budgetVsActual.value.budget,
      backgroundColor: '#5470c6',
      borderRadius: 4
    },
    {
      label: 'Actual',
      data: budgetVsActual.value.actual,
      backgroundColor: '#91cc75',
      borderRadius: 4
    }
  ]
}))

/** Comparison chart options */
const comparisonChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        font: {
          size: isMobile.value ? 10 : 12
        }
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const label = context.dataset.label || ''
          const value = context.parsed.y || 0
          return `${label}: ${value.toFixed(2)} €`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: any) => `${value} €`,
        font: {
          size: isMobile.value ? 9 : 11
        }
      }
    },
    x: {
      ticks: {
        font: {
          size: isMobile.value ? 9 : 11
        },
        maxRotation: isMobile.value ? 45 : 0,
        minRotation: isMobile.value ? 45 : 0
      }
    }
  }
}
</script>