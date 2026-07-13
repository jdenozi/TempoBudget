<template>
  <n-card size="small" class="category-card">
    <!-- Parent Category Header -->
    <div class="category-header" @click="expanded = !expanded">
      <div class="category-main">
        <div class="category-title-row">
          <span class="expand-icon" :class="{ expanded }">▶</span>
          <strong class="category-name">{{ category.name }}</strong>
          <span v-if="category.percentage > 100" class="warning-badge">⚠️</span>
          <n-space v-if="category.tags && category.tags.length > 0" size="small">
            <n-tag v-for="tag in category.tags" :key="tag" size="small" :type="getTagType(tag)">
              {{ tag }}
            </n-tag>
          </n-space>
        </div>

        <!-- Main progress bar (always visible) -->
        <div class="category-progress-section">
          <div class="progress-bar-container">
            <div
              class="progress-bar-fill"
              :style="{
                width: Math.min(category.percentage, 100) + '%',
                background: getProgressGradient(category.percentage, category.isIncome)
              }"
            ></div>
            <!-- Projected overlay -->
            <div
              v-if="category.projected > category.spent && category.projectedPercentage <= 100"
              class="progress-bar-projected"
              :style="{
                left: Math.min(category.percentage, 100) + '%',
                width: Math.min(category.projectedPercentage - category.percentage, 100 - category.percentage) + '%'
              }"
            ></div>
          </div>
          <div class="progress-stats">
            <span class="progress-spent">
              {{ category.spent.toFixed(0) }}€
              <span class="progress-separator">/</span>
              {{ category.amount.toFixed(0) }}€
            </span>
            <span class="progress-remaining" :class="{ negative: category.remaining < 0 }">
              {{ category.remaining >= 0 ? '+' : '' }}{{ category.remaining.toFixed(0) }}€
            </span>
          </div>
        </div>
      </div>

      <n-space size="small" class="category-actions" @click.stop>
        <n-button size="tiny" quaternary @click="$emit('edit', category)">{{ t('common.edit') }}</n-button>
        <n-popconfirm @positive-click="$emit('delete', category.id)">
          <template #trigger>
            <n-button size="tiny" quaternary type="error">{{ t('common.delete') }}</n-button>
          </template>
          {{ t('category.deleteCategoryConfirm') }}
        </n-popconfirm>
      </n-space>
    </div>

    <!-- Subcategories (always visible mini-bars) -->
    <div v-if="subcategories.length > 0" class="subcategories-preview">
      <div
        v-for="sub in subcategories"
        :key="sub.id"
        class="subcategory-row"
        @click.stop
      >
        <span class="subcategory-name">{{ sub.name }}</span>
        <div class="subcategory-progress">
          <div
            class="subcategory-progress-fill"
            :style="{
              width: sub.amount > 0 ? Math.min((sub.spent / sub.amount) * 100, 100) + '%' : '0%',
              background: getProgressColor(sub.amount > 0 ? (sub.spent / sub.amount) * 100 : 0, category.isIncome)
            }"
          ></div>
        </div>
        <span class="subcategory-amount">
          {{ sub.spent.toFixed(0) }}/{{ sub.amount.toFixed(0) }}€
        </span>
      </div>
    </div>

    <!-- Collapsible Content -->
    <n-collapse-transition :show="expanded">
      <!-- Member shares for group budgets -->
      <div v-if="isGroupBudget && members.length > 0" class="member-shares">
        <span v-for="member in members" :key="member.id" class="member-share">
          {{ member.user_name }}: <strong>{{ (category.amount * member.share / 100).toFixed(2) }} €</strong>
        </span>
      </div>

      <!-- Detailed Progress Bars -->
      <div class="detailed-progress">
        <!-- Spent/Received -->
        <div class="progress-row">
          <div class="progress-label-row">
            <span>{{ category.isIncome ? t('budget.received') : t('budget.spent') }}: {{ category.spent.toFixed(2) }} € ({{ category.percentage.toFixed(1) }}%)</span>
            <span :class="{ negative: category.remaining < 0, positive: category.remaining >= 0 }">
              {{ category.remaining.toFixed(2) }} € {{ category.isIncome ? t('budget.toReceive') : t('budget.remaining') }}
            </span>
          </div>
          <div class="progress-bar-lg">
            <div
              class="progress-bar-fill-lg"
              :style="{
                width: Math.min(category.percentage, 100) + '%',
                background: getProgressGradient(category.percentage, category.isIncome)
              }"
            ></div>
          </div>
        </div>

        <!-- Projected -->
        <div class="progress-row projected">
          <div class="progress-label-row">
            <span class="projected-label">{{ t('budget.projected') }}: {{ category.projected.toFixed(2) }} € ({{ category.projectedPercentage.toFixed(1) }}%)</span>
            <span :class="{ negative: category.projectedRemaining < 0, positive: category.projectedRemaining >= 0 }">
              {{ category.projectedRemaining.toFixed(2) }} € {{ category.isIncome ? t('budget.toReceive') : t('budget.remaining') }}
            </span>
          </div>
          <div class="progress-bar-lg">
            <div
              class="progress-bar-fill-lg projected-fill"
              :style="{
                width: Math.min(category.projectedPercentage, 100) + '%',
                background: category.projectedPercentage > 100 ? '#dc2626' : '#f59e0b'
              }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Detailed Subcategories -->
      <div v-if="subcategories.length > 0" class="subcategories-detailed">
        <div class="subcategories-header">{{ t('category.subcategories').toUpperCase() }}</div>
        <n-space vertical size="small">
          <div v-for="sub in subcategories" :key="sub.id" class="subcategory-card">
            <div class="subcategory-card-header">
              <div class="subcategory-card-title">
                <span class="subcategory-card-name">{{ sub.name }}</span>
                <span v-if="sub.amount > 0" class="subcategory-card-budget">({{ sub.amount.toFixed(2) }} €)</span>
                <span v-if="sub.amount > 0 && (sub.spent / sub.amount) > 1" class="warning-badge small">⚠️</span>
                <n-space v-if="sub.tags && sub.tags.length > 0" size="small">
                  <n-tag v-for="tag in sub.tags" :key="tag" size="tiny" :type="getTagType(tag)">
                    {{ tag }}
                  </n-tag>
                </n-space>
              </div>
              <n-space size="small" align="center">
                <n-button size="tiny" quaternary @click="$emit('edit', sub)">{{ t('common.edit') }}</n-button>
                <n-popconfirm @positive-click="$emit('delete', sub.id)">
                  <template #trigger>
                    <n-button size="tiny" quaternary type="error">{{ t('common.delete') }}</n-button>
                  </template>
                  {{ t('category.deleteCategoryConfirm') }}
                </n-popconfirm>
              </n-space>
            </div>

            <!-- Subcategory progress bar -->
            <div v-if="sub.amount > 0" class="subcategory-card-progress">
              <div class="progress-bar-sm">
                <div
                  class="progress-bar-fill-sm"
                  :style="{
                    width: Math.min((sub.spent / sub.amount) * 100, 100) + '%',
                    background: getProgressGradient((sub.spent / sub.amount) * 100, category.isIncome)
                  }"
                ></div>
              </div>
            </div>

            <div class="subcategory-card-stats">
              <span v-if="sub.amount > 0" class="stat-item">{{ t('budget.amount') }}: {{ sub.amount.toFixed(2) }} €</span>
              <span class="stat-item highlight">{{ category.isIncome ? t('budget.received') : t('budget.spent') }}: {{ sub.spent.toFixed(2) }} €</span>
              <span v-if="sub.amount > 0" class="stat-item" :class="{ negative: (sub.amount - sub.spent) < 0 }">
                {{ category.isIncome ? t('budget.toReceive') : t('budget.remaining') }}: {{ (sub.amount - sub.spent).toFixed(2) }} €
              </span>
              <span class="stat-item projected-text">{{ t('budget.projected') }}: {{ sub.projected.toFixed(2) }} €</span>
              <span
                v-if="sub.amount > 0 && sub.projected !== sub.spent"
                class="stat-item"
                :class="{ negative: (sub.amount - sub.projected) < 0 }"
              >
                ({{ t('budget.projectedRemaining') }}: {{ (sub.amount - sub.projected).toFixed(2) }} €)
              </span>
            </div>

            <!-- Member shares for subcategories -->
            <div v-if="isGroupBudget && members.length > 0 && sub.amount > 0" class="subcategory-members">
              <span v-for="member in members" :key="member.id" class="member-share-small">
                {{ member.user_name }}: {{ (sub.amount * member.share / 100).toFixed(2) }} €
              </span>
            </div>
          </div>
        </n-space>
      </div>

      <!-- Add Subcategory Button -->
      <div class="add-subcategory">
        <n-button size="small" dashed block @click="$emit('addSubcategory', category.id)">
          + {{ t('category.addSubcategory') }}
        </n-button>
      </div>
    </n-collapse-transition>
  </n-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NSpace, NTag, NButton, NPopconfirm, NCollapseTransition } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { BudgetMemberWithUser } from '@/services/api'

