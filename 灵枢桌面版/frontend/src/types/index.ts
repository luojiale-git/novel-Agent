// 项目类型
export type ProjectType = 'story' | 'article' | 'research' | 'code' | 'other'
export type ProjectStatus = 'draft' | 'active' | 'completed' | 'archived'

export interface Project {
  id: string
  name: string
  description: string
  project_type: ProjectType
  status: ProjectStatus
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
  project_type?: ProjectType
}

// 会话类型
export interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp?: string
}

export interface Session {
  id: string
  name: string
  project_id?: string
  messages: Message[]
  created_at: string
  updated_at: string
}

export interface SessionCreate {
  name?: string
  project_id?: string
}

// 文档类型
export interface Document {
  id: string
  title: string
  content: string
  project_id: string
  doc_type: string
  word_count: number
  created_at: string
  updated_at: string
}

export interface DocumentCreate {
  title: string
  content?: string
  project_id: string
  doc_type?: string
}

// SSE 事件
export interface SSEEvent {
  type: 'reasoning' | 'tool_call' | 'observation' | 'response' | 'error'
  content: string
}
