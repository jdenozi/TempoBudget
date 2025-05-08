<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Budget Detail View

  Displays detailed budget information including:
  - Budget summary (total, spent, remaining)
  - Category breakdown with spending progress
  - Member management for group budgets
  - Category and member invitation modals
-->

<template>
  <n-space vertical size="large">
    <!-- Header -->
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <div>
        <n-button text @click="router.back()" style="margin-bottom: 8px;">
          ← Back
        </n-button>
        <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">
          {{ budgetStore.currentBudget?.name || 'Budget' }}
        </h1>
      </div>

      <n-space :vertical="isMobile">
        <n-date-picker
          v-model:value="selectedMonth"
          type="month"
          :style="{ width: isMobile ? '100%' : '200px' }"
        />

        <n-popconfirm
          @positive-click="handleDeleteBudget"
        >
          <template #trigger>
            <n-button type="error" ghost>
              Delete Budget
            </n-button>
          </template>
          Are you sure you want to delete this budget? This action is irreversible.
        </n-popconfirm>
      </n-space>
    </div>

    <!-- Loading -->
    <div v-if="budgetStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <template v-else>
      <!-- Summary -->
      <n-card>
        <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
          <n-gi>
            <n-statistic label="Total Budget" :value="totalBudget.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic label="Spent" :value="totalSpent.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic label="Remaining" :value="remaining.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <div style="display: flex; justify-content: center;">
              <n-progress
                type="circle"
                :percentage="percentage"
                :color="percentage > 100 ? '#d03050' : '#18a058'"
                :style="{ width: isMobile ? '80px' : '100px' }"
              />
            </div>
          </n-gi>
        </n-grid>
      </n-card>

      <!-- Categories -->
      <n-card title="Categories">
        <n-empty
          v-if="budgetStore.categories.length === 0"
          description="No categories"
        >
          <template #extra>
            <n-button @click="showAddCategory = true" type="primary" size="small">
              Add a Category
            </n-button>
          </template>
        </n-empty>

        <n-grid v-else :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
          <n-gi v-for="category in categoriesWithSpent" :key="category.id">
            <n-card size="small">
              <div style="margin-bottom: 8px;">
                <strong>{{ category.name }}</strong>
              </div>
              <div style="font-size: 12px; color: #888; margin-bottom: 8px;">
                {{ category.spent.toFixed(2) }} / {{ category.amount.toFixed(2) }} €
              </div>
              <n-progress
                :percentage="category.percentage"
                :color="category.percentage > 100 ? '#d03050' : '#18a058'"
                :show-indicator="false"
              />
              <div
                style="font-size: 12px; margin-top: 4px;"
                :style="{ color: category.remaining >= 0 ? '#18a058' : '#d03050' }"
              >
                Remaining: {{ category.remaining.toFixed(2) }} €
              </div>
            </n-card>
          </n-gi>
        </n-grid>

        <template #footer>
          <n-button @click="showAddCategory = true" type="primary" size="small">
            Add a Category
          </n-button>
        </template>
      </n-card>

      <!-- Members (only for group budgets) -->
      <n-card v-if="budgetStore.currentBudget?.budget_type === 'group'" title="Budget Members">
        <n-space vertical>
          <!-- Member list -->
          <n-list v-if="members.length > 0" bordered>
            <n-list-item v-for="member in members" :key="member.id">
              <template #prefix>
                <n-avatar
                  :size="40"
                  round
                  :src="member.user_avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${member.user_name}`"
                />
              </template>

              <n-thing :title="member.user_name">
                <template #description>
                  {{ member.user_email }}
                </template>
              </n-thing>

              <template #suffix>
                <n-space align="center">
                  <n-tag :type="member.role === 'owner' ? 'success' : 'default'" size="small">
                    {{ member.role === 'owner' ? 'Owner' : 'Member' }}
                  </n-tag>

                  <n-popconfirm
                    v-if="member.role !== 'owner' && isOwner"
                    @positive-click="handleRemoveMember(member.id)"
                  >
                    <template #trigger>
                      <n-button size="small" type="error" quaternary circle>
                        <template #icon>
                          <n-icon><TrashOutline /></n-icon>
                        </template>
                      </n-button>
                    </template>
                    Remove this member from the budget?
                  </n-popconfirm>
                </n-space>
              </template>
            </n-list-item>
          </n-list>

          <n-empty v-else description="No members" />
        </n-space>

        <template #footer>
          <n-button
            v-if="isOwner"
            @click="showInviteModal = true"
            type="primary"
            size="small"
          >
            Invite a Member
          </n-button>
        </template>
      </n-card>
    </template>

    <!-- Add category modal -->
    <n-modal v-model:show="showAddCategory">
      <n-card
        title="Add a Category"
        :bordered="false"
        size="huge"
        role="dialog"
        :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
      >
        <n-form ref="categoryFormRef" :model="newCategory">
          <n-form-item label="Name">
            <n-input v-model:value="newCategory.name" placeholder="Housing" />
          </n-form-item>

          <n-form-item label="Amount">
            <n-input-number
              v-model:value="newCategory.amount"
              :min="0"
              :precision="2"
              style="width: 100%;"
            >
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showAddCategory = false">Cancel</n-button>
            <n-button type="primary" :loading="addingCategory" @click="handleAddCategory">
              Add
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- Member invitation modal -->
    <n-modal v-model:show="showInviteModal">
      <n-card
        title="Invite a Member"
        :bordered="false"
        size="huge"
        role="dialog"
        :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
      >
        <n-form ref="inviteFormRef" :model="inviteData">
          <n-form-item label="User Email">
            <n-input
              v-model:value="inviteData.email"
              placeholder="email@example.com"
              type="email"
            />
          </n-form-item>

          <n-form-item label="Role">
            <n-radio-group v-model:value="inviteData.role">
              <n-space>
                <n-radio value="member">Member</n-radio>
                <n-radio value="owner">Owner</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showInviteModal = false">Cancel</n-button>
            <n-button type="primary" :loading="inviting" @click="handleInviteMember">
              Invite
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
/**
 * Budget detail view component.
 *
 * Features:
 * - Display budget summary with total, spent, and remaining amounts
 * - Category breakdown with spending progress bars
 * - Member management for group budgets (invite, remove)
 * - Add new categories
 * - Delete budget functionality
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NSpace, NButton, NDatePicker, NCard, NGrid, NGi,
  NStatistic, NProgress, NEmpty, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSpin, NList, NListItem, NThing,
  NAvatar, NTag, NIcon, NRadioGroup, NRadio, NPopconfirm,
  useMessage
} from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import { useBudgetStore } from '@/stores/budget'
import { useAuthStore } from '@/stores/auth'
import { budgetMembersAPI, budgetsAPI, type BudgetMemberWithUser } from '@/services/api'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const budgetStore = useBudgetStore()
const authStore = useAuthStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** Selected month timestamp for filtering */
const selectedMonth = ref(Date.now())

