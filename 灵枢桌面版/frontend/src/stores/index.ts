import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, Session, Message } from '@/types'
import { projectsApi, sessionsApi } from '@/api'

// 项目 Store
export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const res = await projectsApi.list()
      projects.value = res.projects
    } finally {
      loading.value = false
    }
  }

  async function createProject(data: { name: string; description?: string; project_type?: string }) {
    const project = await projectsApi.create(data)
    projects.value.unshift(project)
    return project
  }

  async function deleteProject(id: string) {
    await projectsApi.delete(id)
    projects.value = projects.value.filter(p => p.id !== id)
    if (currentProject.value?.id === id) {
      currentProject.value = null
    }
  }

  async function selectProject(id: string) {
    const project = await projectsApi.get(id)
    currentProject.value = project
    return project
  }

  return { projects, currentProject, loading, fetchProjects, createProject, deleteProject, selectProject }
})

// 会话 Store
export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const currentSession = ref<Session | null>(null)
  const messages = ref<Message[]>([])

  async function fetchSessions(projectId?: string) {
    const res = await sessionsApi.list(projectId)
    sessions.value = res.sessions
  }

  async function createSession(data: { name?: string; project_id?: string }) {
    const session = await sessionsApi.create(data)
    sessions.value.unshift(session)
    currentSession.value = session
    messages.value = []
    return session
  }

  async function selectSession(id: string) {
    const session = await sessionsApi.get(id)
    currentSession.value = session
    messages.value = session.messages || []
    return session
  }

  function addMessage(msg: Message) {
    messages.value.push(msg)
  }

  async function deleteSession(id: string) {
    await sessionsApi.delete(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSession.value?.id === id) {
      currentSession.value = null
      messages.value = []
    }
  }

  return {
    sessions, currentSession, messages,
    fetchSessions, createSession, selectSession, addMessage, deleteSession,
  }
})
