import type { Project, ProjectCreate, Session, SessionCreate, Document, DocumentCreate, SSEEvent } from '@/types'

const BASE = '/api/v1'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// === Projects ===
export const projectsApi = {
  list: () => request<{ projects: Project[]; total: number }>('/projects'),
  get: (id: string) => request<Project>(`/projects/${id}`),
  create: (data: ProjectCreate) =>
    request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<ProjectCreate>) =>
    request<Project>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<{ ok: boolean }>(`/projects/${id}`, { method: 'DELETE' }),
}

// === Sessions ===
export const sessionsApi = {
  list: (projectId?: string) =>
    request<{ sessions: Session[]; total: number }>(
      `/sessions${projectId ? `?project_id=${projectId}` : ''}`
    ),
  get: (id: string) => request<Session>(`/sessions/${id}`),
  create: (data: SessionCreate) =>
    request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<{ ok: boolean }>(`/sessions/${id}`, { method: 'DELETE' }),
  saveMessages: (id: string, messages: any[]) =>
    request<{ ok: boolean }>(`/sessions/${id}/messages`, {
      method: 'PUT',
      body: JSON.stringify({ messages }),
    }),
}

// === Agent ===
export const agentApi = {
  chat: (message: string, sessionId?: string) =>
    request<{ response: string; session_id?: string }>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    }),
  chatStream: (message: string, sessionId?: string): EventSource => {
    const params = new URLSearchParams()
    // Use POST via EventSource alternative - we use fetch with streaming
    throw new Error('Use agentApi.chatStreamFetch instead')
  },
  chatStreamFetch: async function* (
    message: string,
    sessionId?: string
  ): AsyncGenerator<SSEEvent> {
    const response = await fetch(`${BASE}/agent/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    })
    if (!response.ok) throw new Error('Stream request failed')
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          try {
            const data = JSON.parse(line.slice(6)) as SSEEvent
            yield data
          } catch { /* skip malformed */ }
        }
      }
    }
  },
  reset: (sessionId?: string) =>
    request<{ ok: boolean }>('/agent/reset', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),
  tools: () => request<{ tools: any[] }>('/agent/tools'),
  status: () => request<{ memory_turns: number; tools_count: number; llm_backend: string }>('/agent/status'),
}

// === Content / Documents ===
export const documentsApi = {
  list: (projectId: string) =>
    request<{ documents: Document[]; total: number }>(`/content?project_id=${projectId}`),
  get: (docId: string, projectId: string) =>
    request<Document>(`/content/${docId}?project_id=${projectId}`),
  create: (data: DocumentCreate) =>
    request<Document>('/content', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (docId: string, projectId: string, data: Partial<DocumentCreate>) =>
    request<Document>(`/content/${docId}?project_id=${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (docId: string, projectId: string) =>
    request<{ ok: boolean }>(`/content/${docId}?project_id=${projectId}`, {
      method: 'DELETE',
    }),
}