const { t } = useI18n()
const expanded = ref(false)

interface CategoryWithSpent {
  id: string
  name: string
  amount: number
  tags: string[]
  parent_id: string | null
  spent: number
  projected: number
  remaining: number
  projectedRemaining: number
  percentage: number
  projectedPercentage: number
  isIncome?: boolean
}

interface Props {
  category: CategoryWithSpent
  subcategories: CategoryWithSpent[]
  members: BudgetMemberWithUser[]
  isGroupBudget: boolean
}

defineProps<Props>()

defineEmits<{
  'edit': [category: CategoryWithSpent]
  'delete': [categoryId: string]
  'addSubcategory': [parentId: string]
}>()

const getTagType = (tag: string) => {
  const types: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
    'crédit': 'error',
    'besoin': 'warning',
    'loisir': 'info',
    'épargne': 'success',
    'revenu': 'success',
  }
  return types[tag] || 'default'
}

const getProgressColor = (pct: number, isIncome?: boolean) => {
  if (isIncome) return '#22c55e'
  if (pct <= 70) return '#22c55e'       // vert
  if (pct <= 90) return '#f59e0b'       // orange
  if (pct <= 100) return '#3b82f6'      // bleu (objectif atteint)
  return '#ef4444'                       // rouge (dépassement)
}

