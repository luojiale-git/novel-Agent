<template>
  <div style="padding: 24px; height: 100%; overflow-y: auto; color: #ccc;">
    <div v-if="loading" style="text-align: center; padding: 60px 0;">
      <n-spin size="large" />
    </div>
    <template v-else-if="project">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
          <n-button text @click="router.push('/projects')" style="color: #888; margin-bottom: 4px;">
            <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
            返回项目列表
          </n-button>
          <h2 style="color: #fff; margin: 4px 0 0 0;">{{ project.name }}</h2>
        </div>
        <div style="display: flex; gap: 8px;">
          <n-tag :type="statusTagType(project.status)" size="small">{{ project.status }}</n-tag>
          <n-tag size="small">{{ typeLabel(project.project_type) }}</n-tag>
        </div>
      </div>

      <p style="color: #888; margin-bottom: 24px;">{{ project.description || '暂无描述' }}</p>

      <n-tabs type="line" default-value="sessions" theme-overrides="{ tabTextColorActive: '#fff' }">
        <n-tab-pane name="sessions" tab="对话会话">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: #888; font-size: 13px;">共 {{ sessions.length }} 个会话</span>
            <n-button size="small" @click="handleNewSession">
              <template #icon><n-icon><AddOutline /></n-icon></template>
              新建会话
            </n-button>
          </div>
          <div v-if="sessions.length === 0" style="text-align: center; padding: 40px; color: #555;">
            暂无会话，点击"新建会话"开始
          </div>
          <n-list v-else>
            <n-list-item v-for="session in sessions" :key="session.id"
              style="cursor: pointer; border-bottom: 1px solid #2a2a3e;"
              @click="router.push('/agent')"
            >
              <n-thing :title="session.name || '未命名会话'" :description="session.created_at?.slice(0, 16) || ''">
                <span style="color: #666; font-size: 12px;">{{ session.messages?.length || 0 }} 条消息</span>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-tab-pane>

        <n-tab-pane name="documents" tab="文档">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: #888; font-size: 13px;">共 {{ documents.length }} 个文档</span>
            <n-button size="small" @click="showNewDocModal = true">
              <template #icon><n-icon><DocumentOutline /></n-icon></template>
              新建文档
            </n-button>
          </div>
          <div v-if="documents.length === 0" style="text-align: center; padding: 40px; color: #555;">
            暂无文档
          </div>
          <n-list v-else>
            <n-list-item v-for="doc in documents" :key="doc.id"
              style="border-bottom: 1px solid #2a2a3e;">
              <n-thing :title="doc.title" :description="doc.updated_at?.slice(0, 10) || ''">
                <span style="color: #666; font-size: 12px;">{{ doc.word_count }} 字 · {{ doc.doc_type }}</span>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-tab-pane>
      </n-tabs>

      <!-- 新建文档模态框 -->
      <n-modal v-model:show="showNewDocModal" preset="card" title="新建文档" style="width: 500px;">
        <n-form>
          <n-form-item label="文档标题" required>
            <n-input v-model:value="docForm.title" placeholder="输入文档标题" />
          </n-form-item>
          <n-form-item label="文档类型">
            <n-select v-model:value="docForm.doc_type" :options="docTypes" />
          </n-form-item>
          <div style="display: flex; justify-content: flex-end; gap: 8px;">
            <n-button @click="showNewDocModal = false">取消</n-button>
            <n-button type="primary" @click="handleCreateDoc">创建</n-button>
          </div>
        </n-form>
      </n-modal>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores'
import { documentsApi, sessionsApi } from '@/api'
import type { Document, Session } from '@/types'
import {
  NButton, NIcon, NSpin, NTag, NTabs, NTabPane,
  NList, NListItem, NThing, NModal, NForm, NFormItem,
  NInput, NSelect, useMessage
} from 'naive-ui'
import { ArrowBackOutline, AddOutline, DocumentOutline } from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const message = useMessage()

const loading = ref(true)
const project = ref(projectStore.currentProject)
const sessions = ref<Session[]>([])
const documents = ref<Document[]>([])

const showNewDocModal = ref(false)
const docForm = ref({ title: '', doc_type: 'article' })

const docTypes = [
  { label: '文章', value: 'article' },
  { label: '大纲', value: 'outline' },
  { label: '笔记', value: 'note' },
  { label: '其他', value: 'other' },
]

function statusTagType(status: string) {
  switch (status) {
    case 'draft': return 'warning' as const
    case 'active': return 'success' as const
    case 'completed': return 'info' as const
    default: return 'default' as const
  }
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    story: '故事', article: '文章', research: '调研', code: '代码', other: '其他',
  }
  return map[type] || type
}

async function handleNewSession() {
  try {
    const session = await sessionsApi.create({ project_id: route.params.id as string })
    router.push('/agent')
  } catch (e: any) {
    message.error(e.message || '创建会话失败')
  }
}

async function handleCreateDoc() {
  if (!docForm.value.title.trim()) {
    message.warning('请输入文档标题')
    return
  }
  try {
    await documentsApi.create({
      title: docForm.value.title,
      doc_type: docForm.value.doc_type,
      project_id: route.params.id as string,
    })
    showNewDocModal.value = false
    docForm.value = { title: '', doc_type: 'article' }
    message.success('文档创建成功')
    loadDocuments()
  } catch (e: any) {
    message.error(e.message || '创建文档失败')
  }
}

async function loadDocuments() {
  try {
    const res = await documentsApi.list(route.params.id as string)
    documents.value = res.documents
  } catch { /* ignore */ }
}

onMounted(async () => {
  const id = route.params.id as string
  try {
    project.value = await projectStore.selectProject(id)
    const [sessRes] = await Promise.all([
      sessionsApi.list(id),
      loadDocuments(),
    ])
    sessions.value = sessRes.sessions
  } catch (e: any) {
    message.error('加载项目失败')
    router.push('/projects')
  } finally {
    loading.value = false
  }
})
</script>