/** Add category modal visibility */
const showAddCategory = ref(false)

/** Loading state for adding category */
const addingCategory = ref(false)

/** Category form reference */
const categoryFormRef = ref<any>(null)

/** New category form data */
const newCategory = ref({
  name: '',
  amount: 0,
})

/** List of budget members */
const members = ref<BudgetMemberWithUser[]>([])

/** Invite member modal visibility */
const showInviteModal = ref(false)

/** Loading state for invitation */
const inviting = ref(false)

/** Invite form reference */
const inviteFormRef = ref<any>(null)

/** Invitation form data */
const inviteData = ref({
  email: '',
  role: 'member' as 'member' | 'owner',
})

/**
 * Checks if the viewport is mobile-sized.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

/**
 * Determines if the current user is an owner of this budget.
 * For personal budgets, the creator is always the owner.
 * For group budgets, checks the member list for owner role.
 */
const isOwner = computed(() => {
  if (!authStore.user || !budgetStore.currentBudget) return false

  // For personal budgets, the user is always the owner
  if (budgetStore.currentBudget.budget_type === 'personal') {
    return budgetStore.currentBudget.user_id === authStore.user.id
  }

  // For group budgets, check the members list
  return members.value.some(m =>
    m.user_id === authStore.user!.id && m.role === 'owner'
  )
})

/**
 * Loads the member list for group budgets.
 */
