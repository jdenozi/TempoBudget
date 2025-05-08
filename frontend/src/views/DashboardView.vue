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
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">My Budgets</h1>
      <n-button type="primary" @click="showModal = true">
        Create Budget
      </n-button>
    </div>

    <!-- Loading State -->
    <div v-if="budgetStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <!-- Budget List -->
    <n-grid v-else :cols="isMobile ? 1 : 3" :x-gap="16" :y-gap="16">
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
                {{ budget.budget_type === 'personal' ? 'Personal' : 'Group' }}
              </n-tag>
            </div>
          </template>

          <n-statistic label="Balance" value="0.00 €">
            <template #prefix>
              <n-icon><CashOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Empty State -->
    <n-empty
      v-if="!budgetStore.loading && budgetStore.budgets.length === 0"
      description="No budgets created"
      style="margin-top: 40px;"
    >
      <template #extra>
        <n-button @click="showModal = true" type="primary">
          Create my first budget
        </n-button>
      </template>
    </n-empty>

    <!-- Create Budget Modal -->
    <n-modal v-model:show="showModal">
      <n-card
        title="Create Budget"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
        :style="{ maxWidth: isMobile ? '95vw' : '500px' }"
      >
        <n-form ref="formRef" :model="newBudget" :rules="rules">
          <n-form-item label="Budget Name" path="name">
            <n-input v-model:value="newBudget.name" placeholder="Personal Budget" />
          </n-form-item>

          <n-form-item label="Type" path="type">
            <n-radio-group v-model:value="newBudget.type">
              <n-space>
                <n-radio value="personal">Personal</n-radio>
                <n-radio value="group">Group</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showModal = false">Cancel</n-button>
            <n-button type="primary" :loading="creating" @click="handleCreate">
              Create
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
  NIcon, NSpin, NEmpty, useMessage
} from 'naive-ui'
import { CashOutline } from '@vicons/ionicons5'
import { useBudgetStore } from '@/stores/budget'

const router = useRouter()
const message = useMessage()
const budgetStore = useBudgetStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Create budget modal visibility */
const showModal = ref(false)

/** Budget creation loading state */
const creating = ref(false)

/** Form reference for validation */
const formRef = ref<any>(null)

/** New budget form data */
const newBudget = ref({
  name: '',
  type: 'personal' as 'personal' | 'group',
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

  // Load budgets
  try {
    await budgetStore.fetchBudgets()
  } catch (error) {
    console.error('Error loading budgets:', error)
    message.error('Error loading budgets')
  }
})

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