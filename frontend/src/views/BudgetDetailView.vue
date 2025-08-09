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
                :percentage="Math.min(percentage, 100)"
                :color="percentage > 100 ? '#d03050' : '#18a058'"
                :style="{ width: isMobile ? '80px' : '100px' }"
              >
                {{ percentage.toFixed(2) }}%
              </n-progress>
            </div>
          </n-gi>
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
          <n-gi :span="isMobile ? 2 : 1">
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
        </n-grid>
      </n-card>

      <!-- Tag Statistics -->
      <n-card v-if="tagStatistics.length > 0" title="Statistics by Tag">
        <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
          <n-gi v-for="stat in tagStatistics" :key="stat.tag">
            <n-card size="small" :style="{ borderLeft: `3px solid ${getTagColor(stat.tag)}` }">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <n-tag :type="getTagType(stat.tag)" size="small">{{ stat.tag }}</n-tag>
                <span style="font-size: 12px; color: #888;">{{ stat.percentage.toFixed(2) }}%</span>
              </div>
              <div style="font-size: 14px; font-weight: bold; margin-bottom: 4px;">
                {{ stat.spent.toFixed(2) }} / {{ stat.budget.toFixed(2) }} €
              </div>
              <n-progress
                :percentage="Math.min(stat.percentage, 100)"
                :color="stat.percentage > 100 ? '#d03050' : getTagColor(stat.tag)"
                :show-indicator="false"
                :height="6"
              />
              <div
                style="font-size: 11px; margin-top: 4px;"
                :style="{ color: stat.remaining >= 0 ? '#18a058' : '#d03050' }"
              >
                {{ stat.remaining >= 0 ? 'Remaining' : 'Over' }}: {{ Math.abs(stat.remaining).toFixed(2) }} €
              </div>
            </n-card>
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

        <n-space v-else vertical size="large">
          <n-card v-for="category in parentCategories" :key="category.id" size="small">
            <!-- Parent Category Header -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
              <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                  <strong style="font-size: 16px;">{{ category.name }}</strong>
                  <n-space v-if="category.tags && category.tags.length > 0" size="small">
                    <n-tag v-for="tag in category.tags" :key="tag" size="small" :type="getTagType(tag)">
                      {{ tag }}
                    </n-tag>
                  </n-space>
                </div>
                <div style="font-size: 13px; color: #888;">
                  Budget: <strong>{{ category.amount.toFixed(2) }} €</strong>
                </div>
              </div>
              <n-space size="small">
                <n-button size="tiny" quaternary @click="openEditModal(category)">Edit</n-button>
                <n-popconfirm @positive-click="handleDeleteCategory(category.id)">
                  <template #trigger>
                    <n-button size="tiny" quaternary type="error">Delete</n-button>
                  </template>
                  Delete this category?
                </n-popconfirm>
              </n-space>
            </div>

            <!-- Progress Bars -->
            <div style="margin-bottom: 8px;">
              <!-- Spent -->
              <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                <span>Spent: {{ category.spent.toFixed(2) }} € ({{ category.percentage.toFixed(2) }}%)</span>
                <span :style="{ color: category.remaining >= 0 ? '#18a058' : '#d03050' }">
                  {{ category.remaining.toFixed(2) }} € remaining
                </span>
              </div>
              <n-progress
                :percentage="Math.min(category.percentage, 100)"
                :color="category.percentage > 100 ? '#d03050' : '#18a058'"
                :show-indicator="false"
              />
              <!-- Projected -->
              <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; margin-top: 8px;">
                <span style="color: #f0a020;">Projected: {{ category.projected.toFixed(2) }} € ({{ category.projectedPercentage.toFixed(2) }}%)</span>
                <span :style="{ color: category.projectedRemaining >= 0 ? '#18a058' : '#d03050' }">
                  {{ category.projectedRemaining.toFixed(2) }} € remaining
                </span>
              </div>
              <n-progress
                :percentage="Math.min(category.projectedPercentage, 100)"
                :color="category.projectedPercentage > 100 ? '#d03050' : '#f0a020'"
                :show-indicator="false"
              />
            </div>

            <!-- Subcategories -->
            <div v-if="getSubcategories(category.id).length > 0" style="margin-top: 16px;">
              <div style="font-size: 12px; color: #888; margin-bottom: 8px;">SUBCATEGORIES</div>
              <n-space vertical size="small">
                <div
                  v-for="sub in getSubcategories(category.id)"
                  :key="sub.id"
                  style="background: rgba(255,255,255,0.05); border-radius: 6px; padding: 10px 12px;"
                >
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span style="font-size: 14px;">{{ sub.name }}</span>
                      <n-space v-if="sub.tags && sub.tags.length > 0" size="small">
                        <n-tag v-for="tag in sub.tags" :key="tag" size="tiny" :type="getTagType(tag)">
                          {{ tag }}
                        </n-tag>
                      </n-space>
                    </div>
                    <n-space size="small" align="center">
                      <n-button size="tiny" quaternary @click="openEditModal(sub)">Edit</n-button>
                      <n-popconfirm @positive-click="handleDeleteCategory(sub.id)">
                        <template #trigger>
                          <n-button size="tiny" quaternary type="error">Del</n-button>
                        </template>
                        Delete?
                      </n-popconfirm>
                    </n-space>
                  </div>
                  <div style="display: flex; gap: 16px; font-size: 12px;">
                    <span style="color: #18a058;">Spent: {{ sub.spent.toFixed(2) }} €</span>
                    <span style="color: #f0a020;">Projected: {{ sub.projected.toFixed(2) }} €</span>
                  </div>
                </div>
              </n-space>
            </div>

            <!-- Add Subcategory Button -->
            <div style="margin-top: 12px;">
              <n-button size="small" dashed block @click="openAddSubcategory(category.id)">
                + Add Subcategory
              </n-button>
            </div>
          </n-card>
        </n-space>

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
        title="Add Category"
        :bordered="false"
        size="huge"
        role="dialog"
        :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
      >
        <n-form ref="categoryFormRef" :model="newCategory">
          <n-form-item label="Type">
            <n-radio-group v-model:value="newCategory.isSubcategory">
              <n-space>
                <n-radio :value="false">Category</n-radio>
                <n-radio :value="true">Subcategory</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>

          <n-form-item v-if="newCategory.isSubcategory" label="Parent Category">
            <n-select
              v-model:value="newCategory.parentId"
              :options="parentCategoryOptions"
              placeholder="Select parent category"
            />
          </n-form-item>

          <n-form-item label="Name">
            <n-input v-model:value="newCategory.name" placeholder="Housing" />
          </n-form-item>

          <n-form-item v-if="!newCategory.isSubcategory" label="Budget Amount">
            <n-input-number
              v-model:value="newCategory.amount"
              :min="0"
              :precision="2"
              style="width: 100%;"
            >
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>

          <n-form-item label="Tags">
            <n-checkbox-group v-model:value="newCategory.tags">
              <n-space>
                <n-checkbox value="crédit">Crédit</n-checkbox>
                <n-checkbox value="besoin">besoin</n-checkbox>
                <n-checkbox value="loisir">Loisir</n-checkbox>
                <n-checkbox value="épargne">Épargne</n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="closeAddModal">Cancel</n-button>
            <n-button type="primary" :loading="addingCategory" @click="handleAddCategory">
              Add
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- Edit category modal -->
    <n-modal v-model:show="showEditCategory">
      <n-card
        title="Edit Category"
        :bordered="false"
        size="huge"
        role="dialog"
        :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
      >
        <n-form :model="editCategory">
          <n-form-item label="Name">
            <n-input v-model:value="editCategory.name" placeholder="Category name" />
          </n-form-item>

          <n-form-item v-if="!editCategory.isSubcategory" label="Budget Amount">
            <n-input-number
              v-model:value="editCategory.amount"
              :min="0"
              :precision="2"
              style="width: 100%;"
            >
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>

          <n-form-item label="Tags">
            <n-checkbox-group v-model:value="editCategory.tags">
              <n-space>
                <n-checkbox value="crédit">Crédit</n-checkbox>
                <n-checkbox value="besoin">besoin</n-checkbox>
                <n-checkbox value="loisir">Loisir</n-checkbox>
                <n-checkbox value="épargne">Épargne</n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showEditCategory = false">Cancel</n-button>
            <n-button type="primary" :loading="editingCategory" @click="handleEditCategory">
              Save
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
  NCheckbox, NCheckboxGroup, NSelect, NDivider,
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
  parentId: null as string | null,
  tags: [] as string[],
  isSubcategory: false,
})

