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

        <!-- Parent category selector for subcategories -->
        <n-form-item v-if="formData.isSubcategory && parentCategoryOptions.length > 0" :label="t('category.parentCategory')">
          <n-select
            v-model:value="formData.parentId"
            :options="parentCategoryOptions"
            :placeholder="t('category.selectParent')"
          />
        </n-form-item>

        <n-form-item :label="t('budget.amount')">
          <n-input-number
            v-model:value="formData.amount"
            :min="0"
            :precision="2"
            style="width: 100%;"
          >
            <template #suffix>€</template>
          </n-input-number>
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
  NCheckboxGroup, NCheckbox, NSpace, NButton, NSelect
} from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface CategoryData {
  id: string
  name: string
  amount: number
  tags: string[]
  isSubcategory: boolean
  parentId?: string | null
}

interface ParentOption {
  label: string
  value: string
}

interface Props {
  show: boolean
  isMobile: boolean
  loading: boolean
  category: CategoryData | null
  parentCategoryOptions?: ParentOption[]
}

const props = withDefaults(defineProps<Props>(), {
  parentCategoryOptions: () => []
})

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
  parentId: null,
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
