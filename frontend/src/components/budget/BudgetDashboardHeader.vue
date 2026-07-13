<template>
  <n-card class="dashboard-header">
    <!-- Main Dashboard Grid -->
    <div class="dashboard-grid" :class="{ mobile: isMobile }">
      <!-- KPI: Revenus -->
      <div class="kpi-card income">
        <div class="kpi-icon">📥</div>
        <div class="kpi-content">
          <div class="kpi-label">{{ t('budget.income') }}</div>
          <div class="kpi-value">{{ formatCurrency(totalIncome) }}</div>
          <div class="kpi-sub">
            <span>{{ t('budget.received') }}:</span>
            <span class="kpi-sub-value">{{ formatCurrency(totalIncomeReceived) }}</span>
          </div>
          <div class="kpi-progress">
            <div
              class="kpi-progress-bar income-bar"
              :style="{ width: incomeReceivedPercent + '%' }"
            ></div>
          </div>
          <div class="kpi-percent">{{ incomeReceivedPercent.toFixed(0) }}% {{ t('budget.received').toLowerCase() }}</div>
        </div>
      </div>

      <!-- KPI: Dépenses -->
      <div class="kpi-card expenses">
        <div class="kpi-icon">📤</div>
        <div class="kpi-content">
          <div class="kpi-label">{{ t('budget.expenses') }}</div>
          <div class="kpi-value">{{ formatCurrency(totalBudget) }}</div>
          <div class="kpi-sub">
            <span>{{ t('budget.spent') }}:</span>
            <span class="kpi-sub-value">{{ formatCurrency(totalSpent) }}</span>
          </div>
          <div class="kpi-progress">
            <div
              class="kpi-progress-bar"
              :style="{ width: Math.min(percentage, 100) + '%', background: getProgressColor(percentage) }"
            ></div>
          </div>
          <div class="kpi-percent">{{ percentage.toFixed(0) }}% {{ t('budget.percentage').toLowerCase() }}</div>
        </div>
      </div>

      <!-- KPI: Restant -->
      <div class="kpi-card remaining" :class="{ negative: remaining < 0 }">
        <div class="kpi-icon">{{ remaining >= 0 ? '💰' : '⚠️' }}</div>
        <div class="kpi-content">
          <div class="kpi-label">{{ t('budget.remaining') }}</div>
          <div class="kpi-value" :class="{ negative: remaining < 0 }">{{ formatCurrency(remaining) }}</div>
          <div class="kpi-sub">
            <span>vs {{ t('budget.income') }}:</span>
            <span class="kpi-sub-value" :class="{ negative: remainingFromIncome < 0 }">{{ formatCurrency(remainingFromIncome) }}</span>
          </div>
          <div class="remaining-bar-container">
            <div class="remaining-bar">
              <div
                class="remaining-bar-fill"
                :style="{ width: remainingPercent + '%', background: remaining >= 0 ? '#22c55e' : '#dc2626' }"
              ></div>
            </div>
          </div>
          <div class="kpi-percent">{{ remainingPercent.toFixed(0) }}% {{ t('budget.remaining').toLowerCase() }}</div>
        </div>
      </div>

      <!-- Donut Chart -->
      <div class="donut-container">
        <div class="donut-chart-wrapper">
          <Doughnut
            v-if="hasChartData"
            :data="chartData"
            :options="chartOptions"
          />
          <div v-else class="no-chart-data">
            <span>{{ t('budget.noData') }}</span>
          </div>
          <div class="donut-center">
            <span class="donut-percent" :style="{ color: getProgressColor(percentage) }">
              {{ percentage.toFixed(0) }}%
            </span>
            <span class="donut-label">{{ t('budget.used') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Global Progress Bar -->
    <div class="global-progress-section">
      <div class="progress-header">
        <span class="progress-label">{{ t('budget.budgetProgress') }}</span>
        <span class="progress-values">
          {{ formatCurrency(totalSpent) }} / {{ formatCurrency(totalBudget) }}
        </span>
      </div>
      <div class="global-progress-bar">
        <div
          class="global-progress-fill"
          :class="{ 'pulse-animation': percentage > 100 }"
          :style="{
            width: Math.min(percentage, 100) + '%',
            background: getProgressGradient(percentage)
          }"
        ></div>
        <!-- Projected marker -->
        <div
          v-if="projectedPercentage > percentage && projectedPercentage <= 100"
          class="projected-marker"
          :style="{ left: projectedPercentage + '%' }"
        >
          <div class="projected-line"></div>
          <span class="projected-label">{{ projectedPercentage.toFixed(0) }}%</span>
        </div>
      </div>
      <div class="progress-legend">
        <span class="legend-item">
          <span class="legend-dot spent"></span>
          {{ t('budget.spent') }}
        </span>
        <span v-if="projectedPercentage > percentage" class="legend-item">
          <span class="legend-dot projected"></span>
          {{ t('budget.projected') }}
        </span>
      </div>
    </div>

    <!-- Balance Row -->
    <div class="balance-row" :class="{ negative: balance < 0 }">
      <span>{{ t('budget.balance') }} ({{ t('budget.income') }} - {{ t('budget.title') }}):</span>
      <span class="balance-value">{{ balance >= 0 ? '+' : '' }}{{ formatCurrency(balance) }}</span>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { CHART_COLORS } from '@/composables/useChartOptions'

ChartJS.register(ArcElement, Tooltip, Legend)

const { t } = useI18n()

interface CategoryData {
  name: string
  amount: number
  spent: number
  color?: string
}

interface Props {
  totalIncome: number
  totalIncomeReceived: number
  totalBudget: number
  totalSpent: number
  remaining: number
  remainingFromIncome: number
  percentage: number
  projectedPercentage: number
  balance: number
  categoriesData: CategoryData[]
  isMobile: boolean
}

const props = defineProps<Props>()

// Computed
const incomeReceivedPercent = computed(() =>
  props.totalIncome > 0 ? (props.totalIncomeReceived / props.totalIncome) * 100 : 0
)

const remainingPercent = computed(() =>
  props.totalBudget > 0 ? Math.max(0, (props.remaining / props.totalBudget) * 100) : 100
)

// Chart configuration
const chartData = computed(() => {
  const filteredCategories = props.categoriesData.filter(c => c.amount > 0)
  return {
    labels: filteredCategories.map(c => c.name),
    datasets: [{
      data: filteredCategories.map(c => c.spent),
      backgroundColor: filteredCategories.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
      borderWidth: 0,
      hoverOffset: 4
    }]
  }
})

const hasChartData = computed(() => {
  const datasets = chartData.value.datasets
  return datasets.length > 0 && datasets[0] && datasets[0].data.length > 0
})

// Helper functions
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

const getProgressColor = (pct: number) => {
  if (pct <= 70) return '#22c55e'      // vert
  if (pct <= 90) return '#f59e0b'      // orange
  if (pct <= 100) return '#ef4444'     // rouge
  return '#dc2626'                      // rouge foncé
}

const getProgressGradient = (pct: number) => {
  if (pct <= 70) return 'linear-gradient(90deg, #22c55e, #4ade80)'
  if (pct <= 90) return 'linear-gradient(90deg, #f59e0b, #fbbf24)'
  if (pct <= 100) return 'linear-gradient(90deg, #ef4444, #f87171)'
  return 'linear-gradient(90deg, #dc2626, #ef4444)'
}

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
          return `${context.label}: ${formatCurrency(value)} (${percentage}%)`
        }
      }
    }
  }
}))
</script>

