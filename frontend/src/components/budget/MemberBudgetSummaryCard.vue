<!--
  Member Budget Summary Card

  Displays budget allocation per member based on their share ratios.
  Shows:
  - Member share percentage
  - Allocated budget (total budget × share)
  - Amount spent by member
  - Remaining budget per member
-->

<template>
  <n-card title="Budget par membre">
    <n-space vertical size="large">
      <!-- Summary table -->
      <n-data-table
        v-if="!isMobile"
        :columns="columns"
        :data="memberBudgets"
        :bordered="false"
        size="small"
      />

      <!-- Mobile view: cards -->
      <n-space v-else vertical>
        <n-card
          v-for="mb in memberBudgets"
          :key="mb.userId"
          size="small"
          :bordered="true"
        >
          <template #header>
            <n-space align="center">
              <n-avatar
                :size="32"
                round
                :src="mb.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${mb.name}`"
              />
              <span>{{ mb.name }}</span>
              <n-tag size="small" type="info">{{ mb.share }}%</n-tag>
            </n-space>
          </template>

          <n-grid :cols="2" :x-gap="12" :y-gap="8">
            <n-gi>
              <div style="font-size: 12px; color: #888;">Budget alloué</div>
              <div style="font-weight: bold;">{{ mb.allocatedBudget.toFixed(2) }} €</div>
            </n-gi>
            <n-gi>
              <div style="font-size: 12px; color: #888;">Dépensé</div>
              <div style="font-weight: bold;">{{ mb.spent.toFixed(2) }} €</div>
            </n-gi>
            <n-gi>
              <div style="font-size: 12px; color: #888;">Restant</div>
              <div :style="{ fontWeight: 'bold', color: mb.remaining >= 0 ? '#18a058' : '#d03050' }">
                {{ mb.remaining.toFixed(2) }} €
              </div>
            </n-gi>
            <n-gi>
              <div style="font-size: 12px; color: #888;">Progression</div>
              <n-progress
                type="line"
                :percentage="Math.min(mb.percentage, 100)"
                :status="mb.percentage > 100 ? 'error' : mb.percentage > 80 ? 'warning' : 'success'"
                :show-indicator="false"
                style="width: 100%;"
              />
              <div style="font-size: 11px; text-align: right;">{{ mb.percentage.toFixed(0) }}%</div>
            </n-gi>
          </n-grid>
        </n-card>
      </n-space>

      <!-- Total row summary -->
      <n-divider style="margin: 8px 0;" />
      <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="8">
        <n-gi>
          <div style="font-size: 12px; color: #888;">Budget total</div>
          <div style="font-weight: bold; font-size: 16px;">{{ totalBudget.toFixed(2) }} €</div>
        </n-gi>
        <n-gi>
          <div style="font-size: 12px; color: #888;">Total dépensé</div>
          <div style="font-weight: bold; font-size: 16px;">{{ totalSpent.toFixed(2) }} €</div>
        </n-gi>
        <n-gi>
          <div style="font-size: 12px; color: #888;">Total restant</div>
          <div :style="{ fontWeight: 'bold', fontSize: '16px', color: totalRemaining >= 0 ? '#18a058' : '#d03050' }">
            {{ totalRemaining.toFixed(2) }} €
          </div>
        </n-gi>
        <n-gi>
          <div style="font-size: 12px; color: #888;">Progression globale</div>
          <n-progress
            type="line"
            :percentage="Math.min(totalPercentage, 100)"
            :status="totalPercentage > 100 ? 'error' : totalPercentage > 80 ? 'warning' : 'success'"
            style="width: 100%;"
          >
            {{ totalPercentage.toFixed(0) }}%
          </n-progress>
        </n-gi>
      </n-grid>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import {
  NCard, NSpace, NDataTable, NAvatar, NTag, NGrid, NGi,
  NProgress, NDivider
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { BudgetMemberWithUser, Transaction } from '@/services/api'

interface Props {
  members: BudgetMemberWithUser[]
  transactions: Transaction[]
  totalBudget: number
  isMobile: boolean
}

const props = defineProps<Props>()

interface MemberBudget {
  userId: string
  name: string
  avatar?: string
  share: number
  allocatedBudget: number
  spent: number
  remaining: number
  percentage: number
}

/** Calculate budget allocation per member */
const memberBudgets = computed<MemberBudget[]>(() => {
  return props.members.map(member => {
    const allocatedBudget = props.totalBudget * (member.share / 100)

    // Calculate spent by this member (transactions they paid for)
    const spent = props.transactions
      .filter(t => t.paid_by_user_id === member.user_id && t.transaction_type === 'expense')
      .reduce((sum, t) => sum + t.amount, 0)

    const remaining = allocatedBudget - spent
    const percentage = allocatedBudget > 0 ? (spent / allocatedBudget) * 100 : 0

    return {
      userId: member.user_id,
      name: member.user_name,
      avatar: member.user_avatar,
      share: member.share,
      allocatedBudget,
      spent,
      remaining,
      percentage,
    }
  })
})

const totalSpent = computed(() => memberBudgets.value.reduce((sum, mb) => sum + mb.spent, 0))
const totalRemaining = computed(() => props.totalBudget - totalSpent.value)
const totalPercentage = computed(() => props.totalBudget > 0 ? (totalSpent.value / props.totalBudget) * 100 : 0)

/** Table columns for desktop view */
const columns = computed<DataTableColumns<MemberBudget>>(() => [
  {
    title: 'Membre',
    key: 'name',
    render: (row) => {
      return h('div', { style: { display: 'flex', alignItems: 'center', gap: '8px' } }, [
        h(NAvatar, {
          size: 28,
          round: true,
          src: row.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${row.name}`,
        }),
        h('span', {}, row.name),
      ])
    },
  },
  {
    title: 'Part',
    key: 'share',
    width: 80,
    render: (row) => h(NTag, { size: 'small', type: 'info' }, { default: () => `${row.share}%` }),
  },
  {
    title: 'Budget alloué',
    key: 'allocatedBudget',
    width: 120,
    render: (row) => `${row.allocatedBudget.toFixed(2)} €`,
  },
  {
    title: 'Dépensé',
    key: 'spent',
    width: 100,
    render: (row) => `${row.spent.toFixed(2)} €`,
  },
  {
    title: 'Restant',
    key: 'remaining',
    width: 100,
    render: (row) => h('span', {
      style: { color: row.remaining >= 0 ? '#18a058' : '#d03050', fontWeight: 'bold' },
    }, `${row.remaining.toFixed(2)} €`),
  },
  {
    title: 'Progression',
    key: 'percentage',
    width: 150,
    render: (row) => h(NProgress, {
      type: 'line',
      percentage: Math.min(row.percentage, 100),
      status: row.percentage > 100 ? 'error' : row.percentage > 80 ? 'warning' : 'success',
      indicatorPlacement: 'inside',
    }),
  },
])
</script>