const loadMembers = async () => {
  if (!budgetStore.currentBudget || budgetStore.currentBudget.budget_type !== 'group') {
    return
  }

  try {
    members.value = await budgetMembersAPI.getMembers(budgetStore.currentBudget.id)
  } catch (error) {
    console.error('Error loading members:', error)
  }
}

/**
 * Invites a new member to the budget.
 */
const handleInviteMember = async () => {
  if (!inviteData.value.email || !budgetStore.currentBudget) {
    message.error('Email is required')
    return
  }

  inviting.value = true
  try {
    await budgetMembersAPI.inviteMember(
      budgetStore.currentBudget.id,
      inviteData.value.email,
      inviteData.value.role
    )
    message.success('Invitation sent!')
    showInviteModal.value = false
    inviteData.value = { email: '', role: 'member' }
  } catch (error: any) {
    console.error('Error inviting member:', error)
    if (error.response?.status === 404) {
      message.error('User not found')
    } else if (error.response?.status === 409) {
      message.error('This user is already a member')
    } else if (error.response?.status === 403) {
      message.error('You must be an owner to invite')
    } else {
      message.error('Error sending invitation')
    }
  } finally {
    inviting.value = false
  }
}

/**
 * Removes a member from the budget.
 * @param memberId - The member ID to remove
 */
const handleRemoveMember = async (memberId: string) => {
  if (!budgetStore.currentBudget) return

  try {
    await budgetMembersAPI.removeMember(budgetStore.currentBudget.id, memberId)
    message.success('Member removed')
    await loadMembers()
  } catch (error) {
    console.error('Error removing member:', error)
    message.error('Error removing member')
  }
}

/**
 * Deletes the current budget.
 */
const handleDeleteBudget = async () => {
  if (!budgetStore.currentBudget) return

  try {
    await budgetsAPI.delete(budgetStore.currentBudget.id)
    message.success('Budget deleted')
    router.push('/dashboard')
  } catch (error: any) {
    console.error('Error deleting budget:', error)
    if (error.response?.status === 403) {
      message.error('You must be an owner to delete')
    } else {
      message.error('Error deleting budget')
    }
  }
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  const budgetId = route.params.id as string

  try {
    await Promise.all([
      budgetStore.fetchBudget(budgetId),
      budgetStore.fetchCategories(budgetId),
      budgetStore.fetchTransactions(budgetId),
    ])
    await loadMembers()
  } catch (error) {
    console.error('Error loading budget:', error)
    message.error('Error loading data')
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

/**
 * Categories with calculated spending amounts.
 * Computes spent, remaining, and percentage for each category.
 */
const categoriesWithSpent = computed(() => {
  return budgetStore.categories.map(cat => {
    const spent = budgetStore.transactions
      .filter(t => t.category_id === cat.id && t.transaction_type === 'expense')
      .reduce((sum, t) => sum + t.amount, 0)

    const remaining = cat.amount - spent
    const percentage = cat.amount > 0 ? (spent / cat.amount) * 100 : 0

    return {
      ...cat,
      spent,
      remaining,
      percentage,
    }
  })
})

/** Total budget amount from all categories */
const totalBudget = computed(() => {
  return budgetStore.categories.reduce((sum, cat) => sum + cat.amount, 0)
})

/** Total amount spent across all categories */
const totalSpent = computed(() => {
  return categoriesWithSpent.value.reduce((sum, cat) => sum + cat.spent, 0)
})

/** Remaining budget amount */
const remaining = computed(() => totalBudget.value - totalSpent.value)

/** Spending percentage of total budget */
const percentage = computed(() => {
  return totalBudget.value > 0 ? (totalSpent.value / totalBudget.value) * 100 : 0
})

/**
 * Adds a new category to the budget.
 */
const handleAddCategory = async () => {
  if (!newCategory.value.name || newCategory.value.amount <= 0) {
    message.error('Please fill in all fields')
    return
  }

  addingCategory.value = true
  try {
    const budgetId = route.params.id as string
    await budgetStore.createCategory(
      budgetId,
      newCategory.value.name,
      newCategory.value.amount
    )
    message.success('Category added!')
    showAddCategory.value = false
    newCategory.value = { name: '', amount: 0 }
  } catch (error) {
    console.error('Error adding category:', error)
    message.error('Error adding category')
  } finally {
    addingCategory.value = false
  }
}
</script>