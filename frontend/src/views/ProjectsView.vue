<template>
  <n-space vertical size="large">
    <n-flex justify="space-between" align="center" :wrap="true" :size="[16, 12]">
      <h1 class="page-title">{{ t('project.title') }}</h1>
      <n-button type="primary" @click="openAddModal">
        {{ t('project.addProject') }}
      </n-button>
    </n-flex>

    <!-- Filters -->
    <n-space>
      <n-button v-for="f in statusFilters" :key="f.value" :type="activeStatus === f.value ? 'primary' : 'default'" size="small" @click="activeStatus = f.value">
        {{ f.label }}
      </n-button>
      <n-divider vertical />
      <n-button v-for="f in modeFilters" :key="f.value" :type="activeMode === f.value ? 'info' : 'default'" size="small" @click="activeMode = f.value">
        {{ f.label }}
      </n-button>
    </n-space>

    <!-- Loading -->
    <n-flex v-if="projectStore.loading" justify="center" style="padding: 40px;">
      <n-spin size="large" />
    </n-flex>

    <!-- Project List -->
    <template v-else-if="filteredProjects.length > 0">
      <n-card v-for="project in filteredProjects" :key="project.id" size="small" hoverable class="project-card" @click="goToDetail(project.id)">
        <template #header>
          <n-flex justify="space-between" align="center" :wrap="true" :size="8">
            <n-flex align="center" :size="8">
              <strong>{{ project.name }}</strong>
              <n-tag :type="statusTagType(project.status)" size="small">
                {{ t('project.' + project.status) }}
              </n-tag>
              <n-tag :type="project.mode === 'pro' ? 'info' : 'default'" size="small">
                {{ t('project.' + project.mode) }}
              </n-tag>
            </n-flex>
            <n-flex :size="8" @click.stop>
              <n-button size="small" type="info" @click="openEditModal(project)">{{ t('common.edit') }}</n-button>
              <n-popconfirm @positive-click="handleDelete(project.id)">
                <template #trigger>
                  <n-button size="small" type="error">{{ t('common.delete') }}</n-button>
                </template>
                {{ t('project.deleteProjectConfirm') }}
              </n-popconfirm>
            </n-flex>
          </n-flex>
        </template>

        <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="8">
          <n-gi>
            <n-text depth="3">{{ t('project.totalBudget') }}:</n-text> <strong>{{ project.total_budget.toFixed(2) }} €</strong>
          </n-gi>
          <n-gi>
            <n-text depth="3">{{ t('project.spent') }}:</n-text> <strong>{{ project.total_spent.toFixed(2) }} €</strong>
          </n-gi>
          <n-gi>
            <n-text depth="3">{{ t('project.remaining') }}:</n-text>
            <strong :class="project.remaining < 0 ? 'amount-negative' : 'amount-positive'">{{ project.remaining.toFixed(2) }} €</strong>
          </n-gi>
          <n-gi v-if="project.target_date">
            <n-text depth="3">{{ t('project.targetDate') }}:</n-text> {{ project.target_date }}
          </n-gi>
        </n-grid>

        <!-- Progress bar -->
        <div class="progress-container">
          <n-flex justify="space-between" class="progress-label">
            <span>{{ t('project.progress') }}</span>
            <span>{{ project.total_budget > 0 ? ((project.total_spent / project.total_budget) * 100).toFixed(1) : 0 }}%</span>
          </n-flex>
          <n-progress
            :percentage="project.total_budget > 0 ? Math.min((project.total_spent / project.total_budget) * 100, 100) : 0"
            :color="project.status === 'completed' ? '#18a058' : project.remaining < 0 ? '#d03050' : '#2080f0'"
            :show-indicator="false"
          />
        </div>

        <n-text v-if="project.description" depth="3" class="project-description">{{ project.description }}</n-text>
      </n-card>
    </template>

    <!-- Empty state -->
    <n-empty v-else-if="!projectStore.loading" :description="t('project.noProjects')" class="empty-state">
      <template #extra>
        <n-button @click="openAddModal" type="primary">{{ t('project.addProject') }}</n-button>
      </template>
    </n-empty>

    <!-- Add/Edit Project Modal -->
    <n-modal v-model:show="showProjectModal" preset="card" :title="editingProject ? t('project.editProject') : t('project.addProject')" :style="{ width: isMobile ? '90%' : '500px' }">
      <n-form>
        <n-form-item :label="t('project.name')">
          <n-input v-model:value="projectForm.name" :placeholder="t('project.name')" />
        </n-form-item>
        <n-form-item :label="t('project.description')">
          <n-input v-model:value="projectForm.description" type="textarea" :placeholder="t('project.description')" />
        </n-form-item>
        <n-form-item :label="t('project.totalBudget')">
          <n-input-number v-model:value="projectForm.total_budget" :min="0" :precision="2" style="width: 100%">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('project.targetDate')">
          <n-date-picker v-model:value="projectForm.target_date" type="date" style="width: 100%" clearable />
        </n-form-item>
        <n-form-item :label="t('project.mode')">
          <n-radio-group v-model:value="projectForm.mode">
            <n-radio-button value="personal">{{ t('project.personal') }}</n-radio-button>
            <n-radio-button value="pro">{{ t('project.pro') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="editingProject" :label="t('project.status')">
          <n-radio-group v-model:value="projectForm.status">
            <n-radio-button value="active">{{ t('project.active') }}</n-radio-button>
            <n-radio-button value="completed">{{ t('project.completed') }}</n-radio-button>
            <n-radio-button value="abandoned">{{ t('project.abandoned') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showProjectModal = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">{{ t('common.save') }}</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSpace, NFlex, NButton, NCard, NGrid, NGi, NText, NTag,
  NSpin, NEmpty, NProgress, NModal, NForm, NFormItem,
  NInput, NInputNumber, NRadioGroup, NRadioButton, NDatePicker,
  NPopconfirm, NDivider, useMessage,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { Project } from '@/services/api'

const { t } = useI18n()
const message = useMessage()
const router = useRouter()
const projectStore = useProjectStore()
const proStore = useProStore()
const { isMobile } = useMobileDetect()

const activeStatus = ref('all')
const activeMode = ref('all')
const showProjectModal = ref(false)
const saving = ref(false)
const editingProject = ref<Project | null>(null)

const projectForm = ref({
  name: '',
  description: '',
  total_budget: 0 as number,
  target_date: null as number | null,
  mode: 'personal' as 'personal' | 'pro',
  status: 'active' as string,
})

const statusFilters = computed(() => [
  { label: t('project.allStatuses'), value: 'all' },
  { label: t('project.active'), value: 'active' },
  { label: t('project.completed'), value: 'completed' },
  { label: t('project.abandoned'), value: 'abandoned' },
])

const modeFilters = computed(() => [
  { label: t('project.allModes'), value: 'all' },
  { label: t('project.personal'), value: 'personal' },
  { label: t('project.pro'), value: 'pro' },
])

const filteredProjects = computed(() => {
  let list = projectStore.projects
  if (activeStatus.value !== 'all') list = list.filter(p => p.status === activeStatus.value)
  if (activeMode.value !== 'all') list = list.filter(p => p.mode === activeMode.value)
  return list
})

const statusTagType = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'abandoned') return 'error'
  return 'default'
}

onMounted(async () => {
  await projectStore.fetchProjects()
})

const formatDate = (ts: number) => {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const goToDetail = (id: string) => {
  router.push({ name: 'project-detail', params: { id } })
}

const openAddModal = () => {
  editingProject.value = null
  projectForm.value = {
    name: '', description: '', total_budget: 0,
    target_date: null, mode: proStore.isProMode ? 'pro' : 'personal', status: 'active',
  }
  showProjectModal.value = true
}

const openEditModal = (project: Project) => {
  editingProject.value = project
  projectForm.value = {
    name: project.name,
    description: project.description || '',
    total_budget: project.total_budget,
    target_date: project.target_date ? new Date(project.target_date).getTime() : null,
    mode: project.mode,
    status: project.status,
  }
  showProjectModal.value = true
}

const handleSave = async () => {
  if (!projectForm.value.name || projectForm.value.total_budget < 0) return
  saving.value = true
  try {
    const targetDate = projectForm.value.target_date ? formatDate(projectForm.value.target_date) : undefined
    if (editingProject.value) {
      await projectStore.updateProject(editingProject.value.id, {
        name: projectForm.value.name,
        description: projectForm.value.description || undefined,
        total_budget: projectForm.value.total_budget,
        target_date: targetDate,
        status: projectForm.value.status,
      })
      message.success(t('project.projectUpdated'))
    } else {
      await projectStore.createProject({
        name: projectForm.value.name,
        description: projectForm.value.description || undefined,
        total_budget: projectForm.value.total_budget,
        target_date: targetDate,
        mode: projectForm.value.mode,
      })
      message.success(t('project.projectAdded'))
    }
    showProjectModal.value = false
    await projectStore.fetchProjects()
  } catch {
    message.error(t('errors.generic'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await projectStore.deleteProject(id)
    message.success(t('project.projectDeleted'))
  } catch {
    message.error(t('errors.generic'))
  }
}
</script>

<style scoped>
.page-title {
  margin: 0;
  font-size: clamp(20px, 5vw, 28px);
}
.project-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.project-card:hover {
  transform: translateY(-1px);
}
.progress-container {
  margin-top: 12px;
}
.progress-label {
  font-size: 12px;
  margin-bottom: 4px;
}
.project-description {
  display: block;
  margin-top: 8px;
}
.empty-state {
  margin-top: 40px;
}
.amount-positive {
  color: var(--color-success, #18a058);
}
.amount-negative {
  color: var(--color-error, #d03050);
}
</style>
