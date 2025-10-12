<template>
  <n-card>
    <!-- Income vs Expenses Summary -->
    <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-statistic label="Revenus" :value="totalIncome.toFixed(2)">
          <template #prefix><span style="color: #18a058;">+</span></template>
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Budget Dépenses" :value="totalBudget.toFixed(2)">
          <template #prefix><span style="color: #d03050;">-</span></template>
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Solde" :value="balance.toFixed(2)">
          <template #prefix><span :style="{ color: balance >= 0 ? '#18a058' : '#d03050' }">{{ balance >= 0 ? '+' : '' }}</span></template>
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <div style="display: flex; justify-content: center;">
          <n-progress
            type="circle"
            :percentage="Math.min(percentage, 100)"
            :color="percentage > 100 ? '#d03050' : '#18a058'"
            :style="{ width: isMobile ? '80px' : '100px' }"
          >
            {{ percentage.toFixed(2) }}%
          </n-progress>
        </div>
      </n-gi>
    </n-grid>

    <!-- Expenses Details -->
    <n-divider style="margin: 16px 0;" />
    <div style="font-size: 12px; color: #888; margin-bottom: 8px;">DÉPENSES</div>
    <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-statistic label="Dépensé" :value="totalSpent.toFixed(2)">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Restant" :value="remaining.toFixed(2)">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi :span="2"></n-gi>
    </n-grid>

    <!-- Projected Summary -->
    <n-divider style="margin: 16px 0;" />
    <div style="font-size: 12px; color: #888; margin-bottom: 8px;">PROJECTED (including recurring)</div>
    <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-statistic label="Projected Spent" :value="totalProjected.toFixed(2)">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Projected Remaining" :value="projectedRemaining.toFixed(2)">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <div style="display: flex; justify-content: center;">
          <n-progress
            type="circle"
            :percentage="Math.min(projectedPercentage, 100)"
            :color="projectedPercentage > 100 ? '#d03050' : '#f0a020'"
            :style="{ width: isMobile ? '80px' : '100px' }"
          >
            {{ projectedPercentage.toFixed(2) }}%
          </n-progress>
        </div>
      </n-gi>
      <n-gi>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="font-size: 12px; color: #888; margin-bottom: 4px;">By Tag</div>
          <div :style="{ width: isMobile ? '80px' : '100px', height: isMobile ? '80px' : '100px' }">
            <Doughnut
              v-if="tagChartData.labels.length > 0"
              :data="tagChartData"
              :options="tagChartOptions"
            />
            <div v-else style="display: flex; align-items: center; justify-content: center; height: 100%; color: #888; font-size: 11px;">
              No tags
            </div>
          </div>
        </div>
      </n-gi>
    </n-grid>
  </n-card>
</template>

<script setup lang="ts">
import { NCard, NGrid, NGi, NStatistic, NProgress, NDivider } from 'naive-ui'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

interface TagChartData {
  labels: string[]
  datasets: {
    data: number[]
    backgroundColor: string[]
    borderWidth: number
    borderColor: string
  }[]
}

interface Props {
  totalIncome: number
  totalBudget: number
  totalSpent: number
  remaining: number
  percentage: number
  balance: number
  totalProjected: number
  projectedRemaining: number
  projectedPercentage: number
  tagChartData: TagChartData
  isMobile: boolean
}

defineProps<Props>()

const tagChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const label = context.label || ''
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const percentage = total > 0 ? ((value / total) * 100).toFixed(2) : '0.00'
          return `${label}: ${value.toFixed(2)} € (${percentage}%)`
        }
      }
    }
  }
}
</script>
