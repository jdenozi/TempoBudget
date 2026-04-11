<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('loans.title') }}</h1>
      <n-button type="primary" @click="openAddModal">
        {{ t('loans.addLoan') }}
      </n-button>
    </div>

    <!-- Summary -->
    <n-card v-if="loanStore.summary" size="small">
      <n-grid :cols="isMobile ? 2 : 5" :x-gap="12" :y-gap="12">
        <n-gi>
          <n-statistic :label="t('loans.totalLent')" :value="loanStore.summary.total_lent.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic :label="t('loans.totalBorrowed')" :value="loanStore.summary.total_borrowed.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic :label="t('loans.remaining') + ' (' + t('loans.lent') + ')'" :value="loanStore.summary.total_lent_remaining.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic :label="t('loans.remaining') + ' (' + t('loans.borrowed') + ')'" :value="loanStore.summary.total_borrowed_remaining.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic :label="t('loans.netPosition')" :value="loanStore.summary.net_position.toFixed(2)">
            <template #prefix>
              <n-icon :color="loanStore.summary.net_position >= 0 ? '#18a058' : '#d03050'"><CashOutline /></n-icon>
            </template>
            <template #suffix>€</template>
          </n-statistic>
        </n-gi>
      </n-grid>
    </n-card>

    <!-- Filters -->
    <n-space>
      <n-button v-for="f in filters" :key="f.value" :type="activeFilter === f.value ? 'primary' : 'default'" size="small" @click="activeFilter = f.value">
        {{ f.label }}
      </n-button>
    </n-space>

    <!-- Loading -->
    <div v-if="loanStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <!-- Loan List -->
    <template v-else-if="filteredLoans.length > 0">
      <n-card v-for="loan in filteredLoans" :key="loan.id" size="small">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <strong>{{ loan.person_name }}</strong>
              <n-tag :type="loan.direction === 'lent' ? 'info' : 'warning'" size="small">
                {{ t('loans.' + loan.direction) }}
              </n-tag>
              <n-tag :type="loan.status === 'repaid' ? 'success' : 'default'" size="small">
                {{ t('loans.' + loan.status) }}
              </n-tag>
            </div>
            <div style="display: flex; gap: 8px;">
              <n-button size="small" type="info" @click="openEditModal(loan)">{{ t('common.edit') }}</n-button>
              <n-popconfirm @positive-click="handleDeleteLoan(loan.id)">
                <template #trigger>
                  <n-button size="small" type="error">{{ t('common.delete') }}</n-button>
                </template>
                {{ t('loans.deleteLoanConfirm') }}
              </n-popconfirm>
            </div>
          </div>
        </template>

        <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="8">
          <n-gi>
            <n-text depth="3">{{ t('loans.amount') }}:</n-text> <strong>{{ loan.amount.toFixed(2) }} €</strong>
          </n-gi>
          <n-gi>
            <n-text depth="3">{{ t('loans.remaining') }}:</n-text> <strong>{{ loan.remaining.toFixed(2) }} €</strong>
          </n-gi>
          <n-gi>
            <n-text depth="3">{{ t('loans.date') }}:</n-text> {{ loan.date }}
          </n-gi>
          <n-gi v-if="loan.description">
            <n-text depth="3">{{ t('loans.description') }}:</n-text> {{ loan.description }}
          </n-gi>
        </n-grid>

        <!-- Progress bar -->
        <div style="margin-top: 12px;">
          <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
            <span>{{ t('loans.progress') }}</span>
            <span>{{ loan.amount > 0 ? ((loan.total_repaid / loan.amount) * 100).toFixed(1) : 0 }}%</span>
          </div>
          <n-progress
            :percentage="loan.amount > 0 ? Math.min((loan.total_repaid / loan.amount) * 100, 100) : 0"
            :color="loan.status === 'repaid' ? '#18a058' : '#2080f0'"
            :show-indicator="false"
          />
        </div>

        <!-- Add repayment button -->
        <div style="margin-top: 12px; display: flex; gap: 8px; align-items: center;">
          <n-button size="small" @click="openRepaymentModal(loan)">
            {{ t('loans.addRepayment') }}
          </n-button>
          <n-button v-if="loan.repayments.length > 0" size="small" text @click="toggleRepayments(loan.id)">
            {{ t('loans.repayments') }} ({{ loan.repayments.length }})
            {{ expandedLoans.has(loan.id) ? '▲' : '▼' }}
          </n-button>
        </div>

        <!-- Repayments list -->
        <div v-if="expandedLoans.has(loan.id) && loan.repayments.length > 0" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08);">
          <div v-for="rep in loan.repayments" :key="rep.id" style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0;">
            <div>
              <strong>{{ rep.amount.toFixed(2) }} €</strong>
              <n-text depth="3" style="margin-left: 8px;">{{ rep.date }}</n-text>
              <n-text v-if="rep.comment" depth="3" style="margin-left: 8px;">— {{ rep.comment }}</n-text>
            </div>
            <n-popconfirm @positive-click="handleDeleteRepayment(loan.id, rep.id)">
              <template #trigger>
                <n-button size="tiny" type="error" text>{{ t('common.delete') }}</n-button>
              </template>
              {{ t('loans.deleteRepaymentConfirm') }}
            </n-popconfirm>
          </div>
        </div>
      </n-card>
    </template>

    <!-- Empty state -->
    <n-empty v-else-if="!loanStore.loading" :description="t('loans.noLoans')" style="margin-top: 40px;">
      <template #extra>
        <n-button @click="openAddModal" type="primary">{{ t('loans.addLoan') }}</n-button>
      </template>
    </n-empty>

    <!-- Add/Edit Loan Modal -->
    <n-modal v-model:show="showLoanModal" preset="card" :title="editingLoan ? t('loans.editLoan') : t('loans.addLoan')" :style="{ width: isMobile ? '90%' : '500px' }">
      <n-form>
        <n-form-item :label="t('loans.personName')">
          <n-input v-model:value="loanForm.person_name" />
        </n-form-item>
        <n-form-item :label="t('loans.direction')">
          <n-radio-group v-model:value="loanForm.direction">
            <n-radio-button value="lent">{{ t('loans.lent') }}</n-radio-button>
            <n-radio-button value="borrowed">{{ t('loans.borrowed') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('loans.amount')">
          <n-input-number v-model:value="loanForm.amount" :min="0.01" :precision="2" style="width: 100%">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('loans.date')">
          <n-date-picker v-model:value="loanForm.date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item :label="t('loans.description')">
          <n-input v-model:value="loanForm.description" type="textarea" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showLoanModal = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveLoan">{{ t('common.save') }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Add Repayment Modal -->
    <n-modal v-model:show="showRepaymentModal" preset="card" :title="t('loans.addRepayment')" :style="{ width: isMobile ? '90%' : '400px' }">
      <n-form>
        <n-form-item :label="t('loans.amount')">
          <n-input-number v-model:value="repaymentForm.amount" :min="0.01" :precision="2" style="width: 100%">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('loans.date')">
          <n-date-picker v-model:value="repaymentForm.date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item :label="t('loans.comment')">
          <n-input v-model:value="repaymentForm.comment" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRepaymentModal = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveRepayment">{{ t('common.save') }}</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSpace, NButton, NCard, NGrid, NGi, NStatistic, NTag, NText,
  NIcon, NSpin, NEmpty, NProgress, NModal, NForm, NFormItem,
  NInput, NInputNumber, NRadioGroup, NRadioButton, NDatePicker,
  NPopconfirm, useMessage
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { CashOutline } from '@vicons/ionicons5'
import { useLoanStore } from '@/stores/loan'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { Loan } from '@/services/api'

const { t } = useI18n()
const message = useMessage()
const loanStore = useLoanStore()
const { isMobile } = useMobileDetect()

const activeFilter = ref('all')
const expandedLoans = ref(new Set<string>())
const showLoanModal = ref(false)
const showRepaymentModal = ref(false)
const saving = ref(false)
const editingLoan = ref<Loan | null>(null)
const repaymentLoanId = ref<string | null>(null)

const loanForm = ref({
  person_name: '',
  amount: 0 as number,
  direction: 'lent' as 'lent' | 'borrowed',
  date: Date.now() as number | null,
  description: '',
})

const repaymentForm = ref({
  amount: 0 as number,
  date: Date.now() as number | null,
  comment: '',
})

const filters = computed(() => [
  { label: t('loans.all'), value: 'all' },
  { label: t('loans.filterLent'), value: 'lent' },
  { label: t('loans.filterBorrowed'), value: 'borrowed' },
  { label: t('loans.filterActive'), value: 'active' },
  { label: t('loans.filterRepaid'), value: 'repaid' },
])

const filteredLoans = computed(() => {
  let loans = loanStore.loans
  if (activeFilter.value === 'lent') loans = loans.filter(l => l.direction === 'lent')
  if (activeFilter.value === 'borrowed') loans = loans.filter(l => l.direction === 'borrowed')
  if (activeFilter.value === 'active') loans = loans.filter(l => l.status === 'active')
  if (activeFilter.value === 'repaid') loans = loans.filter(l => l.status === 'repaid')
  return loans
})

onMounted(async () => {
  await Promise.all([loanStore.fetchLoans(), loanStore.fetchSummary()])
})

const formatDate = (ts: number) => {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const openAddModal = () => {
  editingLoan.value = null
  loanForm.value = { person_name: '', amount: 0, direction: 'lent', date: Date.now(), description: '' }
  showLoanModal.value = true
}

const openEditModal = (loan: Loan) => {
  editingLoan.value = loan
  loanForm.value = {
    person_name: loan.person_name,
    amount: loan.amount,
    direction: loan.direction,
    date: new Date(loan.date).getTime(),
    description: loan.description || '',
  }
  showLoanModal.value = true
}

const openRepaymentModal = (loan: Loan) => {
  repaymentLoanId.value = loan.id
  repaymentForm.value = { amount: 0, date: Date.now(), comment: '' }
  showRepaymentModal.value = true
}

const toggleRepayments = (id: string) => {
  if (expandedLoans.value.has(id)) {
    expandedLoans.value.delete(id)
  } else {
    expandedLoans.value.add(id)
  }
}

const handleSaveLoan = async () => {
  if (!loanForm.value.person_name || !loanForm.value.amount || !loanForm.value.date) return
  saving.value = true
  try {
    const dateStr = formatDate(loanForm.value.date)
    if (editingLoan.value) {
      await loanStore.updateLoan(editingLoan.value.id, {
        person_name: loanForm.value.person_name,
        amount: loanForm.value.amount,
        direction: loanForm.value.direction,
        date: dateStr,
        description: loanForm.value.description || undefined,
      })
      message.success(t('loans.loanUpdated'))
    } else {
      await loanStore.createLoan({
        person_name: loanForm.value.person_name,
        amount: loanForm.value.amount,
        direction: loanForm.value.direction,
        date: dateStr,
        description: loanForm.value.description || undefined,
      })
      message.success(t('loans.loanAdded'))
    }
    showLoanModal.value = false
  } catch {
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

const handleDeleteLoan = async (id: string) => {
  try {
    await loanStore.deleteLoan(id)
    message.success(t('loans.loanDeleted'))
  } catch {
    message.error(t('errors.generic'))
  }
}

const handleSaveRepayment = async () => {
  if (!repaymentLoanId.value || !repaymentForm.value.amount || !repaymentForm.value.date) return
  saving.value = true
  try {
    await loanStore.addRepayment(repaymentLoanId.value, {
      amount: repaymentForm.value.amount,
      date: formatDate(repaymentForm.value.date),
      comment: repaymentForm.value.comment || undefined,
    })
    message.success(t('loans.repaymentAdded'))
    showRepaymentModal.value = false
  } catch {
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

const handleDeleteRepayment = async (loanId: string, repaymentId: string) => {
  try {
    await loanStore.deleteRepayment(loanId, repaymentId)
    message.success(t('loans.repaymentDeleted'))
  } catch {
    message.error(t('errors.generic'))
  }
}
</script>