/** Edit category modal visibility */
const showEditCategory = ref(false)

/** Loading state for editing category */
const editingCategory = ref(false)

/** Edit category form data */
const editCategory = ref({
  id: '',
  name: '',
  amount: 0,
  tags: [] as string[],
  isSubcategory: false,
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
      budgetStore.fetchRecurringTransactions(budgetId),
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
 * Get all subcategory IDs for a parent category.
 */
const getSubcategoryIds = (parentId: string): string[] => {
  return budgetStore.categories
    .filter(c => c.parent_id === parentId)
    .map(c => c.id)
}

/**
 * Calculate projected recurring expenses for a category until end of month.
 */
const getProjectedRecurring = (categoryIds: string[]): number => {
  const now = new Date()
  const currentDay = now.getDate()
  const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
  const daysRemaining = lastDayOfMonth - currentDay

  return budgetStore.recurringTransactions
    .filter(r => categoryIds.includes(r.category_id) && r.active && r.transaction_type === 'expense')
    .reduce((sum, r) => {
      let occurrences = 0

      if (r.frequency === 'monthly') {
        // Check if the recurring day is still coming this month
        const recurringDay = r.day || 1
        if (recurringDay > currentDay && recurringDay <= lastDayOfMonth) {
          occurrences = 1
        }
      } else if (r.frequency === 'weekly') {
        // Calculate how many weeks remain
        occurrences = Math.floor(daysRemaining / 7)
      } else if (r.frequency === 'yearly') {
        // Yearly transactions are rare within a month, skip for projection
        occurrences = 0
      }

      return sum + (r.amount * occurrences)
    }, 0)
}

/**
 * Categories with calculated spending amounts.
 * For parent categories: includes spending from all subcategories.
 * For subcategories: only their own spending.
 */
const categoriesWithSpent = computed(() => {
  return budgetStore.categories.map(cat => {
    let spent: number
    let projected: number

    if (!cat.parent_id) {
      // Parent category: sum spending from self + all subcategories
      const subcategoryIds = getSubcategoryIds(cat.id)
      const allCategoryIds = [cat.id, ...subcategoryIds]
      spent = budgetStore.transactions
        .filter(t => allCategoryIds.includes(t.category_id) && t.transaction_type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0)
      projected = spent + getProjectedRecurring(allCategoryIds)
    } else {
      // Subcategory: only own spending
      spent = budgetStore.transactions
        .filter(t => t.category_id === cat.id && t.transaction_type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0)
      projected = spent + getProjectedRecurring([cat.id])
    }

    // For subcategories, use parent's budget for percentage calc
    const budget = cat.parent_id
      ? budgetStore.categories.find(c => c.id === cat.parent_id)?.amount || 0
      : cat.amount

    const remaining = cat.parent_id ? 0 : cat.amount - spent
    const projectedRemaining = cat.parent_id ? 0 : cat.amount - projected
    const percentage = budget > 0 ? (spent / budget) * 100 : 0
    const projectedPercentage = budget > 0 ? (projected / budget) * 100 : 0

    return {
      ...cat,
      spent,
      projected,
      remaining,
      projectedRemaining,
      percentage,
      projectedPercentage,
    }
  })
})

/** Total budget amount from parent categories only */
const totalBudget = computed(() => {
  return budgetStore.categories
    .filter(cat => !cat.parent_id)
    .reduce((sum, cat) => sum + cat.amount, 0)
})

/** Total amount spent (only count parent categories to avoid double counting) */
const totalSpent = computed(() => {
  return categoriesWithSpent.value
    .filter(cat => !cat.parent_id)
    .reduce((sum, cat) => sum + cat.spent, 0)
})

/** Total projected spending */
const totalProjected = computed(() => {
  return categoriesWithSpent.value
    .filter(cat => !cat.parent_id)
    .reduce((sum, cat) => sum + cat.projected, 0)
})

/** Remaining budget amount */
const remaining = computed(() => totalBudget.value - totalSpent.value)

/** Projected remaining budget amount */
const projectedRemaining = computed(() => totalBudget.value - totalProjected.value)

/** Spending percentage of total budget */
const percentage = computed(() => {
  return totalBudget.value > 0 ? (totalSpent.value / totalBudget.value) * 100 : 0
})

/** Projected spending percentage of total budget */
const projectedPercentage = computed(() => {
  return totalBudget.value > 0 ? (totalProjected.value / totalBudget.value) * 100 : 0
})

/** Available tags */
const VALID_TAGS = ['crédit', 'besoin', 'loisir', 'épargne']

/**
 * Statistics per tag.
 * For each tag, calculates the total budget and spent amounts
 * from all categories that have that tag.
 */
const tagStatistics = computed(() => {
  return VALID_TAGS.map(tag => {
    // Get all categories (parent + sub) that have this tag
    const categoriesWithTag = categoriesWithSpent.value.filter(c =>
      c.tags && c.tags.includes(tag)
    )

    // Sum budgets (only from parent categories to avoid counting parent budget twice)
    const budget = categoriesWithTag
      .filter(c => !c.parent_id)
      .reduce((sum, c) => sum + c.amount, 0)

    // Sum spending from all categories with this tag
    const spent = categoriesWithTag.reduce((sum, c) => sum + c.spent, 0)

    const percentage = budget > 0 ? (spent / budget) * 100 : 0

    return {
      tag,
      budget,
      spent,
      remaining: budget - spent,
      percentage,
    }
  }).filter(stat => stat.budget > 0 || stat.spent > 0) // Only show tags that have data
})

/**
 * Parent categories (categories without parent_id).
 */
const parentCategories = computed(() => {
  return categoriesWithSpent.value.filter(c => !c.parent_id)
})

/**
 * Options for parent category select in add modal.
 */
const parentCategoryOptions = computed(() => {
  return parentCategories.value.map(c => ({
    label: c.name,
    value: c.id,
  }))
})

/**
 * Get subcategories for a parent category.
 */
const getSubcategories = (parentId: string) => {
  return categoriesWithSpent.value.filter(c => c.parent_id === parentId)
}

/**
 * Get tag color type.
 */
const getTagType = (tag: string) => {
  const types: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
    'crédit': 'error',
    'obligé': 'warning',
    'loisir': 'info',
    'épargne': 'success',
  }
  return types[tag] || 'default'
}

/**
 * Open add subcategory modal.
 */
const openAddSubcategory = (parentId: string) => {
  newCategory.value = { name: '', amount: 0, parentId, tags: [], isSubcategory: true }
  showAddCategory.value = true
}

/**
 * Close add modal and reset form.
 */
const closeAddModal = () => {
  showAddCategory.value = false
  newCategory.value = { name: '', amount: 0, parentId: null, tags: [], isSubcategory: false }
}

/**
 * Open edit modal for a category.
 */
const openEditModal = (category: any) => {
  editCategory.value = {
    id: category.id,
    name: category.name,
    amount: category.amount,
    tags: category.tags || [],
    isSubcategory: !!category.parent_id,
  }
  showEditCategory.value = true
}

/**
 * Adds a new category to the budget.
 */
const handleAddCategory = async () => {
  if (!newCategory.value.name) {
    message.error('Please enter a name')
    return
  }

  if (newCategory.value.isSubcategory && !newCategory.value.parentId) {
    message.error('Please select a parent category')
    return
  }

  addingCategory.value = true
  try {
    const budgetId = route.params.id as string
    const amount = newCategory.value.isSubcategory ? 0 : newCategory.value.amount
    const parentId = newCategory.value.isSubcategory ? newCategory.value.parentId : undefined

    await budgetStore.createCategory(
      budgetId,
      newCategory.value.name,
      amount,
      parentId || undefined,
      newCategory.value.tags
    )
    message.success(newCategory.value.isSubcategory ? 'Subcategory added!' : 'Category added!')
    closeAddModal()
  } catch (error) {
    console.error('Error adding category:', error)
    message.error('Error adding category')
  } finally {
    addingCategory.value = false
  }
}

/**
 * Edit an existing category.
 */
const handleEditCategory = async () => {
  if (!editCategory.value.name) {
    message.error('Please enter a name')
    return
  }

  editingCategory.value = true
  try {
    await budgetStore.updateCategory(editCategory.value.id, {
      name: editCategory.value.name,
      amount: editCategory.value.amount,
      tags: editCategory.value.tags,
    })
    message.success('Category updated!')
    showEditCategory.value = false
  } catch (error) {
    console.error('Error updating category:', error)
    message.error('Error updating category')
  } finally {
    editingCategory.value = false
  }
}

/**
 * Delete a category.
 */
const handleDeleteCategory = async (categoryId: string) => {
  try {
    await budgetStore.deleteCategory(categoryId)
    message.success('Category deleted!')
  } catch (error: any) {
    console.error('Error deleting category:', error)
    if (error.response?.data?.detail?.includes('subcategories')) {
      message.error('Delete subcategories first')
    } else {
      message.error('Error deleting category')
    }
  }
}
</script>
