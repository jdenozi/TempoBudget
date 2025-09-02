<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      title="Change Password"
      :bordered="false"
      size="huge"
      style="width: 400px; max-width: 95vw;"
    >
      <n-form ref="formRef" :model="formData" :rules="rules">
        <n-form-item label="Current Password" path="currentPassword">
          <n-input
            v-model:value="formData.currentPassword"
            type="password"
            show-password-on="click"
            placeholder="Enter your current password"
          />
        </n-form-item>

        <n-form-item label="New Password" path="newPassword">
          <n-input
            v-model:value="formData.newPassword"
            type="password"
            show-password-on="click"
            placeholder="Enter your new password"
          />
        </n-form-item>

        <n-form-item label="Confirm New Password" path="confirmPassword">
          <n-input
            v-model:value="formData.confirmPassword"
            type="password"
            show-password-on="click"
            placeholder="Confirm your new password"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">Cancel</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            Change Password
          </n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NModal, NCard, NForm, NFormItem, NInput, NSpace, NButton, type FormInst, type FormRules } from 'naive-ui'

interface Props {
  show: boolean
  loading: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: { currentPassword: string; newPassword: string }]
}>()

const formRef = ref<FormInst | null>(null)

const formData = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const rules: FormRules = {
  currentPassword: [{ required: true, message: 'Current password is required' }],
  newPassword: [
    { required: true, message: 'New password is required' },
    { min: 6, message: 'Password must be at least 6 characters' }
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm your new password' },
    {
      validator: (_rule, value) => value === formData.value.newPassword,
      message: 'Passwords do not match'
    }
  ]
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    emit('submit', {
      currentPassword: formData.value.currentPassword,
      newPassword: formData.value.newPassword
    })
  } catch {
    // Validation failed
  }
}

const resetForm = () => {
  formData.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
}

defineExpose({ resetForm })
</script>
