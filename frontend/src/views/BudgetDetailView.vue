<!--
  Budget Detail View - Displays detailed budget information
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

        <n-popconfirm @positive-click="handleDeleteBudget">
          <template #trigger>
            <n-button type="error" ghost>Delete Budget</n-button>
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
      <BudgetSummaryCard
        :total-income="totalIncome"
        :total-income-received="totalIncomeReceived"
        :total-budget="totalBudget"
        :total-spent="totalSpent"
        :remaining="remaining"
        :remaining-from-income="remainingFromIncome"
        :percentage="percentage"
        :balance="balance"
        :total-projected="totalProjected"
        :projected-remaining="projectedRemaining"
        :projected-remaining-from-income="projectedRemainingFromIncome"
        :projected-percentage="projectedPercentage"
        :tag-chart-data="tagChartData"
        :is-mobile="isMobile"
      />

      <!-- Balances (group budgets only) -->
      <BalancesCard
        v-if="budgetStore.currentBudget?.budget_type === 'group'"
        :balances="balances"
        :is-mobile="isMobile"
      />

      <!-- Tag Statistics -->
      <TagStatisticsCard :tag-distribution="tagDistribution" />

      <!-- Income Categories -->
      <n-card v-if="incomeCategories.length > 0" title="Revenus">
        <n-space vertical size="large">
          <CategoryCard
            v-for="category in incomeCategories"
            :key="category.id"
            :category="category"
            :subcategories="getSubcategories(category.id)"
            :members="members"
            :is-group-budget="budgetStore.currentBudget?.budget_type === 'group'"
            @edit="openEditModal"
            @delete="handleDeleteCategory"
            @add-subcategory="openAddSubcategory"
          />
        </n-space>
      </n-card>

      <!-- Expense Categories -->
      <n-card title="Dépenses">
        <n-empty v-if="expenseCategories.length === 0" description="Aucune catégorie">
          <template #extra>
            <n-button @click="showAddCategory = true" type="primary" size="small">
              Ajouter une catégorie
            </n-button>
          </template>
        </n-empty>

        <n-space v-else vertical size="large">
          <CategoryCard
            v-for="category in expenseCategories"
            :key="category.id"
            :category="category"
            :subcategories="getSubcategories(category.id)"
            :members="members"
            :is-group-budget="budgetStore.currentBudget?.budget_type === 'group'"
            @edit="openEditModal"
            @delete="handleDeleteCategory"
            @add-subcategory="openAddSubcategory"
          />
        </n-space>

        <template #footer>
          <n-button @click="showAddCategory = true" type="primary" size="small">
            Ajouter une catégorie
          </n-button>
        </template>
      </n-card>

      <!-- Members (group budgets only) -->
      <MembersCard
        v-if="budgetStore.currentBudget?.budget_type === 'group'"
        :members="members"
        :is-owner="isOwner"
        :updating-share-id="updatingShare"
        @update-share="handleUpdateShare"
        @remove-member="handleRemoveMember"
        @invite="showInviteModal = true"
      />
    </template>

    <!-- Modals -->
    <AddCategoryModal
      v-model:show="showAddCategory"
      :is-mobile="isMobile"
      :parent-category-options="parentCategoryOptions"
      :loading="addingCategory"
      :initial-parent-id="initialParentId"
      :max-amount="addCategoryMaxAmount"
      ref="addCategoryModalRef"
      @submit="handleAddCategory"
    />

    <EditCategoryModal
      v-model:show="showEditCategory"
      :is-mobile="isMobile"
      :loading="editingCategory"
      :category="editCategoryData"
      :max-amount="editCategoryMaxAmount"
      @submit="handleEditCategory"
    />

    <InviteMemberModal
      v-model:show="showInviteModal"
      :is-mobile="isMobile"
      :loading="inviting"
      ref="inviteModalRef"
      @submit="handleInviteMember"
    />
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NSpace, NButton, NDatePicker, NCard, NEmpty, NSpin, NPopconfirm, useMessage
} from 'naive-ui'
import { useBudgetStore } from '@/stores/budget'
import { useAuthStore } from '@/stores/auth'
import { budgetMembersAPI, budgetsAPI, recurringAPI, type BudgetMemberWithUser, type MemberBalance } from '@/services/api'

// Components
import { BudgetSummaryCard, BalancesCard, TagStatisticsCard, CategoryCard, MembersCard } from '@/components/budget'
import { AddCategoryModal, EditCategoryModal, InviteMemberModal } from '@/components/modals'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const budgetStore = useBudgetStore()
const authStore = useAuthStore()

