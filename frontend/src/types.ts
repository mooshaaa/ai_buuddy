export type Role = 'intern' | 'mentor'

export interface User {
  id: string
  name: string
  role: Role
}

export interface TextBlock { type: 'text'; text: string }
export interface ErrorBlock { type: 'error'; text: string }
export interface ActionCardBlock {
  type: 'action_card'
  action_id: number
  action: string
  title: string
  params: Record<string, unknown>
  status: 'needs_confirmation' | 'done' | 'rejected'
  result: Record<string, unknown> | null
}
export interface SourceItem {
  id: string
  title: string
  source: string
  synthetic: boolean
}
export interface SourceBlock { type: 'source'; items: SourceItem[] }
export type Block = TextBlock | ErrorBlock | ActionCardBlock | SourceBlock

export interface DebugInfo {
  intent: string
  source: 'llm' | 'stub' | 'error'
  model: string
  note: string
  latency_ms: number
  kb_found?: boolean
  kb_sources?: string[]
  answer_source?: string
  answer_model?: string
  history_len?: number
}

export interface DebugEvent extends DebugInfo {
  ts: string
  user: string
  message: string
}

export interface Health {
  status: string
  llm: string
  debug: boolean
}

export interface Message {
  id: number
  from: 'user' | 'bot'
  blocks: Block[]
  debug?: DebugInfo | null
}

export interface HistoryMessage {
  id: number
  role: 'user' | 'bot'
  blocks: Block[]
}

export interface Stage {
  id: number
  period: string
  title: string
  description: string
  done: boolean
}

export interface StagesResponse {
  stages: Stage[]
  done: number
  total: number
}
