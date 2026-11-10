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
export type Block = TextBlock | ErrorBlock | ActionCardBlock

export interface Message {
  id: number
  from: 'user' | 'bot'
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
