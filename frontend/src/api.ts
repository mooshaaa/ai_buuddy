import type { ActionCardBlock, Block, StagesResponse, User } from './types'

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
  chat: (user_id: string, message: string) =>
    request<{ blocks: Block[] }>('/api/chat', post({ user_id, message })).then((r) => r.blocks),
  stages: (user_id: string) => request<StagesResponse>(`/api/stages?user_id=${encodeURIComponent(user_id)}`),
  toggleStage: (user_id: string, stageId: number) =>
    request<StagesResponse>(`/api/stages/${stageId}/toggle`, post({ user_id })),
  confirm: (user_id: string, actionId: number) =>
    request<ActionCardBlock>(`/api/actions/${actionId}/confirm`, post({ user_id })),
  cancel: (user_id: string, actionId: number) =>
    request<ActionCardBlock>(`/api/actions/${actionId}/cancel`, post({ user_id })),
}
