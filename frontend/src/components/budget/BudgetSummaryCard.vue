<template>
  <n-card>
    <!-- Income vs Expenses Summary -->
    <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-statistic label="Revenus (prévu)" :value="totalIncome.toFixed(2)">
          <template #prefix><span style="color: #18a058;">+</span></template>
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Revenus (reçu)" :value="totalIncomeReceived.toFixed(2)">
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
        <n-statistic label="Solde (prévu)" :value="balance.toFixed(2)">
          <template #prefix><span :style="{ color: balance >= 0 ? '#18a058' : '#d03050' }">{{ balance >= 0 ? '+' : '' }}</span></template>
          <template #suffix>€</template>
        </n-statistic>
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
        <n-statistic label="Restant (budget)" :value="remaining.toFixed(2)">
          <template #prefix><span :style="{ color: remaining >= 0 ? '#18a058' : '#d03050' }">{{ remaining >= 0 ? '' : '' }}</span></template>
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Restant (revenus)" :value="remainingFromIncome.toFixed(2)">
          <template #prefix><span :style="{ color: remainingFromIncome >= 0 ? '#18a058' : '#d03050' }">{{ remainingFromIncome >= 0 ? '' : '' }}</span></template>
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
            {{ percentage.toFixed(0) }}%
          </n-progress>
        </div>
      </n-gi>
    </n-grid>

    <!-- Projected Summary -->
    <n-divider style="margin: 16px 0;" />
    <div style="font-size: 12px; color: #888; margin-bottom: 8px;">PROJETÉ (avec récurrents)</div>
    <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-statistic label="Dépenses projetées" :value="totalProjected.toFixed(2)">
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Restant (budget)" :value="projectedRemaining.toFixed(2)">
          <template #prefix><span :style="{ color: projectedRemaining >= 0 ? '#18a058' : '#d03050' }"></span></template>
          <template #suffix>€</template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="Restant (revenus)" :value="projectedRemainingFromIncome.toFixed(2)">
          <template #prefix><span :style="{ color: projectedRemainingFromIncome >= 0 ? '#18a058' : '#d03050' }"></span></template>
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
            {{ projectedPercentage.toFixed(0) }}%
          </n-progress>
        </div>
      </n-gi>
    </n-grid>

    <!-- Tag Chart -->
    <n-divider style="margin: 16px 0;" />
    <div style="display: flex; flex-direction: column; align-items: center;">
      <div style="font-size: 12px; color: #888; margin-bottom: 8px;">RÉPARTITION PAR TAG</div>
      <div :style="{ width: isMobile ? '120px' : '150px', height: isMobile ? '120px' : '150px' }">
        <Doughnut
          v-if="tagChartData.labels.length > 0"
          :data="tagChartData"
          :options="tagChartOptions"
        />
        <div v-else style="display: flex; align-items: center; justify-content: center; height: 100%; color: #888; font-size: 11px;">
          Aucun tag
        </div>
      </div>
    </div>
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
  totalIncomeReceived: number
  totalBudget: number
  totalSpent: number
  remaining: number
  remainingFromIncome: number
  percentage: number
  balance: number
  totalProjected: number
  projectedRemaining: number
  projectedRemainingFromIncome: number
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
