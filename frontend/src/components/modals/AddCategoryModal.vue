<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      title="Add Category"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
    >
      <n-form ref="formRef" :model="formData">
        <n-form-item label="Type">
          <n-radio-group v-model:value="formData.isSubcategory">
            <n-space>
              <n-radio :value="false">Category</n-radio>
              <n-radio :value="true">Subcategory</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>

        <n-form-item v-if="formData.isSubcategory" label="Parent Category">
          <n-select
            v-model:value="formData.parentId"
            :options="parentCategoryOptions"
            placeholder="Select parent category"
          />
        </n-form-item>

        <n-form-item label="Name">
          <n-input v-model:value="formData.name" placeholder="Housing" />
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
            Add
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

interface Props {
  show: boolean
  isMobile: boolean
  parentCategoryOptions: { label: string; value: string }[]
  loading: boolean
  initialParentId?: string | null
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