// Refs
const isMobile = ref(false)
const selectedMonth = ref(Date.now())
const showAddCategory = ref(false)
const addingCategory = ref(false)
const showEditCategory = ref(false)
const editingCategory = ref(false)
const showInviteModal = ref(false)
const inviting = ref(false)
const members = ref<BudgetMemberWithUser[]>([])
const balances = ref<MemberBalance[]>([])
const updatingShare = ref<string | null>(null)
const initialParentId = ref<string | null>(null)
const addCategoryModalRef = ref<any>(null)
const inviteModalRef = ref<any>(null)

const editCategoryData = ref<{
  id: string
  name: string
  amount: number
  tags: string[]
  isSubcategory: boolean
  parentId?: string | null
} | null>(null)

// Computed for max amount in modals
const addCategoryMaxAmount = computed(() => {
  return getAvailableBudget(initialParentId.value)
})

const editCategoryMaxAmount = computed(() => {
  if (!editCategoryData.value?.parentId) return undefined
  return getAvailableBudget(editCategoryData.value.parentId, editCategoryData.value.id)
})

// Computed
const isOwner = computed(() => {
  if (!authStore.user || !budgetStore.currentBudget) return false
  if (budgetStore.currentBudget.budget_type === 'personal') {
    return budgetStore.currentBudget.user_id === authStore.user.id
  }
  return members.value.some(m => m.user_id === authStore.user!.id && m.role === 'owner')
})

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

// Category calculations
const getSubcategoryIds = (parentId: string): string[] => {
  return budgetStore.categories.filter(c => c.parent_id === parentId).map(c => c.id)
}

const getAvailableBudget = (parentId: string | null, excludeCategoryId?: string): number | undefined => {
  if (!parentId) return undefined
  const parent = budgetStore.categories.find(c => c.id === parentId)
  if (!parent) return 0
  const subcategories = budgetStore.categories.filter(c =>
    c.parent_id === parentId && c.id !== excludeCategoryId
  )
  const usedBudget = subcategories.reduce((sum, c) => sum + c.amount, 0)
  return parent.amount - usedBudget
}

const getProjectedRecurring = (categoryIds: string[], isIncome: boolean = false): number => {
  const now = new Date()
  const currentDay = now.getDate()
  const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
  const daysRemaining = lastDayOfMonth - currentDay
  const transactionType = isIncome ? 'income' : 'expense'

  return budgetStore.recurringTransactions
    .filter(r => categoryIds.includes(r.category_id) && r.active && r.transaction_type === transactionType)
    .reduce((sum, r) => {
      let occurrences = 0
      if (r.frequency === 'monthly') {
        const recurringDay = r.day || 1
        if (recurringDay > currentDay && recurringDay <= lastDayOfMonth) occurrences = 1
      } else if (r.frequency === 'weekly') {
        occurrences = Math.floor(daysRemaining / 7)
      }
      return sum + (r.amount * occurrences)
    }, 0)
}

const categoriesWithSpent = computed(() => {
  return budgetStore.categories.map(cat => {
    // Check if this is an income category (has "revenu" tag)
    const isIncome = cat.tags?.includes('revenu')
    // For income categories, count income transactions; for expense categories, count expense transactions
    const transactionType = isIncome ? 'income' : 'expense'

    let spent: number, projected: number

    if (!cat.parent_id) {
      const subcategoryIds = getSubcategoryIds(cat.id)
      const allCategoryIds = [cat.id, ...subcategoryIds]
      spent = budgetStore.transactions
        .filter(t => allCategoryIds.includes(t.category_id) && t.transaction_type === transactionType)
        .reduce((sum, t) => sum + t.amount, 0)
      projected = spent + getProjectedRecurring(allCategoryIds, isIncome)
    } else {
      // For subcategories, inherit income status from parent
      const parent = budgetStore.categories.find(c => c.id === cat.parent_id)
      const parentIsIncome = parent?.tags?.includes('revenu')
      const subTransactionType = parentIsIncome ? 'income' : 'expense'
      spent = budgetStore.transactions
        .filter(t => t.category_id === cat.id && t.transaction_type === subTransactionType)
        .reduce((sum, t) => sum + t.amount, 0)
      projected = spent + getProjectedRecurring([cat.id], parentIsIncome)
    }

    const budget = cat.parent_id
      ? budgetStore.categories.find(c => c.id === cat.parent_id)?.amount || 0
      : cat.amount

    return {
      ...cat,
      spent,
      projected,
      remaining: cat.parent_id ? 0 : cat.amount - spent,
      projectedRemaining: cat.parent_id ? 0 : cat.amount - projected,
      percentage: budget > 0 ? (spent / budget) * 100 : 0,
      projectedPercentage: budget > 0 ? (projected / budget) * 100 : 0,
      isIncome: isIncome || false,
    }
  })
})

