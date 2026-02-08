<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      :title="t('category.editCategory')"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
    >
      <n-form :model="formData">
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
            {{ t('common.save') }}
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
  NCheckboxGroup, NCheckbox, NSpace, NButton
} from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface CategoryData {
  id: string
  name: string
  amount: number
  tags: string[]
  isSubcategory: boolean
}

interface Props {
  show: boolean
  isMobile: boolean
  loading: boolean
  category: CategoryData | null
  maxAmount?: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: CategoryData]
}>()

const formData = ref<CategoryData>({
  id: '',
  name: '',
  amount: 0,
  tags: [],
  isSubcategory: false,
})

watch(() => props.category, (newVal) => {
  if (newVal) {
    formData.value = { ...newVal }
  }
}, { immediate: true })

const handleSubmit = () => {
  emit('submit', { ...formData.value })
}
</script>
