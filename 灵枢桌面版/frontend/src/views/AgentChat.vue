<template>
  <div style="display: flex; height: 100%; color: #ccc;">
    <!-- 左侧会话列表 -->
    <div style="width: 260px; border-right: 1px solid #2a2a3e; background: #12121e; display: flex; flex-direction: column;">
      <div style="padding: 16px; border-bottom: 1px solid #2a2a3e;">
        <n-button block @click="handleNewChat">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          新建对话
        </n-button>
      </div>
      <div style="flex: 1; overflow-y: auto;">
        <n-list v-if="sessionStore.sessions.length > 0">
          <n-list-item
            v-for="session in sessionStore.sessions"
            :key="session.id"
            :class="{ active: sessionStore.currentSession?.id === session.id }"
            style="cursor: pointer; border-bottom: 1px solid #1e1e2e; padding: 10px 16px;"
            :style="sessionStore.currentSession?.id === session.id ? 'background: #1a1a3e;' : ''"
            @click="handleSelectSession(session.id)"
          >
            <div style="font-size: 13px; color: #ddd; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ session.name || '未命名会话' }}
            </div>
            <div style="font-size: 11px; color: #555; margin-top: 2px;">
              {{ session.messages?.length || 0 }} 条消息
            </div>
          </n-list-item>
        </n-list>
        <div v-else style="text-align: center; padding: 40px 16px; color: #555; font-size: 13px;">
          暂无会话，点击"新建对话"开始
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div style="flex: 1; display: flex; flex-direction: column; position: relative;">
      <!-- 消息列表 -->
      <div ref="messageListRef" style="flex: 1; overflow-y: auto; padding: 20px; padding-bottom: 80px;">
        <div v-if="sessionStore.messages.length === 0" style="text-align: center; padding: 60px 20px; color: #555;">
          <div style="font-size: 40px; margin-bottom: 12px; opacity: 0.3;">💬</div>
          <p style="font-size: 16px; margin-bottom: 8px;">开始与 AI Agent 对话</p>
          <p style="font-size: 13px;">灵枢可以帮你写作、调研、编程和创意构思</p>
        </div>

        <div v-for="(msg, idx) in sessionStore.messages" :key="idx" style="margin-bottom: 16px;">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" style="display: flex; justify-content: flex-end; margin-bottom: 8px;">
            <div style="max-width: 70%; background: #1e3a5f; border-radius: 12px 12px 4px 12px; padding: 10px 14px; color: #e0e0e0; font-size: 14px; line-height: 1.5; white-space: pre-wrap;">
              {{ msg.content }}
            </div>
          </div>
          <!-- 助手消息 -->
          <div v-else-if="msg.role === 'assistant'" style="display: flex; margin-bottom: 8px;">
            <div style="max-width: 85%; background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 12px 12px 12px 4px; padding: 10px 14px; color: #d0d0d0; font-size: 14px; line-height: 1.6;">
              <div class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
          <!-- 系统/工具消息 -->
          <div v-else style="text-align: center; margin-bottom: 8px;">
            <n-tag size="small" :type="msg.role === 'tool' ? 'info' : 'warning'" style="font-size: 11px;">
              {{ msg.role === 'tool' ? '工具调用' : '系统' }}: {{ msg.content.slice(0, 80) }}{{ msg.content.length > 80 ? '...' : '' }}
            </n-tag>
          </div>
        </div>

        <!-- 流式响应占位 -->
        <div v-if="streamingContent" style="display: flex; margin-bottom: 8px;">
          <div style="max-width: 85%; background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 12px 12px 12px 4px; padding: 10px 14px; color: #d0d0d0; font-size: 14px; line-height: 1.6;">
            <div class="markdown-content" v-html="renderMarkdown(streamingContent)"></div>
            <n-spin v-if="streaming" size="small" style="margin-left: 4px;" />
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 16px 20px; background: #0f0f1a; border-top: 1px solid #2a2a3e;">
        <div style="display: flex; gap: 8px; align-items: flex-end;">
          <n-input
            v-model:value="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
            :disabled="streaming"
            @keydown="handleKeydown"
            style="flex: 1;"
          />
          <n-button
            type="primary"
            :loading="streaming"
            :disabled="!inputMessage.trim() && !streaming"
            @click="handleSend"
          >
            <template #icon><n-icon><SendOutline /></n-icon></template>
            发送
          </n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores'
