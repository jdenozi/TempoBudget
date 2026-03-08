<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.dashboard.title') }}</h1>

    <!-- Loading State -->
    <div v-if="proStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <template v-else>
      <!-- Setup Profile Alert -->
      <n-card v-if="proStore.proProfile && !proStore.proProfile.siret" size="small" style="border-left: 3px solid #2080f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div>
            <strong>{{ t('pro.dashboard.setupProfile') }}</strong>
            <div style="font-size: 13px; color: rgba(255,255,255,0.6); margin-top: 4px;">{{ t('pro.dashboard.setupProfileDesc') }}</div>
          </div>
          <n-button size="small" type="primary" @click="showProfileModal = true">{{ t('pro.profile.title') }}</n-button>
        </div>
      </n-card>

      <!-- Summary Stats -->
      <n-grid :cols="isMobile ? 2 : 3" :x-gap="12" :y-gap="12">
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.caMonth')" :value="summary.ca_month.toFixed(2)">
              <template #prefix><n-icon color="#18a058"><TrendingUpOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.caQuarter')" :value="summary.ca_quarter.toFixed(2)">
              <template #prefix><n-icon color="#18a058"><TrendingUpOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.caYear')" :value="summary.ca_year.toFixed(2)">
              <template #prefix><n-icon color="#18a058"><TrendingUpOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.expensesMonth')" :value="summary.expenses_month.toFixed(2)">
              <template #prefix><n-icon color="#d03050"><TrendingDownOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.netMonth')" :value="summary.net_month.toFixed(2)">
              <template #prefix><n-icon :color="summary.net_month >= 0 ? '#18a058' : '#d03050'"><WalletOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.cotisationsMonth')" :value="summary.cotisations_estimated.toFixed(2)">
              <template #prefix><n-icon color="#f0a020"><CashOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- Threshold Progress -->
      <n-card :title="t('pro.dashboard.thresholdProgress')" size="small">
        <div style="display: flex; align-items: center; gap: 12px;">
          <n-progress
            type="line"
            :percentage="Math.min(summary.threshold_percentage, 100)"
            :color="summary.threshold_percentage > 90 ? '#d03050' : summary.threshold_percentage > 70 ? '#f0a020' : '#18a058'"
            :rail-color="'rgba(255,255,255,0.1)'"
            style="flex: 1;"
          />
          <span style="white-space: nowrap; font-size: 13px;">
            {{ summary.ca_year.toFixed(0) }}€ / {{ threshold.toFixed(0) }}€
          </span>
        </div>
      </n-card>

      <!-- Recent Transactions -->
      <n-card :title="t('pro.dashboard.recentTransactions')" size="small">
        <n-empty v-if="proStore.proTransactions.length === 0" :description="t('pro.transactions.noTransactions')" />
        <n-list v-else>
          <n-list-item v-for="tx in recentTransactions" :key="tx.id">
            <n-thing>
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>{{ tx.title }}</span>
                  <span :style="{ color: tx.transaction_type === 'income' ? '#18a058' : '#d03050', fontWeight: 'bold' }">
                    {{ tx.transaction_type === 'income' ? '+' : '-' }}{{ tx.amount.toFixed(2) }} €
                  </span>
                </div>
              </template>
              <template #description>
                <n-space size="small">
                  <n-tag size="tiny" :type="tx.transaction_type === 'income' ? 'success' : 'error'">
                    {{ tx.category_name }}
                  </n-tag>
                  <span style="color: rgba(255,255,255,0.5); font-size: 12px;">{{ tx.date }}</span>
                  <span v-if="tx.client_name" style="color: rgba(255,255,255,0.5); font-size: 12px;">· {{ tx.client_name }}</span>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-card>
    </template>

    <!-- Profile Modal -->
    <n-modal v-model:show="showProfileModal" preset="card" :title="t('pro.profile.title')" style="max-width: 500px;">
      <n-form>
        <n-form-item :label="t('pro.profile.siret')">
          <n-input v-model:value="profileForm.siret" :placeholder="t('pro.profile.siret')" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.activityType')">
          <n-select :value="profileForm.activity_type" :options="activityTypeOptions" @update:value="onActivityTypeChange" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.cotisationRate')">
          <n-input-number v-model:value="profileForm.cotisation_rate" :min="0" :max="100" :precision="1" style="width: 100%;" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.declarationFrequency')">
          <n-select v-model:value="profileForm.declaration_frequency" :options="frequencyOptions" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.revenueThreshold')">
          <n-input-number v-model:value="profileForm.revenue_threshold" :min="0" :precision="0" style="width: 100%;">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-button type="primary" block @click="saveProfile">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSpace, NCard, NGrid, NGi, NStatistic, NIcon, NProgress,
  NList, NListItem, NThing, NTag, NEmpty, NAlert, NButton,
  NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NSpin
} from 'naive-ui'
import { TrendingUpOutline, TrendingDownOutline, WalletOutline, CashOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'

const { t } = useI18n()
const proStore = useProStore()
const { isMobile } = useMobileDetect()

const showProfileModal = ref(false)

const profileForm = ref({
  siret: '',
  activity_type: 'services',
  cotisation_rate: 21.1,
  declaration_frequency: 'quarterly',
  revenue_threshold: 77700,
})

/** Activity types with their default cotisation rates and thresholds */
const ACTIVITY_PRESETS: Record<string, { rate: number; threshold: number }> = {
  services: { rate: 21.2, threshold: 77700 },
  liberal: { rate: 21.1, threshold: 77700 },
  vente: { rate: 12.3, threshold: 188700 },
  artisan: { rate: 21.2, threshold: 77700 },
  commercant: { rate: 12.3, threshold: 188700 },
  agent_commercial: { rate: 21.2, threshold: 77700 },
  location_meublee: { rate: 6.0, threshold: 188700 },
  restauration: { rate: 21.2, threshold: 77700 },
  transport: { rate: 21.2, threshold: 77700 },
  activite_mixte: { rate: 21.2, threshold: 188700 },
}

const activityTypeOptions = computed(() => [
  { label: t('pro.profile.services'), value: 'services' },
  { label: t('pro.profile.liberal'), value: 'liberal' },
  { label: t('pro.profile.vente'), value: 'vente' },
  { label: t('pro.profile.artisan'), value: 'artisan' },
  { label: t('pro.profile.commercant'), value: 'commercant' },
  { label: t('pro.profile.agent_commercial'), value: 'agent_commercial' },
  { label: t('pro.profile.location_meublee'), value: 'location_meublee' },
  { label: t('pro.profile.restauration'), value: 'restauration' },
  { label: t('pro.profile.transport'), value: 'transport' },
  { label: t('pro.profile.activite_mixte'), value: 'activite_mixte' },
])

/** Auto-fill rate and threshold when activity type changes */
function onActivityTypeChange(value: string) {
  profileForm.value.activity_type = value
  const preset = ACTIVITY_PRESETS[value]
  if (preset) {
    profileForm.value.cotisation_rate = preset.rate
    profileForm.value.revenue_threshold = preset.threshold
  }
}

const frequencyOptions = computed(() => [
  { label: t('pro.profile.monthly'), value: 'monthly' },
  { label: t('pro.profile.quarterly'), value: 'quarterly' },
])

const summary = computed(() => proStore.dashboardSummary || {
  ca_month: 0, ca_quarter: 0, ca_year: 0,
  expenses_month: 0, expenses_quarter: 0, expenses_year: 0,
  net_month: 0, cotisations_estimated: 0, threshold_percentage: 0,
})

const threshold = computed(() => proStore.proProfile?.revenue_threshold || 77700)

const recentTransactions = computed(() => proStore.proTransactions.slice(0, 10))

onMounted(async () => {
  await Promise.all([
    proStore.fetchProfile(),
    proStore.fetchDashboard(),
    proStore.fetchTransactions(),
  ])

  if (proStore.proProfile) {
    profileForm.value = {
      siret: proStore.proProfile.siret || '',
      activity_type: proStore.proProfile.activity_type,
      cotisation_rate: proStore.proProfile.cotisation_rate,
      declaration_frequency: proStore.proProfile.declaration_frequency,
      revenue_threshold: proStore.proProfile.revenue_threshold,
    }
  }
})

async function saveProfile() {
  await proStore.updateProfile(profileForm.value)
  await proStore.fetchDashboard()
  showProfileModal.value = false
}
</script>
