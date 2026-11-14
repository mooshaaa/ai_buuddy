import type { ActionCardBlock, Block, DebugEvent, DebugInfo, Health, HistoryMessage, StagesResponse, User } from './types'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = `Ошибка ${res.status}`
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* тело ответа не JSON */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

const post = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) })

export const api = {
  users: () => request<User[]>('/api/users'),
  health: () => request<Health>('/health'),
  history: (user_id: string) =>
    request<{ messages: HistoryMessage[] }>(`/api/history?user_id=${encodeURIComponent(user_id)}`).then((r) => r.messages),
  resetHistory: (user_id: string) => request<{ status: string }>('/api/history/reset', post({ user_id })),
  debugEvents: () => request<DebugEvent[]>('/api/debug/events'),
  chat: (user_id: string, message: string) =>
    request<{ blocks: Block[]; debug: DebugInfo | null }>('/api/chat', post({ user_id, message })),
  stages: (user_id: string) => request<StagesResponse>(`/api/stages?user_id=${encodeURIComponent(user_id)}`),
  toggleStage: (user_id: string, stageId: number) =>
    request<StagesResponse>(`/api/stages/${stageId}/toggle`, post({ user_id })),
  confirm: (user_id: string, actionId: number) =>
    request<ActionCardBlock>(`/api/actions/${actionId}/confirm`, post({ user_id })),
  cancel: (user_id: string, actionId: number) =>
    request<ActionCardBlock>(`/api/actions/${actionId}/cancel`, post({ user_id })),
}
