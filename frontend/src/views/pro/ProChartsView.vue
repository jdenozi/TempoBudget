<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.charts.title') }}</h1>

    <!-- Filters -->
    <n-card :title="t('common.filter')" size="small">
      <n-space :vertical="isMobile" :size="12">
        <n-radio-group v-model:value="period" size="small">
          <n-radio-button value="monthly">{{ t('pro.charts.monthly') }}</n-radio-button>
          <n-radio-button value="quarterly">{{ t('pro.charts.quarterly') }}</n-radio-button>
        </n-radio-group>
        <n-date-picker
          v-model:value="selectedMonth"
          type="month"
          :style="{ width: isMobile ? '100%' : '200px' }"
          size="small"
        />
        <n-button size="small" @click="showThresholdsModal = true">
          {{ t('pro.thresholds.manage') }}
        </n-button>
      </n-space>
    </n-card>

    <!-- Charts Grid -->
    <n-grid :cols="isMobile ? 1 : 2" :x-gap="16" :y-gap="16">
      <!-- CA Evolution -->
      <n-gi :span="isMobile ? 1 : 2">
        <n-card :title="period === 'quarterly' ? t('pro.charts.caEvolutionQuarterly') : t('pro.charts.caEvolution')">
          <div :style="{ height: isMobile ? '280px' : '340px', position: 'relative' }">
            <Bar :data="caEvolutionData" :options="barChartOpts" />
          </div>
        </n-card>
      </n-gi>

      <!-- Expenses by Category -->
      <n-gi>
        <n-card :title="t('pro.charts.expensesByCategory')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Pie :data="expensesByCategoryData" :options="pieChartOpts" />
          </div>
        </n-card>
      </n-gi>

      <!-- CA by Client -->
      <n-gi>
        <n-card :title="t('pro.charts.caByClient')">
          <div :style="{ height: isMobile ? '250px' : '300px', position: 'relative' }">
            <Doughnut :data="caByClientData" :options="doughnutChartOpts" />
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Thresholds management modal -->
    <n-modal v-model:show="showThresholdsModal" preset="card" :title="t('pro.thresholds.manage')" style="max-width: 640px;">
      <n-space vertical>
        <n-empty v-if="proStore.proThresholds.length === 0" :description="t('pro.thresholds.empty')" />

        <n-list v-else>
          <n-list-item v-for="th in proStore.proThresholds" :key="th.id">
            <n-flex justify="space-between" align="center" :wrap="true" :size="8">
              <n-flex align="center" :size="8">
                <span :style="{ display: 'inline-block', width: '12px', height: '12px', background: th.color, borderRadius: '50%' }" />
                <strong>{{ th.name }}</strong>
                <n-tag size="tiny" type="info">{{ t(`pro.thresholds.period.${th.period}`) }}</n-tag>
                <span>{{ th.amount.toFixed(2) }} €</span>
                <n-tag size="tiny" :type="th.active ? 'success' : 'default'">
                  {{ th.active ? t('common.active') : t('common.inactive') }}
                </n-tag>
              </n-flex>
              <n-flex :size="8">
                <n-button size="tiny" @click="toggleActive(th)">{{ th.active ? t('recurring.deactivate') : t('recurring.activate') }}</n-button>
                <n-button size="tiny" @click="openEdit(th)">{{ t('common.edit') }}</n-button>
                <n-popconfirm @positive-click="handleDelete(th.id)">
                  <template #trigger>
                    <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
                  </template>
                  {{ t('pro.thresholds.deleteConfirm') }}
                </n-popconfirm>
              </n-flex>
            </n-flex>
          </n-list-item>
        </n-list>

        <n-divider style="margin: 8px 0;">{{ editingThreshold ? t('pro.thresholds.edit') : t('pro.thresholds.add') }}</n-divider>

        <n-form :model="form">
          <n-form-item :label="t('pro.thresholds.name')">
            <n-input v-model:value="form.name" :placeholder="t('pro.thresholds.namePlaceholder')" />
          </n-form-item>
          <n-form-item :label="t('pro.thresholds.period.label')">
            <n-radio-group v-model:value="form.period">
              <n-radio-button value="monthly">{{ t('pro.thresholds.period.monthly') }}</n-radio-button>
              <n-radio-button value="quarterly">{{ t('pro.thresholds.period.quarterly') }}</n-radio-button>
              <n-radio-button value="yearly">{{ t('pro.thresholds.period.yearly') }}</n-radio-button>
            </n-radio-group>
          </n-form-item>
          <n-form-item :label="t('transaction.amount')">
            <n-input-number v-model:value="form.amount" :min="0.01" :precision="2" style="width: 100%;">
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>
          <n-form-item :label="t('pro.thresholds.color')">
            <n-color-picker v-model:value="form.color" :show-alpha="false" :modes="['hex']" />
          </n-form-item>
          <n-flex :size="8">
            <n-button v-if="editingThreshold" @click="resetForm">{{ t('common.cancel') }}</n-button>
            <n-button type="primary" :loading="saving" @click="handleSave">{{ t('common.save') }}</n-button>
          </n-flex>
        </n-form>
      </n-space>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NSpace, NCard, NDatePicker, NGrid, NGi, NRadioGroup, NRadioButton,
  NButton, NModal, NEmpty, NList, NListItem, NFlex, NTag, NPopconfirm,
  NDivider, NForm, NFormItem, NInput, NInputNumber, NColorPicker, useMessage,
} from 'naive-ui'
import { Pie, Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import { CHART_COLORS, INCOME_COLORS, usePieChartOptions, useBarChartOptions } from '@/composables/useChartOptions'
import type { ProThreshold } from '@/services/api'

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, annotationPlugin)

