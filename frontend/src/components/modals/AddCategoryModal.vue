<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      :title="t('category.addCategory')"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
    >
      <n-form ref="formRef" :model="formData">
        <n-form-item :label="t('transaction.type')">
          <n-radio-group v-model:value="formData.isSubcategory">
            <n-space>
              <n-radio :value="false">{{ t('category.title') }}</n-radio>
              <n-radio :value="true">{{ t('category.subcategory') }}</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>

        <n-form-item v-if="formData.isSubcategory" :label="t('category.parentCategory')">
          <n-select
            v-model:value="formData.parentId"
            :options="parentCategoryOptions"
            :placeholder="t('category.parentCategory')"
          />
        </n-form-item>

        <n-form-item :label="t('category.categoryName')">
          <n-input v-model:value="formData.name" :placeholder="t('category.categoryName')" />
        </n-form-item>

        <n-form-item :label="t('budget.amount')">
          <n-input-number
            v-model:value="formData.amount"
            :min="0"
            :max="formData.isSubcategory ? maxAmount : undefined"
            :precision="2"
            style="width: 100%;"
          >
            <template #suffix>€</template>
          </n-input-number>
          <template v-if="formData.isSubcategory && maxAmount !== undefined" #feedback>
            {{ t('budget.remaining') }}: {{ maxAmount.toFixed(2) }} €
          </template>
        </n-form-item>

        <n-form-item label="Tags">
          <n-checkbox-group v-model:value="formData.tags">
            <n-space>
              <n-checkbox value="besoin">{{ t('tags.need') }}</n-checkbox>
              <n-checkbox value="loisir">{{ t('tags.leisure') }}</n-checkbox>
              <n-checkbox value="épargne">{{ t('tags.savings') }}</n-checkbox>
              <n-checkbox value="crédit">{{ t('tags.credit') }}</n-checkbox>
              <n-checkbox value="revenu">{{ t('tags.income') }}</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            {{ t('common.add') }}
          </n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  NModal, NCard, NForm, NFormItem, NInput, NInputNumber,
  NRadioGroup, NRadio, NSelect, NCheckboxGroup, NCheckbox,
  NSpace, NButton
} from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  show: boolean
  isMobile: boolean
  parentCategoryOptions: { label: string; value: string }[]
  loading: boolean
  initialParentId?: string | null
  maxAmount?: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: { name: string; amount: number; parentId: string | null; tags: string[]; isSubcategory: boolean }]
}>()

const formRef = ref<any>(null)

const formData = ref({
  name: '',
  amount: 0,
  parentId: null as string | null,
  tags: [] as string[],
  isSubcategory: false,
})

watch(() => props.show, (newVal) => {
  if (newVal && props.initialParentId) {
    formData.value.parentId = props.initialParentId
    formData.value.isSubcategory = true
  }
})

watch(() => props.initialParentId, (newVal) => {
  if (newVal) {
    formData.value.parentId = newVal
    formData.value.isSubcategory = true
  }
})

const handleSubmit = () => {
  emit('submit', { ...formData.value })
}

const resetForm = () => {
  formData.value = {
    name: '',
    amount: 0,
    parentId: null,
    tags: [],
    isSubcategory: false,
  }
}

defineExpose({ resetForm })
</script>
