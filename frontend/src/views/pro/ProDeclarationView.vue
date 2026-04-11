<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.declaration.title') }}</h1>
      <n-select
        v-model:value="selectedYear"
        :options="yearOptions"
        :style="{ width: '140px' }"
      />
    </div>

    <!-- Period Summary Cards -->
    <n-grid :cols="isMobile ? 1 : 2" :x-gap="12" :y-gap="12">
      <n-gi v-for="period in proStore.declarationPeriods" :key="period.period_start">
        <n-card
          size="small"
          :class="{ 'period-active': period.period_start === selectedPeriodStart }"
          style="cursor: pointer;"
          @click="selectPeriod(period.period_start, period.period_end)"
        >
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>{{ period.period_label }}</strong>
              <div style="font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 4px;">
                {{ period.declared_transactions }} / {{ period.total_transactions }} {{ t('pro.declaration.declared') }}
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-weight: bold; font-size: 16px;">{{ period.declared_income.toFixed(2) }} €</div>
              <div style="font-size: 12px; color: rgba(255,255,255,0.5);">
                / {{ period.total_income.toFixed(2) }} €
              </div>
            </div>
          </div>
          <n-progress
            type="line"
            :percentage="period.total_income > 0 ? Math.round(period.declared_income / period.total_income * 100) : 0"
            :color="period.declared_income >= period.total_income && period.total_income > 0 ? '#18a058' : '#2080f0'"
            :rail-color="'rgba(255,255,255,0.1)'"
            :show-indicator="false"
            style="margin-top: 8px;"
          />
          <div v-if="period.cotisations_estimated > 0" style="font-size: 12px; color: #f0a020; margin-top: 4px;">
            {{ t('pro.declaration.cotisations') }}: {{ period.cotisations_estimated.toFixed(2) }} €
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Selected Period: Transaction List -->
    <template v-if="selectedPeriodStart">
      <n-divider />
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
        <h2 style="margin: 0;">{{ selectedPeriodLabel }}</h2>
        <n-space :size="8">
          <n-button
            v-if="undeclaredTransactions.length > 0"
            type="primary"
            size="small"
            @click="declareAll"
          >
            {{ t('pro.declaration.declareAll') }}
          </n-button>
          <n-button
            v-if="declaredTransactions.length > 0"
            size="small"
            quaternary
            @click="undeclareAll"
          >
            {{ t('pro.declaration.undeclareAll') }}
          </n-button>
        </n-space>
      </div>

      <!-- Stats for the selected period -->
      <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.declaration.totalIncome')" :value="periodTotalIncome.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.declaration.declaredIncome')" :value="periodDeclaredIncome.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.declaration.undeclaredIncome')" :value="periodUndeclaredIncome.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.declaration.cotisations')" :value="periodCotisations.toFixed(2)">
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- Transaction List -->
      <n-empty v-if="periodIncomeTransactions.length === 0" :description="t('pro.transactions.noTransactions')" />

      <!-- Desktop Table -->
      <n-data-table
        v-if="!isMobile && periodIncomeTransactions.length > 0"
        :columns="columns"
        :data="periodIncomeTransactions"
        :row-key="(row: ProTransaction) => row.id"
        :pagination="{ pageSize: 20 }"
      />

      <!-- Mobile Cards -->
      <n-space v-if="isMobile && periodIncomeTransactions.length > 0" vertical>
        <n-card v-for="tx in periodIncomeTransactions" :key="tx.id" size="small">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <n-checkbox
                  :checked="tx.is_declared === 1"
                  @update:checked="(v: boolean) => toggleDeclared(tx.id, v)"
                />
                <span>{{ tx.title }}</span>
              </div>
              <div style="font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 4px;">
                {{ tx.date }} · {{ tx.category_name }}
                <span v-if="tx.client_name"> · {{ tx.client_name }}</span>
              </div>
            </div>
            <div style="font-weight: bold; color: #18a058;">
              +{{ tx.amount.toFixed(2) }} €
            </div>
          </div>
        </n-card>
      </n-space>
    </template>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, h, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NSpace, NCard, NGrid, NGi, NStatistic, NButton, NDataTable,
  NSelect, NEmpty, NProgress, NDivider, NCheckbox, NTag, useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProTransaction } from '@/services/api'

const { t } = useI18n()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const currentYear = new Date().getFullYear()
const selectedYear = ref(currentYear)
const selectedPeriodStart = ref<string | null>(null)
const selectedPeriodEnd = ref<string | null>(null)

const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear; y >= currentYear - 3; y--) {
    years.push({ label: String(y), value: y })
  }
  return years
})

const selectedPeriodLabel = computed(() => {
  if (!selectedPeriodStart.value) return ''
  const period = proStore.declarationPeriods.find(p => p.period_start === selectedPeriodStart.value)
  return period?.period_label || ''
})