const { t, locale } = useI18n()
const proStore = useProStore()
const { isMobile } = useMobileDetect()
const message = useMessage()

const period = ref<'monthly' | 'quarterly'>('monthly')
const selectedMonth = ref(Date.now())
const showThresholdsModal = ref(false)
const editingThreshold = ref<ProThreshold | null>(null)
const saving = ref(false)

type Period = 'monthly' | 'quarterly' | 'yearly'

const form = ref({
  name: '',
  period: 'monthly' as Period,
  amount: null as number | null,
  color: '#f0a020',
})

const pieChartOpts = usePieChartOptions(isMobile)
const doughnutChartOpts = usePieChartOptions(isMobile, { showPercentage: false })

onMounted(async () => {
  await Promise.all([
    proStore.fetchTransactions(),
    proStore.fetchClients(),
    proStore.fetchCategories(),
    proStore.fetchThresholds(),
  ])
})

/** Convert a threshold's amount to the per-bucket value matching the current period view. */
function thresholdValueForView(th: ProThreshold): number {
  if (period.value === 'monthly') {
    if (th.period === 'monthly') return th.amount
    if (th.period === 'quarterly') return th.amount / 3
    return th.amount / 12
  }
  if (th.period === 'monthly') return th.amount * 3
  if (th.period === 'quarterly') return th.amount
  return th.amount / 4
}

/** Bar chart options with horizontal threshold lines as annotations. */
const barChartOpts = computed(() => {
  const base = useBarChartOptions(isMobile) as Record<string, unknown>
  const annotations: Record<string, unknown> = {}
  for (const th of proStore.proThresholds) {
    if (!th.active) continue
    const value = thresholdValueForView(th)
    annotations[`th_${th.id}`] = {
      type: 'line',
      yMin: value,
      yMax: value,
      borderColor: th.color,
      borderWidth: 2,
      borderDash: [6, 4],
      label: {
        display: true,
        content: `${th.name} — ${value.toFixed(0)} €`,
        position: 'end',
        backgroundColor: th.color,
        color: '#fff',
        font: { size: isMobile.value ? 9 : 11 },
        padding: 4,
      },
    }
  }
  return {
    ...base,
    plugins: {
      ...((base.plugins as Record<string, unknown>) ?? {}),
      annotation: { annotations },
    },
  } as Record<string, unknown>
})

