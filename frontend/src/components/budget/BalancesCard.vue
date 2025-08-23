<template>
  <n-card v-if="balances.length > 0" title="Balances">
    <n-space vertical size="large">
      <!-- Balance summary per member -->
      <n-list bordered>
        <n-list-item v-for="balance in balances" :key="balance.user_id">
          <n-thing :title="balance.user_name">
            <template #description>
              <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="8" style="margin-top: 8px;">
                <n-gi>
                  <div style="font-size: 12px; color: #888;">Share</div>
                  <div style="font-weight: bold;">{{ balance.share }}%</div>
                </n-gi>
                <n-gi>
                  <div style="font-size: 12px; color: #888;">Should pay</div>
                  <div style="font-weight: bold;">{{ balance.total_due.toFixed(2) }} €</div>
                </n-gi>
                <n-gi>
                  <div style="font-size: 12px; color: #888;">Has paid</div>
                  <div style="font-weight: bold;">{{ balance.total_paid.toFixed(2) }} €</div>
                </n-gi>
                <n-gi>
                  <div style="font-size: 12px; color: #888;">Balance</div>
                  <div :style="{ fontWeight: 'bold', color: balance.balance >= 0 ? '#18a058' : '#d03050' }">
                    {{ balance.balance >= 0 ? '+' : '' }}{{ balance.balance.toFixed(2) }} €
                  </div>
                </n-gi>
              </n-grid>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>

      <!-- Settlement summary -->
      <n-card size="small" :bordered="false" style="background: rgba(255,255,255,0.05);">
        <div style="font-size: 14px; font-weight: bold; margin-bottom: 12px;">Remboursements</div>
        <div v-if="settlements.length === 0">
          <n-tag type="success">Tout est équilibré !</n-tag>
        </div>
        <n-space v-else vertical size="medium">
          <div
            v-for="(settlement, idx) in settlements"
            :key="idx"
            style="display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: rgba(0,0,0,0.1); border-radius: 8px;"
          >
            <span style="color: #d03050; font-weight: bold;">{{ settlement.from }}</span>
            <span style="font-size: 20px;">→</span>
            <span style="color: #18a058; font-weight: bold;">{{ settlement.to }}</span>
            <n-tag type="warning" size="medium" style="margin-left: auto;">
              {{ settlement.amount.toFixed(2) }} €
            </n-tag>
          </div>
        </n-space>
      </n-card>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NSpace, NList, NListItem, NThing, NGrid, NGi, NTag } from 'naive-ui'
import type { MemberBalance } from '@/services/api'

interface Props {
  balances: MemberBalance[]
  isMobile: boolean
}

const props = defineProps<Props>()

const settlements = computed(() => {
  const result: { from: string; to: string; amount: number }[] = []

  const debtors = props.balances
    .filter(b => b.balance < -0.01)
    .map(b => ({ name: b.user_name, remaining: Math.abs(b.balance) }))
    .sort((a, b) => b.remaining - a.remaining)

  const creditors = props.balances
    .filter(b => b.balance > 0.01)
    .map(b => ({ name: b.user_name, remaining: b.balance }))
    .sort((a, b) => b.remaining - a.remaining)

  for (const debtor of debtors) {
    while (debtor.remaining > 0.01) {
      const creditor = creditors.find(c => c.remaining > 0.01)
      if (!creditor) break

      const amount = Math.min(debtor.remaining, creditor.remaining)
      result.push({
        from: debtor.name,
        to: creditor.name,
        amount: Math.round(amount * 100) / 100,
      })

      debtor.remaining -= amount
      creditor.remaining -= amount
    }
  }

  return result
})
</script>
