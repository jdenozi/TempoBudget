<template>
  <n-card>
    <!-- Main Summary Row -->
    <div class="summary-grid" :class="{ mobile: isMobile }">
      <!-- Revenus -->
      <div class="summary-box income">
        <div class="summary-label">Revenus</div>
        <div class="summary-row">
          <span class="summary-sub">Prévu</span>
          <span class="summary-value">{{ totalIncome.toFixed(2) }} €</span>
        </div>
        <div class="summary-row">
          <span class="summary-sub">Reçu</span>
          <span class="summary-value highlight">{{ totalIncomeReceived.toFixed(2) }} €</span>
        </div>
      </div>

      <!-- Budget Dépenses -->
      <div class="summary-box expenses">
        <div class="summary-label">Dépenses</div>
        <div class="summary-row">
          <span class="summary-sub">Budget</span>
          <span class="summary-value">{{ totalBudget.toFixed(2) }} €</span>
        </div>
        <div class="summary-row">
          <span class="summary-sub">Dépensé</span>
          <span class="summary-value highlight">{{ totalSpent.toFixed(2) }} €</span>
        </div>
      </div>

      <!-- Restant -->
      <div class="summary-box remaining" :class="{ negative: remainingFromIncome < 0 }">
        <div class="summary-label">Restant</div>
        <div class="summary-row">
          <span class="summary-sub">vs Budget</span>
          <span class="summary-value" :class="{ negative: remaining < 0 }">{{ remaining.toFixed(2) }} €</span>
        </div>
        <div class="summary-row">
          <span class="summary-sub">vs Revenus</span>
          <span class="summary-value highlight" :class="{ negative: remainingFromIncome < 0 }">{{ remainingFromIncome.toFixed(2) }} €</span>
        </div>
      </div>

      <!-- Progress -->
      <div class="summary-box progress-box">
        <div class="summary-label">Utilisé</div>
        <n-progress
          type="circle"
          :percentage="Math.min(percentage, 100)"
          :color="percentage > 100 ? '#d03050' : '#18a058'"
          :style="{ width: '80px' }"
        >
          <span class="progress-text">{{ percentage.toFixed(0) }}%</span>
        </n-progress>
      </div>
    </div>

    <!-- Solde -->
    <div class="balance-row" :class="{ negative: balance < 0 }">
      <span>Solde (Revenus - Budget):</span>
      <span class="balance-value">{{ balance >= 0 ? '+' : '' }}{{ balance.toFixed(2) }} €</span>
    </div>

    <!-- Projected Summary -->
    <n-divider style="margin: 16px 0;" />
    <div class="section-title">PROJETÉ (avec récurrents)</div>
    <div class="projected-grid" :class="{ mobile: isMobile }">
      <div class="projected-item">
        <span class="projected-label">Dépenses</span>
        <span class="projected-value">{{ totalProjected.toFixed(2) }} €</span>
      </div>
      <div class="projected-item">
        <span class="projected-label">Restant (budget)</span>
        <span class="projected-value" :class="{ negative: projectedRemaining < 0 }">{{ projectedRemaining.toFixed(2) }} €</span>
      </div>
      <div class="projected-item">
        <span class="projected-label">Restant (revenus)</span>
        <span class="projected-value" :class="{ negative: projectedRemainingFromIncome < 0 }">{{ projectedRemainingFromIncome.toFixed(2) }} €</span>
      </div>
      <div class="projected-item progress">
        <n-progress
          type="circle"
          :percentage="Math.min(projectedPercentage, 100)"
          :color="projectedPercentage > 100 ? '#d03050' : '#f0a020'"
          :style="{ width: '60px' }"
        >
          <span class="progress-text small">{{ projectedPercentage.toFixed(0) }}%</span>
        </n-progress>
      </div>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { NCard, NProgress, NDivider } from 'naive-ui'

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
  isMobile: boolean
}

defineProps<Props>()
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.summary-grid.mobile {
  grid-template-columns: repeat(2, 1fr);
}

.summary-box {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid #888;
}

.summary-box.income {
  border-left-color: #18a058;
}

.summary-box.expenses {
  border-left-color: #d03050;
}

.summary-box.remaining {
  border-left-color: #2080f0;
}

.summary-box.remaining.negative {
  border-left-color: #d03050;
}

.summary-box.progress-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-left-color: #18a058;
}

.summary-label {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.summary-sub {
  font-size: 11px;
  color: #666;
}

.summary-value {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.summary-value.highlight {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.summary-value.negative {
  color: #d03050;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
}

.progress-text.small {
  font-size: 12px;
}

.balance-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(24, 160, 88, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(24, 160, 88, 0.3);
}

.balance-row.negative {
  background: rgba(208, 48, 80, 0.1);
  border-color: rgba(208, 48, 80, 0.3);
}

.balance-value {
  font-size: 18px;
  font-weight: 700;
  color: #18a058;
}

.balance-row.negative .balance-value {
  color: #d03050;
}

.section-title {
  font-size: 12px;
  color: #888;
  margin-bottom: 12px;
  font-weight: 500;
}

.projected-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  align-items: center;
}

.projected-grid.mobile {
  grid-template-columns: repeat(2, 1fr);
}

.projected-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.projected-item.progress {
  display: flex;
  align-items: center;
  justify-content: center;
}

.projected-label {
  font-size: 11px;
  color: #666;
}

.projected-value {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.projected-value.negative {
  color: #d03050;
}
</style>
