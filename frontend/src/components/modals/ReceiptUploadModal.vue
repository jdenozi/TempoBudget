<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      :title="t('receipt.upload')"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '600px', width: '100%' }"
    >
      <!-- Step 1: Upload -->
      <template v-if="step === 'upload'">
        <n-upload
          accept="image/*"
          :max="1"
          :show-file-list="false"
          :custom-request="handleUpload"
          :disabled="uploading"
        >
          <n-upload-dragger>
            <div style="padding: 40px;">
              <n-icon size="48" :depth="3">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19.35 10.04A7.49 7.49 0 0012 4C9.11 4 6.6 5.64 5.35 8.04A5.994 5.994 0 000 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
                </svg>
              </n-icon>
              <n-text style="display: block; margin-top: 12px;">
                {{ t('receipt.uploadHint') }}
              </n-text>
            </div>
          </n-upload-dragger>
        </n-upload>

        <n-spin v-if="uploading" style="margin-top: 20px;">
          <template #description>{{ t('receipt.processing') }}</template>
        </n-spin>

        <n-alert v-if="uploadError" type="error" style="margin-top: 16px;">
          {{ uploadError }}
        </n-alert>
      </template>

      <!-- Step 2: Preview & Edit -->
      <template v-else-if="step === 'preview' && ocrResult">
        <n-space vertical size="large">
          <!-- Confidence indicator -->
          <n-alert :type="confidenceType">
            {{ t('receipt.confidence') }}: {{ confidenceLabel }}
            ({{ Math.round(ocrResult.confidence * 100) }}%)
          </n-alert>

          <!-- Extracted image preview -->
          <n-image
            v-if="previewUrl"
            :src="previewUrl"
            height="150"
            object-fit="contain"
            style="width: 100%; border-radius: 8px;"
          />

          <!-- Editable form -->
          <n-form ref="formRef" :model="formData">
            <n-form-item :label="t('transaction.type')">
              <n-radio-group v-model:value="formData.transaction_type">
                <n-space>
                  <n-radio value="expense">
                    <n-tag type="error">{{ t('transaction.expense') }}</n-tag>
                  </n-radio>
                  <n-radio value="income">
                    <n-tag type="success">{{ t('transaction.income') }}</n-tag>
                  </n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>

            <n-form-item :label="t('category.title')">
              <n-select
                v-model:value="formData.category_id"
                :options="categoryOptions"
                :placeholder="t('placeholders.selectCategory')"
              />
            </n-form-item>

            <n-form-item :label="t('transaction.amount')">
              <n-input-number
                v-model:value="formData.amount"
                :min="0.01"
                :precision="2"
                style="width: 100%;"
              >
                <template #suffix>€</template>
              </n-input-number>
            </n-form-item>

            <n-form-item :label="t('transaction.transactionTitle')">
              <n-input v-model:value="formData.title" :placeholder="t('transaction.transactionTitle')" />
            </n-form-item>

            <n-form-item :label="t('transaction.date')">
              <n-date-picker
                v-model:value="formData.date"
                type="date"
                style="width: 100%;"
              />
            </n-form-item>

            <n-form-item :label="t('transaction.comment')">
              <n-input
                v-model:value="formData.comment"
                type="textarea"
                :rows="2"
                :placeholder="t('transaction.comment')"
              />
            </n-form-item>
          </n-form>

          <!-- Raw OCR text (collapsible) -->
          <n-collapse>
            <n-collapse-item :title="t('receipt.rawText')">
              <n-code :code="ocrResult.raw_text" style="max-height: 200px; overflow: auto;" />
            </n-collapse-item>
          </n-collapse>
        </n-space>
      </template>

      <template #footer>
        <n-space justify="space-between" style="width: 100%;">
          <n-button v-if="step === 'preview'" @click="resetToUpload">
            {{ t('common.back') }}
          </n-button>
          <div v-else></div>

          <n-space>
            <n-button @click="$emit('update:show', false)">{{ t('common.cancel') }}</n-button>
            <template v-if="step === 'preview'">
              <n-button type="warning" :loading="submitting" @click="handleSubmit(true)">
                {{ t('receipt.createPending') }}
              </n-button>
              <n-button type="primary" :loading="submitting" @click="handleSubmit(false)">
                {{ t('receipt.createConfirmed') }}
              </n-button>
            </template>
          </n-space>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NModal, NCard, NUpload, NUploadDragger, NIcon, NText, NSpin,
  NAlert, NImage, NForm, NFormItem, NInput, NInputNumber, NSelect,
  NDatePicker, NRadioGroup, NRadio, NTag, NSpace, NButton,
  NCollapse, NCollapseItem, NCode, useMessage
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { UploadCustomRequestOptions } from 'naive-ui'
import { transactionsAPI, type ReceiptOCRResult } from '@/services/api'
import { formatDateLocal, parseDateToTimestamp } from '@/utils/date'