<style scoped>
.dashboard-header {
  margin-bottom: 16px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr) 200px;
  gap: 16px;
  margin-bottom: 20px;
}

.dashboard-grid.mobile {
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.dashboard-grid.mobile .donut-container {
  grid-column: span 2;
  order: 4;
}

/* KPI Cards */
.kpi-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid #888;
  display: flex;
  gap: 12px;
}

.kpi-card.income {
  border-left-color: #22c55e;
}

.kpi-card.expenses {
  border-left-color: #ef4444;
}

.kpi-card.remaining {
  border-left-color: #3b82f6;
}

.kpi-card.remaining.negative {
  border-left-color: #dc2626;
}

.kpi-icon {
  font-size: 24px;
  opacity: 0.9;
}

.kpi-content {
  flex: 1;
  min-width: 0;
}

.kpi-label {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 22px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.2;
}

.kpi-value.negative {
  color: #ef4444;
}

.kpi-sub {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
  margin-top: 8px;
}

.kpi-sub-value {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.kpi-sub-value.negative {
  color: #ef4444;
}

.kpi-progress {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.kpi-progress-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.kpi-progress-bar.income-bar {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.kpi-percent {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
}

/* Remaining bar */
.remaining-bar-container {
  margin-top: 8px;
}

.remaining-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.remaining-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

/* Donut Chart */
.donut-container {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;
}

.donut-chart-wrapper {
  position: relative;
  width: 140px;
  height: 140px;
}

.dashboard-grid.mobile .donut-chart-wrapper {
  width: 160px;
  height: 160px;
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.donut-percent {
  font-size: 24px;
  font-weight: 700;
  display: block;
}

.donut-label {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
}

.no-chart-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-size: 12px;
}

/* Global Progress Bar */
.global-progress-section {
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.progress-values {
  font-size: 13px;
  color: #888;
}

.global-progress-bar {
  position: relative;
  height: 12px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: visible;
}

.global-progress-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease, background 0.3s ease;
}

.pulse-animation {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.projected-marker {
  position: absolute;
  top: -4px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.projected-line {
  width: 2px;
  height: 20px;
  background: #f59e0b;
  border-radius: 1px;
}

.projected-marker .projected-label {
  font-size: 10px;
  color: #f59e0b;
  margin-top: 2px;
}

.progress-legend {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #888;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.spent {
  background: #22c55e;
}

.legend-dot.projected {
  background: #f59e0b;
}

/* Balance Row */
.balance-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(34, 197, 94, 0.3);
  font-size: 14px;
}

.balance-row.negative {
  background: rgba(220, 38, 38, 0.1);
  border-color: rgba(220, 38, 38, 0.3);
}

.balance-value {
  font-size: 18px;
  font-weight: 700;
  color: #22c55e;
}

.balance-row.negative .balance-value {
  color: #dc2626;
}

/* Mobile adjustments */
@media (max-width: 768px) {
  .kpi-icon {
    font-size: 20px;
  }

  .kpi-value {
    font-size: 18px;
  }

  .kpi-card {
    padding: 12px;
  }

  .donut-percent {
    font-size: 20px;
  }
}
</style>
