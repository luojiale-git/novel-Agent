<template>
  <div style="padding: 24px; height: 100%; overflow-y: auto; color: #ccc;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="color: #fff; margin: 0;">项目</h2>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        新建项目
      </n-button>
    </div>

    <n-grid :cols="3" :x-gap="16" :y-gap="16">
      <n-grid-item v-for="project in projectStore.projects" :key="project.id">
        <n-card
          :title="project.name"
          hoverable
          @click="router.push(`/projects/${project.id}`)"
          style="cursor: pointer; background: #1a1a2e; border: 1px solid #2a2a3e;"
        >
          <template #header-extra>
            <n-tag :type="statusType(project.status)" size="small">{{ project.status }}</n-tag>
          </template>
          <p style="color: #888; font-size: 13px; height: 40px; overflow: hidden;">
            {{ project.description || '暂无描述' }}
          </p>
          <template #footer>
            <div style="display: flex; justify-content: space-between; color: #555; font-size: 12px;">
              <span>{{ typeLabel(project.project_type) }}</span>
              <span>{{ project.updated_at?.slice(0, 10) }}</span>
            </div>
          </template>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 新建项目模态框 -->
    <n-modal v-model:show="showCreateModal" preset="card" title="新建项目" style="width: 500px;">
      <n-form>
        <n-form-item label="项目名称" required>
          <n-input v-model:value="form.name" placeholder="输入项目名称" />
        </n-form-item>
        <n-form-item label="项目类型">
          <n-select v-model:value="form.project_type" :options="projectTypes" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="form.description" type="textarea" rows="3" placeholder="项目描述" />
        </n-form-item>
        <div style="display: flex; justify-content: flex-end; gap: 8px;">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreate">创建</n-button>
        </div>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores'
import {
  NButton, NIcon, NCard, NGrid, NGridItem, NTag,
  NModal, NForm, NFormItem, NInput, NSelect, useMessage
} from 'naive-ui'
import { AddOutline } from '@vicons/ionicons5'
import type { ProjectType } from '@/types'

const router = useRouter()
const projectStore = useProjectStore()
const message = useMessage()

const showCreateModal = ref(false)
const form = ref({
  name: '',
  description: '',
  project_type: 'story' as ProjectType | string,
})

const projectTypes = [
  { label: '故事创作', value: 'story' },
  { label: '文章写作', value: 'article' },
  { label: '调研分析', value: 'research' },
  { label: '代码开发', value: 'code' },
  { label: '其他', value: 'other' },
]

function statusType(status: string): 'warning' | 'success' | 'info' | 'default' {
  switch (status) {
    case 'draft': return 'warning'
    case 'active': return 'success'
    case 'completed': return 'info'
    default: return 'default'
  }
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    story: '故事',
    article: '文章',
    research: '调研',
    code: '代码',
    other: '其他',
  }
  return map[type] || type
}

async function handleCreate() {
  if (!form.value.name.trim()) {
    message.warning('请输入项目名称')
    return
  }
  try {
    await projectStore.createProject({
      name: form.value.name,
      description: form.value.description,
      project_type: form.value.project_type as any,
    })
    showCreateModal.value = false
    form.value = { name: '', description: '', project_type: 'story' }
    message.success('项目创建成功')
  } catch (e: any) {
    message.error(e.message || '创建失败')
  }
}

onMounted(() => {
  projectStore.fetchProjects()
})
</script>
