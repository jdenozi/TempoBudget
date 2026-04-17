<template>
  <n-space vertical size="large">
    <!-- Loading -->
    <n-flex v-if="projectStore.loading && !projectStore.currentProject" justify="center" style="padding: 40px;">
      <n-spin size="large" />
    </n-flex>

    <template v-else-if="project">
      <!-- Header -->
      <n-flex justify="space-between" align="center" :wrap="true" :size="[16, 12]">
        <n-flex align="center" :size="12">
          <n-button text @click="router.push({ name: 'projects' })">
            <template #icon><ArrowBackOutline /></template>
          </n-button>
          <h1 class="project-title">{{ project.name }}</h1>
          <n-tag :type="statusTagType(project.status)" size="small">{{ t('project.' + project.status) }}</n-tag>
          <n-tag :type="project.mode === 'pro' ? 'info' : 'default'" size="small">{{ t('project.' + project.mode) }}</n-tag>
        </n-flex>
      </n-flex>

      <!-- Summary -->
      <n-card size="small">
        <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
          <n-gi>
            <n-popover v-if="project.categories.length > 0" trigger="hover" placement="bottom-start" :show-arrow="false">
              <template #trigger>
                <div class="stat-with-breakdown">
                  <n-statistic :label="t('project.totalBudget')" :value="project.total_budget.toFixed(2)">
                    <template #suffix>€</template>
                  </n-statistic>
                </div>
              </template>
              <div class="budget-breakdown">
                <div class="budget-breakdown-title">{{ t('project.budgetByCategory') }}</div>
                <div v-for="cat in project.categories" :key="cat.id" class="budget-breakdown-row">
                  <span>{{ cat.name }}</span>
                  <strong>{{ cat.planned_amount.toFixed(2) }} €</strong>
                </div>
                <div class="budget-breakdown-total">
                  <span>{{ t('common.total') }}</span>
                  <strong>{{ categoriesPlannedTotal.toFixed(2) }} €</strong>
                </div>
              </div>
            </n-popover>
            <n-statistic v-else :label="t('project.totalBudget')" :value="project.total_budget.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic :label="t('project.spent')" :value="project.total_spent.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi>
            <n-statistic :label="t('project.remaining')" :value="project.remaining.toFixed(2)">
              <template #prefix>
                <n-icon :color="project.remaining >= 0 ? '#18a058' : '#d03050'"><CashOutline /></n-icon>
              </template>
              <template #suffix>€</template>
            </n-statistic>
          </n-gi>
          <n-gi v-if="project.target_date">
            <div class="target-date-block">
              <div class="target-date-label">{{ t('project.targetDate') }}</div>
              <div class="target-date-value">{{ project.target_date }}</div>
            </div>
          </n-gi>
        </n-grid>
        <div class="summary-progress-wrapper">
          <n-flex justify="space-between" class="summary-progress-label">
            <span>{{ t('project.progress') }}</span>
            <strong>{{ project.total_budget > 0 ? ((project.total_spent / project.total_budget) * 100).toFixed(1) : '0.0' }}%</strong>
          </n-flex>
          <n-progress
            :percentage="project.total_budget > 0 ? Math.min((project.total_spent / project.total_budget) * 100, 100) : 0"
            :color="project.remaining < 0 ? '#d03050' : '#2080f0'"
            :show-indicator="false"
          />
        </div>
        <n-text v-if="project.description" depth="3" class="summary-description">
          {{ project.description }}
        </n-text>
      </n-card>

      <!-- Categories -->
      <n-card :title="t('project.categories')" size="small">
        <template #header-extra>
          <n-button size="small" type="primary" @click="openCategoryModal()">{{ t('project.addCategory') }}</n-button>
        </template>
        <template v-if="project.categories.length > 0">
          <div v-for="cat in project.categories" :key="cat.id" class="list-row">
            <div class="list-row-header list-row-header--clickable" @click="toggleCategory(cat.id)">
              <n-flex align="center" :size="6">
                <n-icon :component="expandedCategoryId === cat.id ? ChevronDownOutline : ChevronForwardOutline" />
                <strong>{{ cat.name }}</strong>
                <n-text depth="3">({{ categoryTransactions(cat.id).length }})</n-text>
              </n-flex>
              <n-flex align="center" :size="8" @click.stop>
                <n-text depth="3">
                  {{ cat.total_spent.toFixed(2) }}<span v-if="pendingPlannedAmount(cat.id) > 0" class="text-pending"> + {{ pendingPlannedAmount(cat.id).toFixed(2) }}</span> / {{ cat.planned_amount.toFixed(2) }} €
                </n-text>
                <n-button size="tiny" @click="openCategoryModal(cat)">{{ t('common.edit') }}</n-button>
                <n-popconfirm @positive-click="handleDeleteCategory(cat.id)">
                  <template #trigger>
                    <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
                  </template>
                  {{ t('project.deleteCategoryConfirm') }}
                </n-popconfirm>
              </n-flex>
            </div>
            <div class="multi-progress">
              <div class="multi-progress-segment" :style="{ width: categoryBar(cat).spentPct + '%', background: categoryBar(cat).overBudget ? 'var(--color-error)' : 'var(--color-success)' }" />
              <div class="multi-progress-segment" :style="{ width: categoryBar(cat).pendingPct + '%', background: 'var(--color-pending)' }" />
              <div v-if="categoryBar(cat).showBudgetMark" class="multi-progress-mark" :style="{ left: categoryBar(cat).budgetMarkPct + '%' }" />
            </div>
            <div v-if="expandedCategoryId === cat.id" class="category-tx-list">
              <template v-if="categoryTransactions(cat.id).length > 0">
                <div v-for="tx in categoryTransactions(cat.id)" :key="tx.id" class="sub-row">
                  <n-flex justify="space-between" align="center" :size="8" :wrap="true">
                    <n-flex align="center" :size="8">
                      <n-tag :type="tx.transaction_type === 'expense' ? 'error' : 'success'" size="small">
                        {{ tx.transaction_type === 'expense' ? '-' : '+' }}{{ tx.amount.toFixed(2) }} €
                      </n-tag>
                      <span>{{ tx.title }}</span>
                    </n-flex>
                    <n-flex align="center" :size="8">
                      <n-tag size="small" :type="tx.source === 'pro' ? 'info' : 'default'">{{ tx.source }}</n-tag>
                      <n-text depth="3">{{ tx.date }}</n-text>
                      <n-button size="tiny" @click="openTxEditModal(tx)">{{ t('common.edit') }}</n-button>
                    </n-flex>
                  </n-flex>
                </div>
              </template>
              <n-empty v-else :description="t('project.noLinkedTransactions')" size="small" />
            </div>
          </div>
          <div class="list-total">
            <span>{{ t('common.total') }}</span>
            <span>{{ categoriesSpentTotal.toFixed(2) }} / {{ categoriesPlannedTotal.toFixed(2) }} €</span>
          </div>
        </template>
        <n-empty v-else :description="t('project.noCategories')" />
      </n-card>

      <!-- Planned Expenses -->
      <n-card :title="t('project.plannedExpenses')" size="small">
        <template #header-extra>
          <n-button size="small" type="primary" @click="openExpenseModal()" :disabled="project.categories.length === 0">
            {{ t('project.addPlannedExpense') }}
          </n-button>
        </template>
        <template v-if="projectStore.plannedExpenses.length > 0">
          <div v-for="expense in projectStore.plannedExpenses" :key="expense.id" class="list-row">
            <n-flex justify="space-between" align="center" :size="8" :wrap="true">
              <n-flex align="center" :size="8">
                <strong>{{ expense.description }}</strong>
                <n-tag size="small" :type="expense.status === 'paid' ? 'success' : 'warning'">
                  {{ t('project.' + expense.status) }}
                </n-tag>
                <n-text depth="3" v-if="expense.category_name">{{ expense.category_name }}</n-text>
              </n-flex>
              <n-flex align="center" :size="8">
                <strong>{{ expense.amount.toFixed(2) }} €</strong>
                <n-text v-if="expense.due_date" depth="3">{{ expense.due_date }}</n-text>
                <n-button v-if="expense.status === 'pending'" size="tiny" type="success" @click="handleMarkPaid(expense.id)">
                  {{ t('project.markAsPaid') }}
                </n-button>
                <n-button size="tiny" @click="openExpenseModal(expense)">{{ t('common.edit') }}</n-button>
                <n-popconfirm @positive-click="handleDeleteExpense(expense.id)">
                  <template #trigger>
                    <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
                  </template>
                  {{ t('project.deletePlannedExpenseConfirm') }}
                </n-popconfirm>
              </n-flex>
            </n-flex>
          </div>
        </template>
        <n-empty v-else :description="t('project.noPlannedExpenses')" />
      </n-card>

      <!-- Linked Transactions -->
      <n-card :title="t('project.linkedTransactions')" size="small">
        <template v-if="projectStore.projectTransactions.length > 0">
          <div v-for="tx in projectStore.projectTransactions" :key="tx.id" class="list-row list-row--compact">
            <n-flex justify="space-between" align="center" :size="8" :wrap="true">
              <n-flex align="center" :size="8">
                <n-tag :type="tx.transaction_type === 'expense' ? 'error' : 'success'" size="small">
                  {{ tx.transaction_type === 'expense' ? '-' : '+' }}{{ tx.amount.toFixed(2) }} €
                </n-tag>
                <span>{{ tx.title }}</span>
                <n-text depth="3" v-if="tx.project_category_name">{{ tx.project_category_name }}</n-text>
              </n-flex>
              <n-flex align="center" :size="8">
                <n-tag size="small" :type="tx.source === 'pro' ? 'info' : 'default'">{{ tx.source }}</n-tag>
                <n-text depth="3">{{ tx.date }}</n-text>
                <n-button size="tiny" @click="openTxEditModal(tx)">{{ t('common.edit') }}</n-button>
              </n-flex>
            </n-flex>
          </div>
        </template>
        <n-empty v-else :description="t('project.noLinkedTransactions')" />
      </n-card>

      <!-- Members -->
      <n-card :title="t('project.members')" size="small">
        <template #header-extra>
          <n-button v-if="isOwner" size="small" type="primary" @click="showInviteModal = true">{{ t('project.inviteMember') }}</n-button>
        </template>
        <template v-if="projectStore.members.length > 0">
          <div v-for="member in projectStore.members" :key="member.id" class="list-row">
            <n-flex justify="space-between" align="center" :size="8" :wrap="true">
              <n-flex align="center" :size="8">
                <n-avatar v-if="member.user_avatar" :src="member.user_avatar" :size="28" round />
                <n-avatar v-else :size="28" round>{{ member.user_name.charAt(0).toUpperCase() }}</n-avatar>
                <strong>{{ member.user_name }}</strong>
                <n-text depth="3">{{ member.user_email }}</n-text>
                <n-tag :type="member.role === 'owner' ? 'success' : 'default'" size="small">{{ member.role }}</n-tag>
              </n-flex>
              <n-popconfirm v-if="isOwner && member.role !== 'owner'" @positive-click="handleRemoveMember(member.id)">
                <template #trigger>
                  <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
                </template>
                {{ t('project.removeMemberConfirm') }}
              </n-popconfirm>
            </n-flex>
          </div>
        </template>
        <n-empty v-else :description="t('project.noMembers')" />
      </n-card>
    </template>

    <!-- Invite Member Modal -->
    <n-modal v-model:show="showInviteModal" preset="card"
      :title="t('project.inviteMember')"
      :style="{ width: isMobile ? '90%' : '400px' }">
      <n-form>
        <n-form-item :label="t('project.inviteEmail')">
          <n-input v-model:value="inviteEmail" type="text" placeholder="email@example.com" />
        </n-form-item>
        <n-form-item :label="t('project.memberRole')">
          <n-radio-group v-model:value="inviteRole">
            <n-radio-button value="member">{{ t('project.roleMember') }}</n-radio-button>
            <n-radio-button value="owner">{{ t('project.roleOwner') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showInviteModal = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleInviteMember">{{ t('project.sendInvitation') }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Category Modal -->
    <n-modal v-model:show="showCategoryModal" preset="card"
      :title="editingCategory ? t('project.editCategory') : t('project.addCategory')"
      :style="{ width: isMobile ? '90%' : '400px' }">
      <n-form>
        <n-form-item :label="t('project.categoryName')">
          <n-input v-model:value="categoryForm.name" />
        </n-form-item>
        <n-form-item :label="t('project.plannedAmount')">
          <n-input-number v-model:value="categoryForm.planned_amount" :min="0" :precision="2" style="width: 100%">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCategoryModal = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveCategory">{{ t('common.save') }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Transaction Edit Modal -->
    <n-modal v-model:show="showTxEditModal" preset="card"
      :title="t('transaction.editTransaction')"
      :style="{ width: isMobile ? '90%' : '500px' }">
      <n-form>
        <n-form-item :label="t('transaction.transactionTitle')">
          <n-input v-model:value="txForm.title" />
        </n-form-item>
        <n-form-item :label="t('transaction.type')">
          <n-radio-group v-model:value="txForm.transaction_type">
            <n-radio-button value="expense">{{ t('transaction.expense') }}</n-radio-button>
            <n-radio-button value="income">{{ t('transaction.income') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('transaction.amount')">
          <n-input-number v-model:value="txForm.amount" :min="0.01" :precision="2" style="width: 100%">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('transaction.date')">
          <n-date-picker v-model:value="txForm.date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item :label="t('transaction.comment')">
          <n-input v-model:value="txForm.comment" type="textarea" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTxEditModal = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveTx">{{ t('common.save') }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Planned Expense Modal -->
    <n-modal v-model:show="showExpenseModal" preset="card"
      :title="editingExpense ? t('project.editPlannedExpense') : t('project.addPlannedExpense')"
      :style="{ width: isMobile ? '90%' : '500px' }">
      <n-form>
        <n-form-item :label="t('project.expenseDescription')">
          <n-input v-model:value="expenseForm.description" />
        </n-form-item>
        <n-form-item :label="t('project.plannedAmount')">
          <n-input-number v-model:value="expenseForm.amount" :min="0.01" :precision="2" style="width: 100%">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('project.categories')">
          <n-select v-model:value="expenseForm.project_category_id" :options="categoryOptions" />
        </n-form-item>
        <n-form-item :label="t('project.dueDate')">
          <n-date-picker v-model:value="expenseForm.due_date" type="date" style="width: 100%" clearable />
        </n-form-item>
        <n-form-item :label="t('project.reminderDate')">
          <n-date-picker v-model:value="expenseForm.reminder_date" type="date" style="width: 100%" clearable />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showExpenseModal = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveExpense">{{ t('common.save') }}</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NSpace, NFlex, NButton, NCard, NGrid, NGi, NStatistic, NText, NTag,
  NIcon, NSpin, NEmpty, NProgress, NModal, NForm, NFormItem,
  NInput, NInputNumber, NDatePicker, NSelect, NAvatar,
  NPopconfirm, NPopover, NRadioGroup, NRadioButton, useMessage,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { ArrowBackOutline, CashOutline, ChevronDownOutline, ChevronForwardOutline } from '@vicons/ionicons5'
import { useProjectStore } from '@/stores/project'
import { useMobileDetect } from '@/composables/useMobileDetect'
import { transactionsAPI, proTransactionsAPI } from '@/services/api'
import type { ProjectCategoryWithSpent, ProjectPlannedExpense, ProjectTransaction } from '@/services/api'

const { t } = useI18n()
const message = useMessage()
const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const { isMobile } = useMobileDetect()

import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const saving = ref(false)
const showCategoryModal = ref(false)
const showExpenseModal = ref(false)
const showInviteModal = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('member')
const editingCategory = ref<ProjectCategoryWithSpent | null>(null)
const editingExpense = ref<ProjectPlannedExpense | null>(null)
const editingTx = ref<ProjectTransaction | null>(null)
const showTxEditModal = ref(false)
const expandedCategoryId = ref<string | null>(null)

const txForm = ref({
  title: '',
  amount: 0 as number,
  transaction_type: 'expense' as 'expense' | 'income',
  date: null as number | null,
  comment: '',
})

const toggleCategory = (id: string) => {
  expandedCategoryId.value = expandedCategoryId.value === id ? null : id
}

const categoryTransactions = (categoryId: string) =>
  projectStore.projectTransactions.filter(tx => tx.project_category_id === categoryId)

const pendingPlannedAmount = (categoryId: string) =>
  projectStore.plannedExpenses
    .filter(e => e.project_category_id === categoryId && e.status === 'pending')
    .reduce((sum, e) => sum + e.amount, 0)

const categoryBar = (cat: ProjectCategoryWithSpent) => {
  const spent = cat.total_spent
  const pending = pendingPlannedAmount(cat.id)
  const planned = cat.planned_amount
  const total = spent + pending
  const denominator = Math.max(planned, total, 0.0001)
  const spentPct = (spent / denominator) * 100
  const pendingPct = (pending / denominator) * 100
  const overBudget = total > planned && planned > 0
  const showBudgetMark = overBudget && planned > 0
  const budgetMarkPct = showBudgetMark ? (planned / denominator) * 100 : 0
  return { spentPct, pendingPct, overBudget, showBudgetMark, budgetMarkPct }
}

const categoryForm = ref({ name: '', planned_amount: 0 as number })
const expenseForm = ref({
  description: '',
  amount: 0 as number,
  project_category_id: null as string | null,
  due_date: null as number | null,
  reminder_date: null as number | null,
})

const project = computed(() => projectStore.currentProject)

const categoryOptions = computed(() =>
  (project.value?.categories || []).map(c => ({ label: `${c.name} (${c.planned_amount.toFixed(2)} €)`, value: c.id }))
)

const categoriesPlannedTotal = computed(() =>
  (project.value?.categories || []).reduce((sum, c) => sum + c.planned_amount, 0)
)

const categoriesSpentTotal = computed(() =>
  (project.value?.categories || []).reduce((sum, c) => sum + c.total_spent, 0)
)

const statusTagType = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'abandoned') return 'error'
  return 'default'
}

const formatDate = (ts: number) => {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const projectId = computed(() => route.params.id as string)

const isOwner = computed(() => {
  if (!project.value || !authStore.user) return false
  return projectStore.members.some(m => m.user_id === authStore.user!.id && m.role === 'owner')
})

const loadData = async () => {
  await projectStore.fetchProject(projectId.value)
  await Promise.all([
    projectStore.fetchPlannedExpenses(projectId.value),
    projectStore.fetchProjectTransactions(projectId.value),
    projectStore.fetchMembers(projectId.value),
  ])
}

onMounted(loadData)
watch(projectId, loadData)

// ── Category ──

const openCategoryModal = (cat?: ProjectCategoryWithSpent) => {
  editingCategory.value = cat || null
  categoryForm.value = {
    name: cat?.name || '',
    planned_amount: cat?.planned_amount || 0,
  }
  showCategoryModal.value = true
}

const handleSaveCategory = async () => {
  if (!categoryForm.value.name) return
  saving.value = true
  try {
    if (editingCategory.value) {
      await projectStore.updateCategory(projectId.value, editingCategory.value.id, categoryForm.value)
      message.success(t('project.categoryUpdated'))
    } else {
      await projectStore.createCategory(projectId.value, categoryForm.value)
      message.success(t('project.categoryAdded'))
    }
    showCategoryModal.value = false
    await loadData()
  } catch {
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

const handleDeleteCategory = async (categoryId: string) => {
  try {
    await projectStore.deleteCategory(projectId.value, categoryId)
    message.success(t('project.categoryDeleted'))
    await loadData()
  } catch {
    message.error(t('errors.generic'))
  }
}

// ── Planned Expenses ──

const openExpenseModal = (expense?: ProjectPlannedExpense) => {
  editingExpense.value = expense || null
  expenseForm.value = {
    description: expense?.description || '',
    amount: expense?.amount || 0,
    project_category_id: expense?.project_category_id || null,
    due_date: expense?.due_date ? new Date(expense.due_date).getTime() : null,
    reminder_date: expense?.reminder_date ? new Date(expense.reminder_date).getTime() : null,
  }
  showExpenseModal.value = true
}

const handleSaveExpense = async () => {
  if (!expenseForm.value.description || !expenseForm.value.project_category_id || expenseForm.value.amount <= 0) return
  saving.value = true
  try {
    const data = {
      project_category_id: expenseForm.value.project_category_id,
      description: expenseForm.value.description,
      amount: expenseForm.value.amount,
      due_date: expenseForm.value.due_date ? formatDate(expenseForm.value.due_date) : undefined,
      reminder_date: expenseForm.value.reminder_date ? formatDate(expenseForm.value.reminder_date) : undefined,
    }
    if (editingExpense.value) {
      await projectStore.updatePlannedExpense(projectId.value, editingExpense.value.id, data)
      message.success(t('project.expenseUpdated'))
    } else {
      await projectStore.createPlannedExpense(projectId.value, data)
      message.success(t('project.expenseAdded'))
    }
    showExpenseModal.value = false
    await loadData()
  } catch {
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

const handleMarkPaid = async (expenseId: string) => {
  try {
    await projectStore.updatePlannedExpense(projectId.value, expenseId, { status: 'paid' })
    message.success(t('project.expenseUpdated'))
    await loadData()
  } catch {
    message.error(t('errors.generic'))
  }
}

const handleDeleteExpense = async (expenseId: string) => {
  try {
    await projectStore.deletePlannedExpense(projectId.value, expenseId)
    message.success(t('project.expenseDeleted'))
    await loadData()
  } catch {
    message.error(t('errors.generic'))
  }
}

// ── Transaction edit ──

const openTxEditModal = (tx: ProjectTransaction) => {
  editingTx.value = tx
  txForm.value = {
    title: tx.title,
    amount: tx.amount,
    transaction_type: (tx.transaction_type === 'income' ? 'income' : 'expense'),
    date: new Date(tx.date).getTime(),
    comment: tx.comment || '',
  }
  showTxEditModal.value = true
}

const handleSaveTx = async () => {
  if (!editingTx.value || !txForm.value.date || !txForm.value.title) return
  saving.value = true
  try {
    const data = {
      title: txForm.value.title,
      amount: txForm.value.amount,
      transaction_type: txForm.value.transaction_type,
      date: formatDate(txForm.value.date),
      comment: txForm.value.comment || undefined,
    }
    if (editingTx.value.source === 'pro') {
      await proTransactionsAPI.update(editingTx.value.id, data)
    } else {
      await transactionsAPI.update(editingTx.value.id, data)
    }
    message.success(t('transaction.transactionUpdated'))
    showTxEditModal.value = false
    editingTx.value = null
    await loadData()
  } catch {
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

// ── Members ──

const handleInviteMember = async () => {
  if (!inviteEmail.value) return
  saving.value = true
  try {
    await projectStore.inviteMember(projectId.value, inviteEmail.value, inviteRole.value)
    message.success(t('project.invitationSent'))
    showInviteModal.value = false
    inviteEmail.value = ''
    inviteRole.value = 'member'
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } }
    if (err.response?.status === 404) message.error(t('project.userNotFound'))
    else if (err.response?.status === 409) message.error(t('project.alreadyMember'))
    else message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

const handleRemoveMember = async (memberId: string) => {
  try {
    await projectStore.removeMember(projectId.value, memberId)
    message.success(t('project.memberRemoved'))
  } catch {
    message.error(t('errors.generic'))
  }
}
</script>

<style scoped>
.project-title {
  margin: 0;
  font-size: clamp(20px, 5vw, 28px);
}
.summary-progress-wrapper {
  margin-top: 16px;
}
.summary-progress-label {
  font-size: 12px;
  margin-bottom: 6px;
}
.stat-with-breakdown {
  cursor: help;
  display: inline-block;
}
.stat-with-breakdown :deep(.n-statistic-value__content) {
  border-bottom: 1px dashed var(--n-border-color, rgba(255, 255, 255, 0.25));
}
.target-date-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.target-date-label {
  color: var(--n-text-color-3, rgba(255, 255, 255, 0.5));
  font-size: 14px;
}
.target-date-value {
  font-size: 18px;
  font-weight: 500;
}
.budget-breakdown {
  min-width: 220px;
}
.budget-breakdown-title {
  font-size: 12px;
  color: var(--n-text-color-3, rgba(255, 255, 255, 0.5));
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}
.budget-breakdown-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 3px 0;
}
.budget-breakdown-total {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-top: 8px;
  margin-top: 4px;
  border-top: 1px solid var(--n-border-color);
  font-weight: 600;
}
.summary-description {
  margin-top: 8px;
  display: block;
}
.list-row {
  padding: 10px 0;
  border-bottom: 1px solid var(--n-border-color);
}
.list-row--compact {
  padding: 8px 0;
}
.list-row:last-child {
  border-bottom: none;
}
.list-row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.list-row-header--clickable {
  cursor: pointer;
  margin: -4px -8px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.15s ease;
}
.list-row-header--clickable:hover {
  background-color: var(--n-color-hover, rgba(255, 255, 255, 0.04));
}
.list-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  margin-top: 4px;
  border-top: 1px solid var(--n-border-color);
  font-weight: 600;
}
.multi-progress {
  position: relative;
  display: flex;
  height: 8px;
  margin-top: 8px;
  border-radius: 4px;
  background: var(--n-rail-color, rgba(255, 255, 255, 0.08));
  overflow: hidden;
}
.multi-progress-segment {
  height: 100%;
  transition: width 0.3s ease;
}
.multi-progress-mark {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(255, 255, 255, 0.85);
}
.category-tx-list {
  margin-top: 8px;
  padding-left: 20px;
  border-left: 2px solid var(--n-border-color);
}
.sub-row {
  padding: 6px 0;
  border-bottom: 1px solid var(--n-border-color);
}
.sub-row:last-child {
  border-bottom: none;
}
.text-pending {
  color: var(--color-pending, #f0a020);
}
</style>

<style>
:root {
  --color-success: #18a058;
  --color-error: #d03050;
  --color-pending: #f0a020;
}
</style>
