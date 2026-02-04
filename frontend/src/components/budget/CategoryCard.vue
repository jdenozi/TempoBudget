<template>
  <n-card size="small">
    <!-- Parent Category Header (clickable to expand/collapse) -->
    <div
      style="display: flex; justify-content: space-between; align-items: flex-start; cursor: pointer;"
      @click="expanded = !expanded"
    >
      <div style="flex: 1;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
          <span
            class="expand-icon"
            :class="{ expanded }"
          >▶</span>
          <strong style="font-size: 16px;">{{ category.name }}</strong>
          <n-space v-if="category.tags && category.tags.length > 0" size="small">
            <n-tag v-for="tag in category.tags" :key="tag" size="small" :type="getTagType(tag)">
              {{ tag }}
            </n-tag>
          </n-space>
        </div>
        <div style="font-size: 13px; color: #888; margin-left: 20px;">
          Budget: <strong>{{ category.amount.toFixed(2) }} €</strong>
          <span style="margin-left: 16px;">
            {{ category.isIncome ? 'Reçu' : 'Dépensé' }}: <strong>{{ category.spent.toFixed(2) }} €</strong>
          </span>
          <span
            style="margin-left: 16px;"
            :style="{ color: category.remaining >= 0 ? '#18a058' : '#d03050' }"
          >
            Restant: <strong>{{ category.remaining.toFixed(2) }} €</strong>
          </span>
          <span
            v-if="category.projected !== category.spent"
            style="margin-left: 16px;"
            :style="{ color: category.projectedRemaining >= 0 ? '#18a058' : '#d03050' }"
          >
            (Projeté: <strong>{{ category.projectedRemaining.toFixed(2) }} €</strong>)
          </span>
        </div>
      </div>
      <n-space size="small" @click.stop>
        <n-button size="tiny" quaternary @click="$emit('edit', category)">Edit</n-button>
        <n-popconfirm @positive-click="$emit('delete', category.id)">
          <template #trigger>
            <n-button size="tiny" quaternary type="error">Delete</n-button>
          </template>
          Delete this category?
        </n-popconfirm>
      </n-space>
    </div>

    <!-- Collapsible Content -->
    <n-collapse-transition :show="expanded">
      <!-- Member shares for group budgets -->
      <div
        v-if="isGroupBudget && members.length > 0"
        style="display: flex; gap: 16px; margin-top: 8px; font-size: 12px; margin-left: 20px;"
      >
        <span v-for="member in members" :key="member.id" style="color: #888;">
          {{ member.user_name }}: <strong>{{ (category.amount * member.share / 100).toFixed(2) }} €</strong>
        </span>
      </div>

      <!-- Progress Bars -->
      <div style="margin-top: 12px; margin-bottom: 8px;">
      <!-- Spent/Received -->
      <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
        <span>{{ category.isIncome ? 'Reçu' : 'Dépensé' }}: {{ category.spent.toFixed(2) }} € ({{ category.percentage.toFixed(2) }}%)</span>
        <span :style="{ color: category.remaining >= 0 ? '#18a058' : '#d03050' }">
          {{ category.remaining.toFixed(2) }} € {{ category.isIncome ? 'à recevoir' : 'restant' }}
        </span>
      </div>
      <n-progress
        :percentage="Math.min(category.percentage, 100)"
        :color="category.isIncome ? '#18a058' : (category.percentage > 100 ? '#d03050' : '#18a058')"
        :show-indicator="false"
      />
      <!-- Projected -->
      <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; margin-top: 8px;">
        <span style="color: #f0a020;">Projeté: {{ category.projected.toFixed(2) }} € ({{ category.projectedPercentage.toFixed(2) }}%)</span>
        <span :style="{ color: category.projectedRemaining >= 0 ? '#18a058' : '#d03050' }">
          {{ category.projectedRemaining.toFixed(2) }} € {{ category.isIncome ? 'à recevoir' : 'restant' }}
        </span>
      </div>
      <n-progress
        :percentage="Math.min(category.projectedPercentage, 100)"
        :color="category.projectedPercentage > 100 ? '#d03050' : '#f0a020'"
        :show-indicator="false"
      />
    </div>

    <!-- Subcategories -->
    <div v-if="subcategories.length > 0" style="margin-top: 16px;">
      <div style="font-size: 12px; color: #888; margin-bottom: 8px;">SUBCATEGORIES</div>
      <n-space vertical size="small">
        <div
          v-for="sub in subcategories"
          :key="sub.id"
          style="background: rgba(255,255,255,0.05); border-radius: 6px; padding: 10px 12px;"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 14px;">{{ sub.name }}</span>
              <span v-if="sub.amount > 0" style="font-size: 12px; color: #888;">
                ({{ sub.amount.toFixed(2) }} €)
              </span>
              <n-space v-if="sub.tags && sub.tags.length > 0" size="small">
                <n-tag v-for="tag in sub.tags" :key="tag" size="tiny" :type="getTagType(tag)">
                  {{ tag }}
                </n-tag>
              </n-space>
            </div>
            <n-space size="small" align="center">
              <n-button size="tiny" quaternary @click="$emit('edit', sub)">Edit</n-button>
              <n-popconfirm @positive-click="$emit('delete', sub.id)">
                <template #trigger>
                  <n-button size="tiny" quaternary type="error">Del</n-button>
                </template>
                Delete?
              </n-popconfirm>
            </n-space>
          </div>
          <div style="display: flex; gap: 16px; font-size: 12px;">
            <span v-if="sub.amount > 0" style="color: #888;">Budget: {{ sub.amount.toFixed(2) }} €</span>
            <span style="color: #18a058;">{{ category.isIncome ? 'Reçu' : 'Dépensé' }}: {{ sub.spent.toFixed(2) }} €</span>
            <span v-if="sub.amount > 0" :style="{ color: (sub.amount - sub.spent) >= 0 ? '#18a058' : '#d03050' }">
              {{ category.isIncome ? 'À recevoir' : 'Restant' }}: {{ (sub.amount - sub.spent).toFixed(2) }} €
            </span>
            <span style="color: #f0a020;">Projeté: {{ sub.projected.toFixed(2) }} €</span>
          </div>
          <!-- Member shares for subcategories -->
          <div
            v-if="isGroupBudget && members.length > 0 && sub.amount > 0"
            style="display: flex; gap: 12px; margin-top: 4px; font-size: 11px;"
          >
            <span v-for="member in members" :key="member.id" style="color: #666;">
              {{ member.user_name }}: {{ (sub.amount * member.share / 100).toFixed(2) }} €
            </span>
          </div>
        </div>
      </n-space>
    </div>

      <!-- Add Subcategory Button -->
      <div style="margin-top: 12px;">
        <n-button size="small" dashed block @click="$emit('addSubcategory', category.id)">
          + Add Subcategory
        </n-button>
      </div>
    </n-collapse-transition>
  </n-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NSpace, NTag, NButton, NPopconfirm, NProgress, NCollapseTransition } from 'naive-ui'
import type { BudgetMemberWithUser } from '@/services/api'

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
</script>

<style scoped>
.expand-icon {
  display: inline-block;
  font-size: 10px;
  color: #888;
  transition: transform 0.2s ease;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}
</style>
