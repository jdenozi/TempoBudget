<template>
  <n-modal
    :show="show"
    :mask-closable="false"
    :close-on-esc="false"
    preset="card"
    :title="t('pro.setup.title')"
    style="max-width: 600px; width: 95%;"
  >
    <n-steps :current="currentStep" size="small" style="margin-bottom: 24px;">
      <n-step :title="t('pro.setup.step1')" />
      <n-step :title="t('pro.setup.step2')" />
      <n-step :title="t('pro.setup.step3')" />
      <n-step :title="t('pro.setup.step4')" />
    </n-steps>

    <!-- Step 1: Legal Form -->
    <div v-if="currentStep === 1" class="step-content">
      <h3>{{ t('pro.setup.chooseLegalForm') }}</h3>
      <p class="step-description">{{ t('pro.setup.legalFormDesc') }}</p>

      <n-radio-group v-model:value="form.legal_form" class="legal-form-group">
        <n-space vertical :size="12">
          <n-radio value="micro" class="legal-form-option">
            <div class="option-content">
              <strong>{{ t('pro.profile.legalForms.micro') }}</strong>
              <span class="option-desc">{{ t('pro.setup.microDesc') }}</span>
            </div>
          </n-radio>
          <n-radio value="ei_reel" class="legal-form-option">
            <div class="option-content">
              <strong>{{ t('pro.profile.legalForms.ei_reel') }}</strong>
              <span class="option-desc">{{ t('pro.setup.eiReelDesc') }}</span>
            </div>
          </n-radio>
          <n-radio value="eurl" class="legal-form-option">
            <div class="option-content">
              <strong>{{ t('pro.profile.legalForms.eurl') }}</strong>
              <span class="option-desc">{{ t('pro.setup.eurlDesc') }}</span>
            </div>
          </n-radio>
          <n-radio value="sasu" class="legal-form-option">
            <div class="option-content">
              <strong>{{ t('pro.profile.legalForms.sasu') }}</strong>
              <span class="option-desc">{{ t('pro.setup.sasuDesc') }}</span>
            </div>
          </n-radio>
        </n-space>
      </n-radio-group>
    </div>

    <!-- Step 2: Activity & Rates -->
    <div v-if="currentStep === 2" class="step-content">
      <h3>{{ t('pro.setup.activityTitle') }}</h3>
      <p class="step-description">{{ t('pro.setup.activityDesc') }}</p>

      <n-form-item :label="t('pro.profile.activityType')" v-if="form.legal_form === 'micro'">
        <n-select
          v-model:value="form.activity_type"
          :options="activityOptions"
          @update:value="handleActivityChange"
        />
      </n-form-item>

      <n-form-item :label="t('pro.profile.cotisationRate')">
        <n-input-number
          v-model:value="form.cotisation_rate"
          :min="0"
          :max="100"
          :precision="1"
          style="width: 100%;"
        >
          <template #suffix>%</template>
        </n-input-number>
      </n-form-item>

      <n-form-item :label="t('pro.profile.declarationFrequency')">
        <n-radio-group v-model:value="form.declaration_frequency">
          <n-radio-button value="monthly">{{ t('pro.profile.monthly') }}</n-radio-button>
          <n-radio-button value="quarterly">{{ t('pro.profile.quarterly') }}</n-radio-button>
        </n-radio-group>
      </n-form-item>

      <!-- EURL specific -->
      <n-form-item v-if="form.legal_form === 'eurl'" :label="t('pro.profile.eurlTaxOption')">
        <n-radio-group v-model:value="form.eurl_tax_option">
          <n-radio-button value="ir">{{ t('pro.profile.eurlIR') }}</n-radio-button>
          <n-radio-button value="is">{{ t('pro.profile.eurlIS') }}</n-radio-button>
        </n-radio-group>
      </n-form-item>

      <!-- SASU/SAS specific -->
      <template v-if="form.legal_form === 'sasu' || form.legal_form === 'sas'">
        <n-form-item :label="t('pro.profile.salaryGrossMonthly')">
          <n-input-number v-model:value="form.salary_gross_monthly" :min="0" style="width: 100%;">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('pro.profile.dividendsYearly')">
          <n-input-number v-model:value="form.dividends_yearly" :min="0" style="width: 100%;">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
      </template>
    </div>

    <!-- Step 3: ACRE & TMI -->
    <div v-if="currentStep === 3" class="step-content">
      <h3>{{ t('pro.setup.acreTitle') }}</h3>
      <p class="step-description">{{ t('pro.setup.acreDesc') }}</p>

      <n-form-item :label="t('pro.profile.acreEnabled')">
        <n-switch v-model:value="acreEnabled" />
      </n-form-item>

      <n-form-item v-if="acreEnabled" :label="t('pro.profile.acreStartDate') + ' *'" required>
        <n-date-picker v-model:value="acreStartDateTs" type="date" style="width: 100%;" :status="acreEnabled && !acreStartDateTs ? 'error' : undefined" />
      </n-form-item>

      <n-alert v-if="acreEnabled" type="success" style="margin-bottom: 16px;">
        {{ t('pro.setup.acreInfo') }}
      </n-alert>

      <n-divider />

      <n-form-item :label="t('pro.profile.foyerTmi')">
        <n-select
          v-model:value="form.foyer_tmi"
          :options="tmiOptions"
          :placeholder="t('pro.profile.foyerTmiPlaceholder')"
          clearable
        />
      </n-form-item>
      <p class="field-hint">{{ t('pro.setup.tmiHint') }}</p>
    </div>

    <!-- Step 4: Company Info -->
    <div v-if="currentStep === 4" class="step-content">
      <h3>{{ t('pro.setup.companyTitle') }}</h3>
      <p class="step-description">{{ t('pro.setup.companyDesc') }}</p>

      <n-alert v-if="!canFinish" type="warning" style="margin-bottom: 16px;">
        {{ t('pro.setup.requiredFields') }}
      </n-alert>

      <n-form-item :label="t('pro.profile.companyName') + ' *'">
        <n-input v-model:value="form.company_name" :placeholder="t('pro.setup.companyNamePlaceholder')" :status="!canFinish && !form.company_name.trim() ? 'warning' : undefined" />
      </n-form-item>

      <n-form-item :label="t('pro.profile.siret') + ' *'">
        <n-input v-model:value="form.siret" placeholder="123 456 789 00012" :status="!canFinish && !form.siret.trim() ? 'warning' : undefined" />
      </n-form-item>

      <n-grid :cols="2" :x-gap="12">
        <n-gi>
          <n-form-item :label="t('pro.profile.street')">
            <n-input v-model:value="form.street" />
          </n-form-item>
        </n-gi>
        <n-gi>
          <n-form-item :label="t('pro.profile.postalCode')">
            <n-input v-model:value="form.postal_code" placeholder="75001" />
          </n-form-item>
        </n-gi>
      </n-grid>

      <n-form-item :label="t('pro.profile.city')">
        <n-input v-model:value="form.city" />
      </n-form-item>

      <n-alert type="info">
        {{ t('pro.setup.optionalInfo') }}
      </n-alert>
    </div>

    <template #footer>
      <n-flex justify="space-between">
        <n-button v-if="currentStep > 1" @click="prevStep">
          ← {{ t('common.back') }}
        </n-button>
        <div v-else />

        <n-button
          v-if="currentStep < 4"
          type="primary"
          @click="nextStep"
          :disabled="!canProceed"
        >
          {{ t('pro.setup.next') }} →
        </n-button>
        <n-button
          v-else
          type="primary"
          :loading="saving"
          :disabled="!canFinish"
          @click="finishSetup"
        >
          {{ t('pro.setup.finish') }}
        </n-button>
      </n-flex>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NModal, NSteps, NStep, NRadioGroup, NRadio, NRadioButton, NSpace,
  NFormItem, NSelect, NInputNumber, NInput, NSwitch, NDatePicker,
  NButton, NFlex, NAlert, NDivider, NGrid, NGi
} from 'naive-ui'
import { proProfileAPI } from '@/services/api'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'complete'): void
}>()

