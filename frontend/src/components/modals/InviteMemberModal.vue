<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      title="Invite a Member"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
    >
      <n-form ref="formRef" :model="formData">
        <n-form-item label="User Email">
          <n-input
            v-model:value="formData.email"
            placeholder="email@example.com"
            type="email"
          />
        </n-form-item>

        <n-form-item label="Role">
          <n-radio-group v-model:value="formData.role">
            <n-space>
              <n-radio value="member">Member</n-radio>
              <n-radio value="owner">Owner</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">Cancel</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            Invite
          </n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  NModal, NCard, NForm, NFormItem, NInput,
  NRadioGroup, NRadio, NSpace, NButton
} from 'naive-ui'

interface Props {
  show: boolean
  isMobile: boolean
  loading: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: { email: string; role: 'member' | 'owner' }]
}>()

const formRef = ref<any>(null)

const formData = ref({
  email: '',
  role: 'member' as 'member' | 'owner',
})

const handleSubmit = () => {
  emit('submit', { ...formData.value })
}

const resetForm = () => {
  formData.value = { email: '', role: 'member' }
}

defineExpose({ resetForm })
</script>
