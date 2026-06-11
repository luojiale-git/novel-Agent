<template>
  <div style="padding: 24px; height: 100%; overflow-y: auto; color: #ccc;">
    <h2 style="color: #fff; margin: 0 0 24px 0;">设置</h2>

    <n-card title="Agent 状态" style="background: #1a1a2e; border: 1px solid #2a2a3e; margin-bottom: 16px;">
      <n-description label-placement="left" :column="1">
        <n-description-item label="LLM 后端">
          <n-tag>{{ agentStatus.llm_backend || '未知' }}</n-tag>
        </n-description-item>
        <n-description-item label="记忆轮数">
          {{ agentStatus.memory_turns ?? '-' }}
        </n-description-item>
        <n-description-item label="工具数量">
          {{ agentStatus.tools_count ?? '-' }}
        </n-description-item>
      </n-description>
      <template #footer>
        <n-button size="small" @click="refreshStatus">刷新状态</n-button>
      </template>
    </n-card>

    <n-card title="可用工具" style="background: #1a1a2e; border: 1px solid #2a2a3e; margin-bottom: 16px;">
      <n-list v-if="tools.length > 0">
        <n-list-item v-for="tool in tools" :key="tool.name" style="border-bottom: 1px solid #2a2a3e;">
          <n-thing :title="tool.name" :description="tool.description || '无描述'">
            <div style="font-size: 12px; color: #666;">
              {{ tool.parameters ? Object.keys(tool.parameters).join(', ') : '无参数' }}
            </div>
          </n-thing>
        </n-list-item>
      </n-list>
      <div v-else style="text-align: center; padding: 20px; color: #555;">
        暂无可用工具
      </div>
    </n-card>

    <n-card title="关于" style="background: #1a1a2e; border: 1px solid #2a2a3e;">
      <p>灵枢 (LingShu) — AI Agent 驱动的创意工作台</p>
      <p style="color: #666; font-size: 13px;">版本 1.0.0 · 基于 Vue 3 + Naive UI + Tauri</p>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { agentApi } from '@/api'
import {
  NCard, NButton, NTag, NList, NListItem, NThing, useMessage
} from 'naive-ui'

const message = useMessage()

const agentStatus = ref<{ memory_turns: number; tools_count: number; llm_backend: string }>({
  memory_turns: 0,
  tools_count: 0,
  llm_backend: '',
})
const tools = ref<any[]>([])

async function refreshStatus() {
  try {
    const [statusRes, toolsRes] = await Promise.all([
      agentApi.status(),
      agentApi.tools(),
    ])
    agentStatus.value = statusRes
    tools.value = toolsRes.tools || []
  } catch (e: any) {
    message.error(e.message || '获取状态失败')
  }
}

onMounted(refreshStatus)
</script>
