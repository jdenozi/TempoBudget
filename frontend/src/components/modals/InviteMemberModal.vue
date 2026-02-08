<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)">
    <n-card
      :title="t('member.addMember')"
      :bordered="false"
      size="huge"
      role="dialog"
      :style="{ maxWidth: isMobile ? '95vw' : '400px' }"
    >
      <n-form ref="formRef" :model="formData">
        <n-form-item :label="t('auth.email')">
          <n-input
            v-model:value="formData.email"
            :placeholder="t('placeholders.enterEmail')"
            type="email"
          />
        </n-form-item>

        <n-form-item :label="t('member.role')">
          <n-radio-group v-model:value="formData.role">
            <n-space>
              <n-radio value="member">{{ t('member.memberRole') }}</n-radio>
              <n-radio value="owner">{{ t('member.owner') }}</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="$emit('update:show', false)">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            {{ t('member.addMember') }}
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
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
