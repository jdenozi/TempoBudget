<template>
  <n-card title="Budget Members">
    <n-space vertical>
      <!-- Share total warning -->
      <n-alert
        v-if="members.length > 0 && Math.abs(totalShares - 100) > 0.01"
        :type="totalShares < 100 ? 'warning' : 'error'"
        :title="totalShares < 100 ? 'Shares incomplete' : 'Shares exceed 100%'"
      >
        Total shares: {{ totalShares.toFixed(1) }}% (should be 100%)
      </n-alert>

      <!-- Member list with shares -->
      <n-list v-if="members.length > 0" bordered>
        <n-list-item v-for="member in members" :key="member.id">
          <template #prefix>
            <n-avatar
              :size="40"
              round
              :src="member.user_avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${member.user_name}`"
            />
          </template>

          <n-thing :title="member.user_name">
            <template #description>
              <div>{{ member.user_email }}</div>
              <div style="margin-top: 8px; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 12px; color: #888;">Share:</span>
                <n-input-number
                  v-if="isOwner"
                  :value="member.share"
                  :min="0"
                  :max="100"
                  :precision="1"
                  :step="5"
                  size="small"
                  :style="{ width: '100px' }"
                  :loading="updatingShareId === member.id"
                  @update:value="(v) => $emit('updateShare', member.id, v || 0)"
                >
                  <template #suffix>%</template>
                </n-input-number>
                <span v-else style="font-weight: bold;">{{ member.share }}%</span>
              </div>
            </template>
          </n-thing>

          <template #suffix>
            <n-space align="center">
              <n-tag :type="member.role === 'owner' ? 'success' : 'default'" size="small">
                {{ member.role === 'owner' ? 'Owner' : 'Member' }}
              </n-tag>

              <n-popconfirm
                v-if="member.role !== 'owner' && isOwner"
                @positive-click="$emit('removeMember', member.id)"
              >
                <template #trigger>
                  <n-button size="small" type="error" quaternary circle>
                    <template #icon>
                      <n-icon><TrashOutline /></n-icon>
                    </template>
                  </n-button>
                </template>
                Remove this member from the budget?
              </n-popconfirm>
            </n-space>
          </template>
        </n-list-item>
      </n-list>

      <n-empty v-else description="No members" />
    </n-space>

    <template #footer>
      <n-button
        v-if="isOwner"
        @click="$emit('invite')"
        type="primary"
        size="small"
      >
        Invite a Member
      </n-button>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  NCard, NSpace, NList, NListItem, NThing, NAvatar,
  NInputNumber, NTag, NButton, NIcon, NPopconfirm, NAlert, NEmpty
} from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import type { BudgetMemberWithUser } from '@/services/api'

interface Props {
  members: BudgetMemberWithUser[]
  isOwner: boolean
  updatingShareId: string | null
}

const props = defineProps<Props>()

defineEmits<{
  'updateShare': [memberId: string, share: number]
  'removeMember': [memberId: string]
  'invite': []
}>()

const totalShares = computed(() => {
  return props.members.reduce((sum, m) => sum + m.share, 0)
})
</script>