const { t } = useI18n()
const message = useMessage()

interface Props {
  show: boolean
  isMobile: boolean
  budgetId: string
  categoryOptions: { label: string; value: string }[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'success': []
}>()

const step = ref<'upload' | 'preview'>('upload')
const uploading = ref(false)
const submitting = ref(false)
const uploadError = ref('')
const ocrResult = ref<ReceiptOCRResult | null>(null)
const previewUrl = ref('')

const formData = ref({
  transaction_type: 'expense' as 'expense' | 'income',
  category_id: null as string | null,
  amount: 0,
  title: '',
  date: Date.now(),
  comment: '',
})

const confidenceType = computed(() => {
  if (!ocrResult.value) return 'info'
  if (ocrResult.value.confidence >= 0.7) return 'success'
  if (ocrResult.value.confidence >= 0.4) return 'warning'
  return 'error'
})

const confidenceLabel = computed(() => {
  if (!ocrResult.value) return ''
  if (ocrResult.value.confidence >= 0.7) return t('receipt.confidenceHigh')
  if (ocrResult.value.confidence >= 0.4) return t('receipt.confidenceMedium')
  return t('receipt.confidenceLow')
})

watch(() => props.show, (newVal) => {
  if (!newVal) {
    resetToUpload()
  }
})

const handleUpload = async (options: UploadCustomRequestOptions) => {
  const { file } = options

  if (!file.file) {
    options.onError()
    return
  }

  uploading.value = true
  uploadError.value = ''

  try {
    const result = await transactionsAPI.uploadReceipt(props.budgetId, file.file)
    ocrResult.value = result

    // Pre-fill form with extracted data
    formData.value = {
      transaction_type: 'expense',
      category_id: props.categoryOptions[0]?.value || null,
      amount: result.amount || 0,
      title: result.title || '',
      date: result.date ? parseDateToTimestamp(result.date) : Date.now(),
      comment: '',
    }

    // Create preview URL for the uploaded image
    previewUrl.value = URL.createObjectURL(file.file)

    step.value = 'preview'
    options.onFinish()
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || t('receipt.uploadError')
    uploadError.value = errorMsg
    options.onError()
  } finally {
    uploading.value = false
  }
}

const handleSubmit = async (createAsPending: boolean) => {
  if (!ocrResult.value || !formData.value.category_id || !formData.value.amount) {
    message.error(t('errors.required'))
    return
  }

  submitting.value = true

  try {
    await transactionsAPI.confirmReceipt(props.budgetId, {
      category_id: formData.value.category_id,
      title: formData.value.title || t('receipt.import'),
      amount: formData.value.amount,
      transaction_type: formData.value.transaction_type,
      date: formatDateLocal(formData.value.date),
      comment: formData.value.comment || undefined,
      temp_image_path: ocrResult.value.temp_image_path,
      create_as_pending: createAsPending,
    })

    message.success(t('receipt.transactionCreated'))
    emit('success')
    emit('update:show', false)
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || t('errors.generic')
    message.error(errorMsg)
  } finally {
    submitting.value = false
  }
}

const resetToUpload = () => {
  step.value = 'upload'
  ocrResult.value = null
  uploadError.value = ''
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
  formData.value = {
    transaction_type: 'expense',
    category_id: null,
    amount: 0,
    title: '',
    date: Date.now(),
    comment: '',
  }
}
</script>
