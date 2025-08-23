<template>
  <n-card v-if="tagDistribution.length > 0" title="Statistics by Tag">
    <!-- Stacked bar chart at 100% -->
    <div style="display: flex; height: 32px; border-radius: 6px; overflow: hidden; margin-bottom: 16px;">
      <div
        v-for="stat in tagDistribution"
        :key="stat.tag"
        :style="{
          width: stat.distributionPercent + '%',
          backgroundColor: getTagColor(stat.tag),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minWidth: stat.distributionPercent > 5 ? 'auto' : '0',
        }"
      >
        <span v-if="stat.distributionPercent > 8" style="color: white; font-size: 12px; font-weight: bold;">
          {{ stat.distributionPercent.toFixed(1) }}%
        </span>
      </div>
    </div>

    <!-- Legend -->
    <div style="display: flex; flex-wrap: wrap; gap: 16px;">
      <div v-for="stat in tagDistribution" :key="stat.tag" style="display: flex; align-items: center; gap: 8px;">
        <div :style="{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: getTagColor(stat.tag) }"></div>
        <span style="font-size: 13px;">
          <strong>{{ stat.tag }}</strong>: {{ stat.budget.toFixed(2) }} € ({{ stat.distributionPercent.toFixed(1) }}%)
        </span>
      </div>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { NCard } from 'naive-ui'

interface TagStat {
  tag: string
  budget: number
  spent: number
  remaining: number
  percentage: number
  distributionPercent: number
}

interface Props {
  tagDistribution: TagStat[]
}

defineProps<Props>()

const TAG_COLORS: Record<string, string> = {
  'crédit': '#d03050',
  'besoin': '#f0a020',
  'loisir': '#2080f0',
  'épargne': '#18a058',
}

const getTagColor = (tag: string): string => {
  return TAG_COLORS[tag] || '#888888'
}
</script>