const getProgressGradient = (pct: number, isIncome?: boolean) => {
  if (isIncome) return 'linear-gradient(90deg, #22c55e, #4ade80)'
  if (pct <= 70) return 'linear-gradient(90deg, #22c55e, #4ade80)'
  if (pct <= 90) return 'linear-gradient(90deg, #f59e0b, #fbbf24)'
  if (pct <= 100) return 'linear-gradient(90deg, #3b82f6, #60a5fa)'  // bleu
  return 'linear-gradient(90deg, #ef4444, #f87171)'                   // rouge
}
</script>

<style scoped>
.category-card {
  transition: box-shadow 0.2s ease;
}

.category-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  cursor: pointer;
  gap: 12px;
}

.category-main {
  flex: 1;
  min-width: 0;
}

.category-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.category-name {
  font-size: 16px;
}

.warning-badge {
  font-size: 14px;
  animation: pulse-warning 1.5s ease-in-out infinite;
}

.warning-badge.small {
  font-size: 12px;
}

@keyframes pulse-warning {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.expand-icon {
  display: inline-block;
  font-size: 10px;
  color: #888;
  transition: transform 0.2s ease;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

/* Main progress bar */
.category-progress-section {
  margin-left: 18px;
}

.progress-bar-container {
  position: relative;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.progress-bar-projected {
  position: absolute;
  top: 0;
  height: 100%;
  background: rgba(245, 158, 11, 0.4);
  border-radius: 0 4px 4px 0;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 13px;
}

.progress-spent {
  color: rgba(255, 255, 255, 0.7);
}

.progress-separator {
  margin: 0 2px;
  opacity: 0.5;
}

.progress-remaining {
  font-weight: 600;
  color: #22c55e;
}

.progress-remaining.negative {
  color: #ef4444;
}

.category-actions {
  flex-shrink: 0;
}

/* Subcategories preview (always visible mini-bars) */
.subcategories-preview {
  margin-top: 12px;
  margin-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.subcategory-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.subcategory-name {
  width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #888;
}

.subcategory-progress {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.subcategory-progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.subcategory-amount {
  width: 80px;
  text-align: right;
  color: #666;
  font-size: 11px;
}

/* Collapsible content styles */
.member-shares {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  margin-left: 18px;
  font-size: 12px;
}

.member-share {
  color: #888;
}

.detailed-progress {
  margin-top: 16px;
  margin-bottom: 12px;
}

.progress-row {
  margin-bottom: 12px;
}

.progress-row.projected {
  margin-top: 8px;
}

.progress-label-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 6px;
  color: rgba(255, 255, 255, 0.7);
}

.projected-label {
  color: #f59e0b;
}

.positive {
  color: #22c55e;
}

.negative {
  color: #ef4444;
}

.progress-bar-lg {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill-lg {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.projected-fill {
  opacity: 0.9;
}

/* Detailed subcategories */
.subcategories-detailed {
  margin-top: 20px;
}

.subcategories-header {
  font-size: 11px;
  color: #666;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.subcategory-card {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  padding: 12px;
}

.subcategory-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.subcategory-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.subcategory-card-name {
  font-size: 14px;
  font-weight: 500;
}

.subcategory-card-budget {
  font-size: 12px;
  color: #888;
}

.subcategory-card-progress {
  margin-bottom: 8px;
}

.progress-bar-sm {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill-sm {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.subcategory-card-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
}

.stat-item {
  color: #888;
}

.stat-item.highlight {
  color: #22c55e;
}

.stat-item.projected-text {
  color: #f59e0b;
}

.subcategory-members {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  font-size: 11px;
}

.member-share-small {
  color: #666;
}

.add-subcategory {
  margin-top: 16px;
}
</style>