function selectPeriod(start: string, end: string) {
  selectedPeriodStart.value = start
  selectedPeriodEnd.value = end
  loadPeriodTransactions()
}

async function loadPeriodTransactions() {
  if (!selectedPeriodStart.value || !selectedPeriodEnd.value) return
  // Fetch income transactions for this period
  // end date for API is exclusive in the backend query, but the transactions API uses <=
  // So we need to adjust: period_end is like "2026-02-01", we need transactions with date < that
  // The transactions API filters with date <= end_date, so subtract one day
  const endDate = new Date(selectedPeriodEnd.value)
  endDate.setDate(endDate.getDate() - 1)
  const endStr = endDate.toISOString().slice(0, 10)
  await proStore.fetchTransactions({
    start_date: selectedPeriodStart.value,
    end_date: endStr,
  })
}

const periodIncomeTransactions = computed(() =>
  proStore.proTransactions.filter(tx => tx.transaction_type === 'income')
)

const declaredTransactions = computed(() =>
  periodIncomeTransactions.value.filter(tx => tx.is_declared === 1)
)

const undeclaredTransactions = computed(() =>
  periodIncomeTransactions.value.filter(tx => tx.is_declared !== 1)
)

const periodTotalIncome = computed(() =>
  periodIncomeTransactions.value.reduce((s, tx) => s + tx.amount, 0)
)

const periodDeclaredIncome = computed(() =>
  declaredTransactions.value.reduce((s, tx) => s + tx.amount, 0)
)

const periodUndeclaredIncome = computed(() =>
  undeclaredTransactions.value.reduce((s, tx) => s + tx.amount, 0)
)

const periodCotisations = computed(() => {
  const rate = proStore.proProfile?.cotisation_rate || 21.1
  return periodDeclaredIncome.value * (rate / 100)
})

async function toggleDeclared(txId: string, declared: boolean) {
  await proStore.batchToggleDeclared([txId], declared ? 1 : 0)
  // Update local state
  const tx = proStore.proTransactions.find(t => t.id === txId)
  if (tx) tx.is_declared = declared ? 1 : 0
  // Refresh period summaries
  await proStore.fetchDeclarationPeriods(selectedYear.value)
}

async function declareAll() {
  const ids = undeclaredTransactions.value.map(tx => tx.id)
  if (ids.length === 0) return
  await proStore.batchToggleDeclared(ids, 1)
  ids.forEach(id => {
    const tx = proStore.proTransactions.find(t => t.id === id)
    if (tx) tx.is_declared = 1
  })
  await proStore.fetchDeclarationPeriods(selectedYear.value)
  message.success(t('pro.declaration.allDeclared'))
}

async function undeclareAll() {
  const ids = declaredTransactions.value.map(tx => tx.id)
  if (ids.length === 0) return
  await proStore.batchToggleDeclared(ids, 0)
  ids.forEach(id => {
    const tx = proStore.proTransactions.find(t => t.id === id)
    if (tx) tx.is_declared = 0
  })
  await proStore.fetchDeclarationPeriods(selectedYear.value)
  message.success(t('pro.declaration.allUndeclared'))
}

const columns = computed<DataTableColumns<ProTransaction>>(() => [
  {
    title: '', key: 'declared', width: 50,
    render: (row) => h(NCheckbox, {
      checked: row.is_declared === 1,
      'onUpdate:checked': (v: boolean) => toggleDeclared(row.id, v),
    }),
  },
  { title: t('transaction.date'), key: 'date', width: 110 },
  { title: t('transaction.transactionTitle'), key: 'title' },
  { title: t('category.title'), key: 'category_name' },
  { title: t('pro.transactions.client'), key: 'client_name' },
  {
    title: t('transaction.amount'), key: 'amount', width: 120,
    render: (row) => h('span', { style: { color: '#18a058', fontWeight: 'bold' } }, `+${row.amount.toFixed(2)} €`),
  },
  {
    title: t('common.status'), key: 'status', width: 120,
    render: (row) => h(NTag, {
      type: row.is_declared === 1 ? 'success' : 'warning',
      size: 'small',
    }, () => row.is_declared === 1 ? t('pro.declaration.declared') : t('pro.declaration.undeclared')),
  },
])

watch(selectedYear, async () => {
  selectedPeriodStart.value = null
  selectedPeriodEnd.value = null
  await proStore.fetchDeclarationPeriods(selectedYear.value)
})

onMounted(async () => {
  await Promise.all([
    proStore.fetchProfile(),
    proStore.fetchDeclarationPeriods(selectedYear.value),
  ])
})
</script>

<style scoped>
.period-active {
  border-color: #2080f0 !important;
  border-width: 2px;
}
</style>
