<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      title="Edit Category"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
    >
      <n-form :model="formData">
        <n-form-item label="Name">
          <n-input v-model:value="formData.name" placeholder="Category name" />
        </n-form-item>

        <n-form-item v-if="!formData.isSubcategory" label="Budget Amount">
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
              <n-checkbox value="crédit">Crédit</n-checkbox>
              <n-checkbox value="besoin">Besoin</n-checkbox>
              <n-checkbox value="loisir">Loisir</n-checkbox>
              <n-checkbox value="épargne">Épargne</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">Cancel</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            Save
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