/** Aggregate by month (12 months back) or by quarter (8 quarters back). */
const aggregatedData = computed(() => {
  const localeStr = locale.value === 'fr' ? 'fr-FR' : 'en-US'
  const now = new Date(selectedMonth.value)

  if (period.value === 'monthly') {
    const buckets: { label: string; income: number; expenses: number }[] = []
    for (let i = 11; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const label = d.toLocaleString(localeStr, { month: 'short' })
      const m = d.getMonth()
      const y = d.getFullYear()
      const txs = proStore.proTransactions.filter(tx => {
        const td = new Date(tx.date)
        return td.getMonth() === m && td.getFullYear() === y
      })
      const income = txs.filter(tx => tx.transaction_type === 'income').reduce((s, tx) => s + tx.amount, 0)
      const expenses = txs.filter(tx => tx.transaction_type === 'expense').reduce((s, tx) => s + tx.amount, 0)
      buckets.push({ label, income, expenses })
    }
    return buckets
  }

  // Quarterly: 8 quarters ending with the quarter that contains selectedMonth
  const buckets: { label: string; income: number; expenses: number }[] = []
  const currentQuarter = Math.floor(now.getMonth() / 3)
  for (let i = 7; i >= 0; i--) {
    const totalOffset = currentQuarter - i
    const yearOffset = Math.floor(totalOffset / 4)
    const q = ((totalOffset % 4) + 4) % 4
    const year = now.getFullYear() + yearOffset
    const txs = proStore.proTransactions.filter(tx => {
      const td = new Date(tx.date)
      return td.getFullYear() === year && Math.floor(td.getMonth() / 3) === q
    })
    const income = txs.filter(tx => tx.transaction_type === 'income').reduce((s, tx) => s + tx.amount, 0)
    const expenses = txs.filter(tx => tx.transaction_type === 'expense').reduce((s, tx) => s + tx.amount, 0)
    buckets.push({ label: `Q${q + 1} ${String(year).slice(2)}`, income, expenses })
  }
  return buckets
})

const caEvolutionData = computed(() => ({
  labels: aggregatedData.value.map(d => d.label),
  datasets: [
    {
      label: t('pro.charts.turnover'),
      data: aggregatedData.value.map(d => d.income),
      backgroundColor: '#18a058',
      borderRadius: 4,
    },
    {
      label: t('pro.charts.expenses'),
      data: aggregatedData.value.map(d => d.expenses),
      backgroundColor: '#d03050',
      borderRadius: 4,
    },
  ],
}))

const expensesByCategoryData = computed(() => {
  const byCategory: Record<string, number> = {}
  const now = new Date(selectedMonth.value)
  proStore.proTransactions
    .filter(tx => {
      if (tx.transaction_type !== 'expense') return false
      const d = new Date(tx.date)
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })
    .forEach(tx => {
      const name = tx.category_name || 'Other'
      byCategory[name] = (byCategory[name] || 0) + tx.amount
    })
  return {
    labels: Object.keys(byCategory),
    datasets: [{
      data: Object.values(byCategory),
      backgroundColor: CHART_COLORS,
      borderWidth: 2,
      borderColor: '#fff',
    }],
  }
})

const caByClientData = computed(() => {
  const byClient: Record<string, number> = {}
  const now = new Date(selectedMonth.value)
  proStore.proTransactions
    .filter(tx => {
      if (tx.transaction_type !== 'income') return false
      const d = new Date(tx.date)
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })
    .forEach(tx => {
      const name = tx.client_name || 'Sans client'
      byClient[name] = (byClient[name] || 0) + tx.amount
    })
  return {
    labels: Object.keys(byClient),
    datasets: [{
      data: Object.values(byClient),
      backgroundColor: INCOME_COLORS,
      borderWidth: 2,
      borderColor: '#fff',
    }],
  }
})

function resetForm() {
  editingThreshold.value = null
  form.value = { name: '', period: 'monthly', amount: null, color: '#f0a020' }
}

function openEdit(th: ProThreshold) {
  editingThreshold.value = th
  form.value = {
    name: th.name,
    period: th.period,
    amount: th.amount,
    color: th.color,
  }
}

async function handleSave() {
  if (!form.value.name || !form.value.amount) return
  saving.value = true
  try {
    if (editingThreshold.value) {
      await proStore.updateThreshold(editingThreshold.value.id, {
        name: form.value.name,
        period: form.value.period,
        amount: form.value.amount,
        color: form.value.color,
      })
      message.success(t('pro.thresholds.updated'))
    } else {
      await proStore.createThreshold({
        name: form.value.name,
        period: form.value.period,
        amount: form.value.amount,
        color: form.value.color,
      })
      message.success(t('pro.thresholds.added'))
    }
    resetForm()
  } catch (e) {
    console.error(e)
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

async function toggleActive(th: ProThreshold) {
  await proStore.updateThreshold(th.id, { active: th.active ? 0 : 1 })
}

async function handleDelete(id: string) {
  await proStore.deleteThreshold(id)
  message.success(t('pro.thresholds.deleted'))
}

watch(showThresholdsModal, (open) => {
  if (!open) resetForm()
})
</script>
