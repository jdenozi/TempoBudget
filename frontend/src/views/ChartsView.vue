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

import { ref, computed, onMounted, onUnmounted } from 'vue'
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

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Selected budget ID */
const selectedBudget = ref(2)

/** Selected month timestamp */
const selectedMonth = ref(Date.now())

/**
 * Checks if the viewport is mobile-sized.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

/** Budget options for the selector */
const budgetOptions = [
  { label: 'Personal Budget', value: 1 },
  { label: 'Couple Budget', value: 2 }
]

// Mock data for demonstration
const expensesByCategory = {
  'Housing': 300.00,
  'Groceries': 220.50,
  'Health': 45.00,
  'Vehicle': 203.00,
  'Leisure': 65.00,
  'Sports': 15.00,
  'Couple': 36.39,
  'Pets': 10.00
}

const incomeByCategory = {
  'Salary': 2860.00,
  'Freelance': 500.00,
  'Other': 150.00
}

const monthlyData = [
  { month: 'July', income: 3200, expenses: 2100 },
  { month: 'August', income: 3100, expenses: 2350 },
  { month: 'September', income: 3400, expenses: 2200 },
  { month: 'October', income: 3500, expenses: 2450 },
  { month: 'November', income: 3510, expenses: 2300 },
  { month: 'December', income: 3200, expenses: 1894.89 }
]

const budgetVsActual = {
  categories: ['Housing', 'Groceries', 'Health', 'Vehicle', 'Leisure', 'Sports', 'Couple', 'Pets'],
  budget: [379.53, 181.94, 80.00, 203.00, 50.00, 27.00, 36.39, 10.00],
  actual: [300.00, 220.50, 45.00, 203.00, 65.00, 15.00, 36.39, 10.00]
}

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
  labels: Object.keys(expensesByCategory),
  datasets: [{
    data: Object.values(expensesByCategory),
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
  labels: Object.keys(incomeByCategory),
  datasets: [{
    data: Object.values(incomeByCategory),
    backgroundColor: ['#18a058', '#91cc75', '#73c0de'],
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
  labels: monthlyData.map(d => d.month),
  datasets: [
    {
      label: 'Income',
      data: monthlyData.map(d => d.income),
      backgroundColor: '#18a058',
      borderRadius: 4
    },
    {
      label: 'Expenses',
      data: monthlyData.map(d => d.expenses),
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
  labels: budgetVsActual.categories,
  datasets: [
    {
      label: 'Planned Budget',
      data: budgetVsActual.budget,
      backgroundColor: '#5470c6',
      borderRadius: 4
    },
    {
      label: 'Actual',
      data: budgetVsActual.actual,
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