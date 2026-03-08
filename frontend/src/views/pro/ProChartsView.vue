<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.charts.title') }}</h1>

    <!-- Filters -->
    <n-card :title="t('common.filter')" size="small">
      <n-date-picker
        v-model:value="selectedMonth"
        type="month"
        :style="{ width: isMobile ? '100%' : '200px' }"
        size="small"
      />
    </n-card>

    <!-- Charts Grid -->
    <n-grid :cols="isMobile ? 1 : 2" :x-gap="16" :y-gap="16">
      <!-- CA Evolution (12 months) -->
      <n-gi :span="isMobile ? 1 : 2">
        <n-card :title="t('pro.charts.caEvolution')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Bar :data="caEvolutionData" :options="barChartOpts" />
          </div>
        </n-card>
      </n-gi>

      <!-- Expenses by Category -->
      <n-gi>
        <n-card :title="t('pro.charts.expensesByCategory')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Pie :data="expensesByCategoryData" :options="pieChartOpts" />
          </div>
        </n-card>
      </n-gi>

      <!-- CA by Client -->
      <n-gi>
        <n-card :title="t('pro.charts.caByClient')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Doughnut :data="caByClientData" :options="doughnutChartOpts" />
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NSpace, NCard, NDatePicker, NGrid, NGi } from 'naive-ui'
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
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import { CHART_COLORS, INCOME_COLORS, usePieChartOptions, useBarChartOptions } from '@/composables/useChartOptions'

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const { t, locale } = useI18n()
const proStore = useProStore()
const { isMobile } = useMobileDetect()

const selectedMonth = ref(Date.now())

const pieChartOpts = usePieChartOptions(isMobile)
const doughnutChartOpts = usePieChartOptions(isMobile, { showPercentage: false })
const barChartOpts = useBarChartOptions(isMobile)

onMounted(async () => {
  await proStore.fetchTransactions()
  await proStore.fetchClients()
  await proStore.fetchCategories()
})

/** Monthly CA data for the last 12 months */
const monthlyData = computed(() => {
  const months: { month: string; income: number; expenses: number }[] = []
  const now = new Date(selectedMonth.value)
  const localeStr = locale.value === 'fr' ? 'fr-FR' : 'en-US'

  for (let i = 11; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const monthName = date.toLocaleString(localeStr, { month: 'short' })
    const monthNum = date.getMonth()
    const yearNum = date.getFullYear()

    const monthTxs = proStore.proTransactions.filter(tx => {
      const d = new Date(tx.date)
      return d.getMonth() === monthNum && d.getFullYear() === yearNum
    })

    const income = monthTxs.filter(tx => tx.transaction_type === 'income').reduce((s, tx) => s + tx.amount, 0)
    const expenses = monthTxs.filter(tx => tx.transaction_type === 'expense').reduce((s, tx) => s + tx.amount, 0)

    months.push({ month: monthName, income, expenses })
  }
  return months
})

const caEvolutionData = computed(() => ({
  labels: monthlyData.value.map(d => d.month),
  datasets: [
    {
      label: t('budget.income'),
      data: monthlyData.value.map(d => d.income),
      backgroundColor: '#18a058',
      borderRadius: 4,
    },
    {
      label: t('budget.expenses'),
      data: monthlyData.value.map(d => d.expenses),
      backgroundColor: '#d03050',
      borderRadius: 4,
    },
  ],
}))

/** Expenses by pro category */
const expensesByCategoryData = computed(() => {
  const byCategory: Record<string, number> = {}
  const now = new Date(selectedMonth.value)

  proStore.proTransactions
    .filter(tx => {
      if (tx.transaction_type !== 'expense') return false
      const d = new Date(tx.date)
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })
    .forEach(tx => {
      const name = tx.category_name || 'Other'
      byCategory[name] = (byCategory[name] || 0) + tx.amount
    })

  return {
    labels: Object.keys(byCategory),
    datasets: [{
      data: Object.values(byCategory),
      backgroundColor: CHART_COLORS,
      borderWidth: 2,
      borderColor: '#fff',
    }],
  }
})

/** CA by client */
const caByClientData = computed(() => {
  const byClient: Record<string, number> = {}
  const now = new Date(selectedMonth.value)

  proStore.proTransactions
    .filter(tx => {
      if (tx.transaction_type !== 'income') return false
      const d = new Date(tx.date)
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })
    .forEach(tx => {
      const name = tx.client_name || 'Sans client'
      byClient[name] = (byClient[name] || 0) + tx.amount
    })

  return {
    labels: Object.keys(byClient),
    datasets: [{
      data: Object.values(byClient),
      backgroundColor: INCOME_COLORS,
      borderWidth: 2,
      borderColor: '#fff',
    }],
  }
})
</script>