const parentCategories = computed(() => categoriesWithSpent.value.filter(c => !c.parent_id))
const getSubcategories = (parentId: string) => categoriesWithSpent.value.filter(c => c.parent_id === parentId)

// Separate income (revenu) from expenses
const isIncomeCategory = (cat: { tags?: string[] }) => cat.tags?.includes('revenu')
const incomeCategories = computed(() => parentCategories.value.filter(c => isIncomeCategory(c)))
const expenseCategories = computed(() => parentCategories.value.filter(c => !isIncomeCategory(c)))

const parentCategoryOptions = computed(() => {
  return parentCategories.value.map(c => ({ label: c.name, value: c.id }))
})

// Income totals (expected/budgeted)
const totalIncome = computed(() => {
  return incomeCategories.value.reduce((sum, cat) => sum + cat.amount, 0)
})

// Income actually received (from income transactions)
const totalIncomeReceived = computed(() => {
  return incomeCategories.value.reduce((sum, cat) => sum + cat.spent, 0)
})

// Budget totals (expenses only)
const totalBudget = computed(() => {
  return expenseCategories.value.reduce((sum, cat) => sum + cat.amount, 0)
})

const totalSpent = computed(() => {
  return expenseCategories.value.reduce((sum, cat) => sum + cat.spent, 0)
})

const totalProjected = computed(() => {
  return expenseCategories.value.reduce((sum, cat) => sum + cat.projected, 0)
})

// Remaining compared to expense budget
const remaining = computed(() => totalBudget.value - totalSpent.value)
// Remaining compared to actual income received
const remainingFromIncome = computed(() => totalIncomeReceived.value - totalSpent.value)

const projectedRemaining = computed(() => totalBudget.value - totalProjected.value)
const projectedRemainingFromIncome = computed(() => totalIncomeReceived.value - totalProjected.value)

const percentage = computed(() => totalBudget.value > 0 ? (totalSpent.value / totalBudget.value) * 100 : 0)
const projectedPercentage = computed(() => totalBudget.value > 0 ? (totalProjected.value / totalBudget.value) * 100 : 0)

// Balance (expected income - expected expenses)
const balance = computed(() => totalIncome.value - totalBudget.value)

// Tag statistics
const VALID_TAGS = ['crédit', 'besoin', 'loisir', 'épargne']
const TAG_COLORS: Record<string, string> = {
  'crédit': '#d03050',
  'besoin': '#f0a020',
  'loisir': '#2080f0',
  'épargne': '#18a058',
}

const tagStatistics = computed(() => {
  return VALID_TAGS.map(tag => {
    const categoriesWithTag = categoriesWithSpent.value.filter(c => c.tags?.includes(tag))
    const budget = categoriesWithTag.filter(c => !c.parent_id).reduce((sum, c) => sum + c.amount, 0)
    const spent = categoriesWithTag.reduce((sum, c) => sum + c.spent, 0)
    return { tag, budget, spent, remaining: budget - spent, percentage: budget > 0 ? (spent / budget) * 100 : 0 }
  }).filter(stat => stat.budget > 0 || stat.spent > 0)
})

const tagDistribution = computed(() => {
  const stats = tagStatistics.value
  const totalBudgetByTags = stats.reduce((sum, s) => sum + s.budget, 0)
  return stats
    .filter(s => s.budget > 0)
    .map(s => ({ ...s, distributionPercent: totalBudgetByTags > 0 ? (s.budget / totalBudgetByTags) * 100 : 0 }))
    .sort((a, b) => b.distributionPercent - a.distributionPercent)
})

const tagChartData = computed(() => ({
  labels: tagStatistics.value.map(s => s.tag),
  datasets: [{
    data: tagStatistics.value.map(s => s.spent),
    backgroundColor: tagStatistics.value.map(s => TAG_COLORS[s.tag] || '#888888'),
    borderWidth: 2,
    borderColor: '#1a1a1a',
  }]
}))

// Handlers
const loadMembers = async () => {
  if (!budgetStore.currentBudget || budgetStore.currentBudget.budget_type !== 'group') return
  try {
    members.value = await budgetMembersAPI.getMembers(budgetStore.currentBudget.id)
  } catch (error) {
    console.error('Error loading members:', error)
  }
}

const loadBalances = async () => {
  if (!budgetStore.currentBudget || budgetStore.currentBudget.budget_type !== 'group') return
  try {
    balances.value = await budgetMembersAPI.getBalances(budgetStore.currentBudget.id)
  } catch (error) {
    console.error('Error loading balances:', error)
  }
}

