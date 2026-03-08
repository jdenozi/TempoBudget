<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.giftCards.title') }}</h1>
      <n-button type="primary" @click="openCreateModal">{{ t('pro.giftCards.addGiftCard') }}</n-button>
    </div>

    <n-empty v-if="proStore.proGiftCards.length === 0" :description="t('pro.giftCards.noGiftCards')" />

    <!-- Desktop Table -->
    <n-data-table
      v-if="!isMobile && proStore.proGiftCards.length > 0"
      :columns="columns"
      :data="proStore.proGiftCards"
      :row-key="(row: ProGiftCard) => row.id"
    />

    <!-- Mobile Cards -->
    <n-space v-if="isMobile && proStore.proGiftCards.length > 0" vertical>
      <n-card v-for="gc in proStore.proGiftCards" :key="gc.id" size="small" @click="openUsageModal(gc)">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>{{ gc.code }}</strong>
            <span style="font-weight: bold;">{{ gc.remaining_balance.toFixed(2) }} / {{ gc.initial_amount.toFixed(2) }} €</span>
          </div>
        </template>
        <n-space size="small">
          <n-tag v-if="gc.client_name" size="tiny">{{ gc.client_name }}</n-tag>
          <span style="font-size: 12px; color: rgba(255,255,255,0.5);">{{ gc.purchase_date }}</span>
          <n-tag size="tiny" :type="gc.is_active && gc.remaining_balance > 0 ? 'success' : 'default'">
            {{ gc.is_active && gc.remaining_balance > 0 ? t('pro.coupons.active') : t('pro.coupons.inactive') }}
          </n-tag>
        </n-space>
        <template #action>
          <n-space size="small">
            <n-button size="tiny" @click.stop="openUsageModal(gc)">{{ t('pro.giftCards.usageHistory') }}</n-button>
            <n-popconfirm @positive-click="handleDelete(gc.id)">
              <template #trigger>
                <n-button size="tiny" type="error" @click.stop>{{ t('common.delete') }}</n-button>
              </template>
              {{ t('pro.giftCards.deleteGiftCardConfirm') }}
            </n-popconfirm>
          </n-space>
        </template>
      </n-card>
    </n-space>

    <!-- Create Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" :title="t('pro.giftCards.addGiftCard')" style="max-width: 500px;">
      <n-form :model="gcForm">
        <n-form-item :label="t('pro.giftCards.code')">
          <n-input v-model:value="gcForm.code" />
        </n-form-item>
        <n-form-item :label="t('pro.giftCards.initialAmount')">
          <n-input-number v-model:value="gcForm.initial_amount" :min="0.01" :precision="2" style="width: 100%;">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('pro.giftCards.purchasedBy')">
          <n-select v-model:value="gcForm.client_id" :options="clientOptions" clearable />
        </n-form-item>
        <n-form-item :label="t('pro.giftCards.purchaseDate')">
          <n-date-picker v-model:value="gcForm.purchase_date" type="date" style="width: 100%;" />
        </n-form-item>
        <n-button type="primary" block @click="handleCreate">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>

    <!-- Usage History Modal -->
    <n-modal v-model:show="showUsageModal" preset="card" :title="`${selectedGiftCard?.code} — ${t('pro.giftCards.usageHistory')}`" style="max-width: 600px;">
      <div v-if="selectedGiftCard" style="margin-bottom: 16px;">
        <n-space :size="16">
          <n-statistic :label="t('pro.giftCards.initialAmount')" :value="selectedGiftCard.initial_amount.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
          <n-statistic :label="t('pro.giftCards.remainingBalance')" :value="selectedGiftCard.remaining_balance.toFixed(2)">
            <template #suffix>€</template>
          </n-statistic>
        </n-space>
      </div>

      <n-empty v-if="usages.length === 0" :description="t('pro.giftCards.noUsages')" />

      <n-data-table
        v-if="usages.length > 0"
        :columns="usageColumns"
        :data="usages"
        :row-key="(row: ProGiftCardUsage) => row.id"
        size="small"
      />
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NSpace, NCard, NButton, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NEmpty, NTag, NPopconfirm,
  NDatePicker, NStatistic, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProGiftCard, ProGiftCardUsage } from '@/services/api'

const { t } = useI18n()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const showCreateModal = ref(false)
const showUsageModal = ref(false)
const selectedGiftCard = ref<ProGiftCard | null>(null)
const usages = ref<ProGiftCardUsage[]>([])

const gcForm = ref({
  code: '',
  initial_amount: 50 as number | null,
  client_id: null as string | null,
  purchase_date: Date.now(),
})

const clientOptions = computed(() =>
  proStore.proClients.map(c => ({ label: c.name, value: c.id }))
)

function formatDate(ts: number) {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const columns: DataTableColumns<ProGiftCard> = [
  { title: () => t('pro.giftCards.code'), key: 'code', width: 140 },
  {
    title: () => t('pro.giftCards.initialAmount'),
    key: 'initial_amount',
    width: 130,
    render(row) { return `${row.initial_amount.toFixed(2)} €` },
  },
  {
    title: () => t('pro.giftCards.remainingBalance'),
    key: 'remaining_balance',
    width: 140,
    render(row) {
      const pct = row.initial_amount > 0 ? (row.remaining_balance / row.initial_amount * 100) : 0
      const color = pct > 50 ? '#18a058' : pct > 20 ? '#f0a020' : '#d03050'
      return h('span', { style: { color, fontWeight: 'bold' } }, `${row.remaining_balance.toFixed(2)} €`)
    },
  },
  { title: () => t('pro.giftCards.purchasedBy'), key: 'client_name', width: 150 },
  { title: () => t('pro.giftCards.purchaseDate'), key: 'purchase_date', width: 120 },
  {
    title: () => t('common.actions'),
    key: 'actions',
    width: 180,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', onClick: () => openUsageModal(row) }, () => t('pro.giftCards.usageHistory')),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('pro.giftCards.deleteGiftCardConfirm'),
        }),
      ])
    },
  },
]

const usageColumns: DataTableColumns<ProGiftCardUsage> = [
  { title: () => t('pro.giftCards.forTransaction'), key: 'transaction_title' },
  {
    title: () => t('pro.giftCards.amountUsed'),
    key: 'amount_used',
    width: 130,
    render(row) { return `${row.amount_used.toFixed(2)} €` },
  },
  { title: () => t('transaction.date'), key: 'created_at', width: 180 },
]

function openCreateModal() {
  gcForm.value = { code: '', initial_amount: 50, client_id: null, purchase_date: Date.now() }
  showCreateModal.value = true
}

async function openUsageModal(gc: ProGiftCard) {
  selectedGiftCard.value = gc
  usages.value = await proStore.fetchGiftCardUsages(gc.id)
  showUsageModal.value = true
}

async function handleCreate() {
  if (!gcForm.value.code.trim()) return
  if (!gcForm.value.initial_amount || gcForm.value.initial_amount <= 0) return

  await proStore.createGiftCard({
    code: gcForm.value.code,
    initial_amount: gcForm.value.initial_amount,
    client_id: gcForm.value.client_id || undefined,
    purchase_date: formatDate(gcForm.value.purchase_date),
  })
  message.success(t('pro.giftCards.giftCardAdded'))
  showCreateModal.value = false
}

async function handleDelete(id: string) {
  await proStore.deleteGiftCard(id)
  message.success(t('pro.giftCards.giftCardDeleted'))
}

onMounted(async () => {
  await Promise.all([
    proStore.fetchGiftCards(),
    proStore.fetchClients(),
  ])
})
</script>
