<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      :title="t('profile.changePassword')"
      :bordered="false"
      size="huge"
      style="width: 400px; max-width: 95vw;"
    >
      <n-form ref="formRef" :model="formData" :rules="rules">
        <n-form-item :label="t('profile.currentPassword')" path="currentPassword">
          <n-input
            v-model:value="formData.currentPassword"
            type="password"
            show-password-on="click"
            :placeholder="t('placeholders.enterCurrentPassword')"
          />
        </n-form-item>

        <n-form-item :label="t('profile.newPassword')" path="newPassword">
          <n-input
            v-model:value="formData.newPassword"
            type="password"
            show-password-on="click"
            :placeholder="t('placeholders.enterNewPassword')"
          />
        </n-form-item>

        <n-form-item :label="t('auth.confirmPassword')" path="confirmPassword">
          <n-input
            v-model:value="formData.confirmPassword"
            type="password"
            show-password-on="click"
            :placeholder="t('placeholders.confirmNewPassword')"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            {{ t('profile.changePassword') }}
          </n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NModal, NCard, NForm, NFormItem, NInput, NSpace, NButton, type FormInst, type FormRules } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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

const rules = computed<FormRules>(() => ({
  currentPassword: [{ required: true, message: t('errors.required') }],
  newPassword: [
    { required: true, message: t('errors.required') },
    { min: 6, message: t('errors.minLength', { min: 6 }) }
  ],
  confirmPassword: [
    { required: true, message: t('errors.required') },
    {
      validator: (_rule, value) => value === formData.value.newPassword,
      message: t('errors.passwordMismatch')
    }
  ]
}))

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
