<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Dashboard View

  Main budget overview page displaying all user budgets in a responsive grid.
  Supports budget creation via a modal form and navigation to budget details.
-->

<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('budget.budgets') }}</h1>
      <n-button type="primary" @click="showModal = true">
        {{ t('budget.createBudget') }}
      </n-button>
    </div>

    <!-- Loading State -->
    <div v-if="budgetStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <!-- Budget List -->
    <n-grid v-else :cols="isMobile ? 1 : 2" :x-gap="16" :y-gap="16">
      <n-gi v-for="budget in budgetStore.budgets" :key="budget.id">
        <n-card
          hoverable
          style="cursor: pointer;"
          @click="goToBudget(budget.id)"
        >
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <strong>{{ budget.name }}</strong>
              <n-tag :type="budget.budget_type === 'personal' ? 'info' : 'success'" size="small">
                {{ budget.budget_type === 'personal' ? t('budget.personal') : t('budget.shared') }}
              </n-tag>
            </div>
          </template>

          <!-- Stats Grid -->
          <n-grid :cols="2" :x-gap="12" :y-gap="12">
            <n-gi>
              <n-statistic :label="t('budget.income')" :value="(getSummary(budget.id)?.income_budget || 0).toFixed(2)">
                <template #prefix>
                  <n-icon color="#18a058"><TrendingUpOutline /></n-icon>
                </template>
                <template #suffix>€</template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic :label="t('budget.totalBudget')" :value="(getSummary(budget.id)?.total_budget || 0).toFixed(2)">
                <template #prefix>
                  <n-icon color="#2080f0"><WalletOutline /></n-icon>
                </template>
                <template #suffix>€</template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic :label="t('budget.spent')" :value="(getSummary(budget.id)?.total_spent || 0).toFixed(2)">
                <template #prefix>
                  <n-icon color="#d03050"><TrendingDownOutline /></n-icon>
                </template>
                <template #suffix>€</template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic :label="t('budget.balance')" :value="(getSummary(budget.id)?.balance || 0).toFixed(2)">
                <template #prefix>
                  <n-icon :color="(getSummary(budget.id)?.balance || 0) >= 0 ? '#18a058' : '#d03050'"><CashOutline /></n-icon>
                </template>
                <template #suffix>€</template>
              </n-statistic>
            </n-gi>
          </n-grid>

          <!-- Progress Bar -->
          <div style="margin-top: 16px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
              <span>{{ (getSummary(budget.id)?.percentage || 0).toFixed(1) }}% {{ t('budget.spent').toLowerCase() }}</span>
              <span style="color: #888;">{{ getSummary(budget.id)?.transaction_count || 0 }} {{ t('transaction.transactions').toLowerCase() }}</span>
            </div>
            <n-progress
              :percentage="Math.min(getSummary(budget.id)?.percentage || 0, 100)"
              :color="(getSummary(budget.id)?.percentage || 0) > 100 ? '#d03050' : '#18a058'"
              :show-indicator="false"
            />
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Empty State -->
    <n-empty
      v-if="!budgetStore.loading && budgetStore.budgets.length === 0"
      :description="t('budget.noBudgets')"
      style="margin-top: 40px;"
    >
      <template #extra>
        <n-button @click="showModal = true" type="primary">
          {{ t('budget.createBudget') }}
        </n-button>
      </template>
    </n-empty>

    <!-- Create Budget Modal -->
    <n-modal v-model:show="showModal">
      <n-card
        :title="t('budget.createBudget')"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
        :style="{ maxWidth: isMobile ? '95vw' : '500px' }"
      >
        <n-form ref="formRef" :model="newBudget" :rules="rules">
          <n-form-item :label="t('budget.budgetName')" path="name">
            <n-input v-model:value="newBudget.name" :placeholder="t('budget.personal')" />
          </n-form-item>

          <n-form-item :label="t('budget.budgetType')" path="type">
            <n-radio-group v-model:value="newBudget.type">
              <n-space>
                <n-radio value="personal">{{ t('budget.personal') }}</n-radio>
                <n-radio value="shared">{{ t('budget.shared') }}</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showModal = false">{{ t('common.cancel') }}</n-button>
            <n-button type="primary" :loading="creating" @click="handleCreate">
              {{ t('common.add') }}
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
/**
 * Dashboard view component displaying all user budgets.
 *
 * Features:
 * - Responsive grid layout
 * - Budget creation modal
 * - Loading and empty states
 * - Navigation to budget details
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NSpace, NButton, NGrid, NGi, NCard, NTag, NStatistic,
  NModal, NForm, NFormItem, NInput, NRadioGroup, NRadio,
  NIcon, NSpin, NEmpty, NProgress, useMessage
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { CashOutline, WalletOutline, TrendingUpOutline, TrendingDownOutline } from '@vicons/ionicons5'
import { useBudgetStore } from '@/stores/budget'
import { budgetsAPI, type BudgetSummary } from '@/services/api'

const router = useRouter()
const message = useMessage()
const { t } = useI18n()
const budgetStore = useBudgetStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Create budget modal visibility */
const showModal = ref(false)

/** Budget creation loading state */
const creating = ref(false)

/** Form reference for validation */
const formRef = ref<any>(null)

/** Budget summaries with stats */
const summaries = ref<BudgetSummary[]>([])

/** New budget form data */
const newBudget = ref({
  name: '',
  type: 'personal' as 'personal' | 'shared',
})

/** Form validation rules */
const rules = {
  name: {
    required: true,
    message: 'Name is required',
    trigger: 'blur',
  },
}

/**
 * Checks if the viewport is mobile-sized.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // Load budgets and summaries
  try {
    await budgetStore.fetchBudgets()
    summaries.value = await budgetsAPI.getSummaries()
  } catch (error) {
    console.error('Error loading budgets:', error)
    message.error('Error loading budgets')
  }
})

/**
 * Gets summary for a specific budget.
 * @param budgetId - Budget unique identifier
 */
const getSummary = (budgetId: string): BudgetSummary | undefined => {
  return summaries.value.find(s => s.id === budgetId)
}

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

/**
 * Navigates to the budget detail view.
 * @param id - Budget unique identifier
 */
const goToBudget = (id: string) => {
  router.push({ name: 'budget-detail', params: { id } })
}

/**
 * Handles budget creation form submission.
 */
const handleCreate = () => {
  formRef.value?.validate(async (errors: any) => {
    if (errors) return

    creating.value = true
    try {
      await budgetStore.createBudget(newBudget.value.name, newBudget.value.type)
      message.success('Budget created!')
      showModal.value = false
      newBudget.value = { name: '', type: 'personal' }
    } catch (error) {
      console.error('Error creating budget:', error)
      message.error('Error creating budget')
    } finally {
      creating.value = false
    }
  })
}
</script>