const handleUpdateShare = async (memberId: string, share: number) => {
  if (!budgetStore.currentBudget) return
  updatingShare.value = memberId
  try {
    const updated = await budgetMembersAPI.updateShare(budgetStore.currentBudget.id, memberId, share)
    const index = members.value.findIndex(m => m.id === memberId)
    if (index !== -1) members.value[index] = updated
    await loadBalances()
    message.success('Share updated')
  } catch (error: any) {
    message.error(error.response?.status === 403 ? 'Only owners can update shares' : 'Error updating share')
  } finally {
    updatingShare.value = null
  }
}

const handleInviteMember = async (data: { email: string; role: 'member' | 'owner' }) => {
  if (!data.email || !budgetStore.currentBudget) {
    message.error('Email is required')
    return
  }
  inviting.value = true
  try {
    await budgetMembersAPI.inviteMember(budgetStore.currentBudget.id, data.email, data.role)
    message.success('Invitation sent!')
    showInviteModal.value = false
    inviteModalRef.value?.resetForm()
  } catch (error: any) {
    const status = error.response?.status
    if (status === 404) message.error('User not found')
    else if (status === 409) message.error('This user is already a member')
    else if (status === 403) message.error('You must be an owner to invite')
    else message.error('Error sending invitation')
  } finally {
    inviting.value = false
  }
}

const handleRemoveMember = async (memberId: string) => {
  if (!budgetStore.currentBudget) return
  try {
    await budgetMembersAPI.removeMember(budgetStore.currentBudget.id, memberId)
    message.success('Member removed')
    await loadMembers()
  } catch (error) {
    message.error('Error removing member')
  }
}

const handleDeleteBudget = async () => {
  if (!budgetStore.currentBudget) return
  try {
    await budgetsAPI.delete(budgetStore.currentBudget.id)
    message.success('Budget deleted')
    router.push('/dashboard')
  } catch (error: any) {
    message.error(error.response?.status === 403 ? 'You must be an owner to delete' : 'Error deleting budget')
  }
}

const openAddSubcategory = (parentId: string) => {
  initialParentId.value = parentId
  showAddCategory.value = true
}

const openEditModal = (category: any) => {
  editCategoryData.value = {
    id: category.id,
    name: category.name,
    amount: category.amount,
    tags: category.tags || [],
    isSubcategory: !!category.parent_id,
    parentId: category.parent_id,
  }
  showEditCategory.value = true
}

const handleAddCategory = async (data: { name: string; amount: number; parentId: string | null; tags: string[]; isSubcategory: boolean }) => {
  if (!data.name) {
    message.error('Please enter a name')
    return
  }
  if (data.isSubcategory && !data.parentId) {
    message.error('Please select a parent category')
    return
  }
  addingCategory.value = true
  try {
    const budgetId = route.params.id as string
    await budgetStore.createCategory(budgetId, data.name, data.amount, data.parentId || undefined, data.tags)
    message.success(data.isSubcategory ? 'Subcategory added!' : 'Category added!')
    showAddCategory.value = false
    initialParentId.value = null
    addCategoryModalRef.value?.resetForm()
  } catch (error) {
    message.error('Error adding category')
  } finally {
    addingCategory.value = false
  }
}

const handleEditCategory = async (data: { id: string; name: string; amount: number; tags: string[]; isSubcategory: boolean }) => {
  if (!data.name) {
    message.error('Please enter a name')
    return
  }
  editingCategory.value = true
  try {
    const updateData: { name?: string; amount?: number; tags?: string[] } = {
      name: data.name,
      amount: data.amount,
      tags: data.tags || []
    }
    await budgetStore.updateCategory(data.id, updateData)
    message.success('Category updated!')
    showEditCategory.value = false
  } catch (error) {
    message.error('Error updating category')
  } finally {
    editingCategory.value = false
  }
}

const handleDeleteCategory = async (categoryId: string) => {
  try {
    await budgetStore.deleteCategory(categoryId)
    message.success('Category deleted!')
  } catch (error: any) {
    if (error.response?.data?.detail?.includes('subcategories')) {
      message.error('Delete subcategories first')
    } else {
      message.error('Error deleting category')
    }
  }
}

// Lifecycle
onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  const budgetId = route.params.id as string
  try {
    await recurringAPI.process(budgetId)
    await Promise.all([
      budgetStore.fetchBudget(budgetId),
      budgetStore.fetchCategories(budgetId),
      budgetStore.fetchTransactions(budgetId),
      budgetStore.fetchRecurringTransactions(budgetId),
    ])
    await loadMembers()
    await loadBalances()
  } catch (error) {
    message.error('Error loading data')
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>