const { t } = useI18n()

const currentStep = ref(1)
const saving = ref(false)

const form = ref({
  legal_form: 'micro' as 'micro' | 'ei_reel' | 'eurl' | 'sasu' | 'sas',
  activity_type: 'services',
  cotisation_rate: 21.2,
  declaration_frequency: 'quarterly',
  eurl_tax_option: 'ir' as 'ir' | 'is',
  salary_gross_monthly: 0,
  dividends_yearly: 0,
  foyer_tmi: null as number | null,
  company_name: '',
  siret: '',
  street: '',
  postal_code: '',
  city: '',
  acre_enabled: 0,
  acre_start_date: null as string | null,
})

const acreEnabled = ref(false)
const acreStartDateTs = ref<number | null>(null)

watch(acreEnabled, (val) => {
  form.value.acre_enabled = val ? 1 : 0
})

watch(acreStartDateTs, (val) => {
  form.value.acre_start_date = val ? new Date(val).toISOString().slice(0, 10) : null
})

const activityOptions = computed(() => [
  { label: t('pro.profile.services'), value: 'services' },
  { label: t('pro.profile.liberal'), value: 'liberal' },
  { label: t('pro.profile.vente'), value: 'vente' },
  { label: t('pro.profile.artisan'), value: 'artisan' },
  { label: t('pro.profile.commercant'), value: 'commercant' },
])

const tmiOptions = [
  { label: '0%', value: 0 },
  { label: '11%', value: 11 },
  { label: '30%', value: 30 },
  { label: '41%', value: 41 },
  { label: '45%', value: 45 },
]

const ACTIVITY_PRESETS: Record<string, number> = {
  services: 21.2,
  liberal: 23.1,
  vente: 12.3,
  artisan: 21.2,
  commercant: 12.3,
}

function handleActivityChange(value: string) {
  form.value.cotisation_rate = ACTIVITY_PRESETS[value] || 21.2
}

const canProceed = computed(() => {
  if (currentStep.value === 1) return !!form.value.legal_form
  if (currentStep.value === 2) return form.value.cotisation_rate > 0
  if (currentStep.value === 3) {
    // If ACRE is enabled, start date is required
    if (acreEnabled.value && !acreStartDateTs.value) return false
    return true
  }
  return true
})

const canFinish = computed(() => {
  // At least company name OR siret must be filled
  const hasCompanyName = form.value.company_name.trim().length > 0
  const hasSiret = form.value.siret.trim().length > 0
  return hasCompanyName || hasSiret
})

function nextStep() {
  if (currentStep.value < 4) currentStep.value++
}

function prevStep() {
  if (currentStep.value > 1) currentStep.value--
}

async function finishSetup() {
  saving.value = true
  try {
    await proProfileAPI.update(form.value)
    emit('complete')
    emit('update:show', false)
  } catch (error) {
    console.error('Error saving profile:', error)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.step-content {
  min-height: 280px;
}

.step-content h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.step-description {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 20px;
  font-size: 14px;
}

.legal-form-group {
  width: 100%;
}

.legal-form-option {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  margin-bottom: 4px;
}

.legal-form-option:hover {
  background: rgba(255, 255, 255, 0.06);
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: normal;
}

.field-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: -8px;
}
</style>