import { agentApi } from '@/api'
import type { Message } from '@/types'
import {
  NButton, NIcon, NInput, NList, NListItem, NSpin, NTag, useMessage
} from 'naive-ui'
import { AddOutline, SendOutline } from '@vicons/ionicons5'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()
const sessionStore = useSessionStore()
const message = useMessage()

const inputMessage = ref('')
const streaming = ref(false)
const streamingContent = ref('')
const messageListRef = ref<HTMLElement | null>(null)

function renderMarkdown(text: string): string {
  if (!text) return ''
  const raw = marked.parse(text, { async: false }) as string
  return DOMPurify.sanitize(raw)
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

watch(() => sessionStore.messages.length, scrollToBottom)
watch(streamingContent, scrollToBottom)

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

async function handleNewChat() {
  try {
    await sessionStore.createSession({})
    message.success('已创建新会话')
  } catch (e: any) {
    message.error(e.message || '创建失败')
  }
}

async function handleSelectSession(id: string) {
  try {
    await sessionStore.selectSession(id)
  } catch (e: any) {
    message.error(e.message || '加载会话失败')
  }
}

async function handleSend() {
  const text = inputMessage.value.trim()
  if (!text || streaming.value) return

  inputMessage.value = ''

  // 如果当前没有会话，先创建一个
  if (!sessionStore.currentSession) {
    try {
      await sessionStore.createSession({})
    } catch (e: any) {
      message.error('创建会话失败')
      return
    }
  }

  // 添加用户消息
  const userMsg: Message = { role: 'user', content: text }
  sessionStore.addMessage(userMsg)

  // 发起流式请求
  streaming.value = true
  streamingContent.value = ''

  const sessionId = sessionStore.currentSession?.id

  try {
    const gen = agentApi.chatStreamFetch(text, sessionId)
    let fullContent = ''

    for await (const event of gen) {
      if (event.type === 'response') {
        fullContent += event.content
        streamingContent.value = fullContent
      } else if (event.type === 'reasoning') {
        // 推理过程可选择展示
      } else if (event.type === 'tool_call') {
        // 工具调用信息
      } else if (event.type === 'error') {
        message.error(event.content)
      }
    }

    // 添加助手消息
    if (fullContent) {
      const assistantMsg: Message = { role: 'assistant', content: fullContent }
      sessionStore.addMessage(assistantMsg)
    }

    // 保存消息
    if (sessionStore.currentSession) {
      await agentApi.chat(text, sessionId).catch(() => {})
    }
  } catch (e: any) {
    message.error(e.message || '请求失败')
    // 回退到普通请求
    try {
      const res = await agentApi.chat(text, sessionId)
      if (res.response) {
        const fallbackMsg: Message = { role: 'assistant', content: res.response }
        sessionStore.addMessage(fallbackMsg)
      }
    } catch (e2: any) {
      message.error(e2.message || '通信失败')
    }
  } finally {
    streaming.value = false
    streamingContent.value = ''
  }
}

onMounted(() => {
  sessionStore.fetchSessions()
})
</script>

<style scoped>
.active {
  background: #1a1a3e;
}
.markdown-content :deep(pre) {
  background: #0d0d1a;
  border: 1px solid #2a2a3e;
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}
.markdown-content :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
}
.markdown-content :deep(p) {
  margin: 4px 0;
}
.markdown-content :deep(h1), .markdown-content :deep(h2), .markdown-content :deep(h3) {
  color: #fff;
  margin: 12px 0 6px;
}
.markdown-content :deep(ul), .markdown-content :deep(ol) {
  padding-left: 20px;
}
.markdown-content :deep(blockquote) {
  border-left: 3px solid #3a6a9f;
  padding-left: 12px;
  color: #888;
  margin: 8px 0;
}
</style>
