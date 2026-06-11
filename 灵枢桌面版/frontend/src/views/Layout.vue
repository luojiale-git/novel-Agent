<template>
  <n-layout position="absolute" has-sider>
    <!-- 左侧导航栏 -->
    <n-layout-sider
      bordered
      width="60"
      :native-scrollbar="false"
      style="background: #1a1a2e; display: flex; flex-direction: column; align-items: center; padding-top: 12px;"
    >
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle style="margin-bottom: 8px; color: #fff;" @click="router.push('/projects')">
            <template #icon><n-icon size="22"><FolderOutline /></n-icon></template>
          </n-button>
        </template>
        项目
      </n-tooltip>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle style="margin-bottom: 8px; color: #fff;" @click="router.push('/agent')">
            <template #icon><n-icon size="22"><ChatbubblesOutline /></n-icon></template>
          </n-button>
        </template>
        Agent 对话
      </n-tooltip>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle style="margin-bottom: 8px; color: #fff;" @click="router.push('/settings')">
            <template #icon><n-icon size="22"><SettingsOutline /></n-icon></template>
          </n-button>
        </template>
        设置
      </n-tooltip>
      <div style="flex:1"></div>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle style="margin-bottom: 12px; color: #666;" @click="router.push('/')">
            <template #icon><n-icon size="20"><LogoGithub /></n-icon></template>
          </n-button>
        </template>
        灵枢 v1.0
      </n-tooltip>
    </n-layout-sider>

    <!-- 内容区 -->
    <n-layout style="background: #0f0f1a;">
      <router-view />
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NLayout, NLayoutSider, NButton, NTooltip, NIcon } from 'naive-ui'
import { FolderOutline, ChatbubblesOutline, SettingsOutline, LogoGithub } from '@vicons/ionicons5'

const router = useRouter()
</script>
