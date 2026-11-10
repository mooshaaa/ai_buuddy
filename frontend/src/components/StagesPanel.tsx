import { useEffect, useState } from 'react'
import { api } from '../api'
import type { StagesResponse, User } from '../types'

export default function StagesPanel({ user, refreshKey }: { user: User; refreshKey: number }) {
  const [data, setData] = useState<StagesResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.stages(user.id).then(setData).catch(() => setError('Не удалось загрузить этапы'))
  }, [user.id, refreshKey])

  async function toggle(id: number) {
    try {
      setData(await api.toggleStage(user.id, id))
    } catch {
      setError('Не удалось обновить этап')
    }
  }

  if (error) return <aside className="stages"><p className="bubble bubble-error">{error}</p></aside>
  if (!data) return <aside className="stages"><p className="muted">Загружаю этапы…</p></aside>

  const periods = [...new Set(data.stages.map((s) => s.period))]
  const next = data.stages.find((s) => !s.done)
  const pct = data.total ? Math.round((data.done / data.total) * 100) : 0

  return (
    <aside className="stages" aria-label="Этапы адаптации">
      <div className="progress-head">
        <h2>Адаптация</h2>
        <span>{data.done} из {data.total}</span>
      </div>
      <div className="bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div style={{ width: `${pct}%` }} />
      </div>

      {next ? (
        <div className="next">
          <span className="next-label">Следующий шаг</span>
          <strong>{next.title}</strong>
          <span>{next.description}</span>
        </div>
      ) : (
        <div className="next"><strong>Все шаги выполнены</strong></div>
      )}

      {periods.map((p) => (
        <div key={p} className="period">
          <h3>{p}</h3>
          <ul>
            {data.stages
              .filter((s) => s.period === p)
              .map((s) => (
                <li key={s.id} className={s.done ? 'done' : ''}>
                  <label>
                    <input type="checkbox" checked={s.done} onChange={() => toggle(s.id)} />
                    <span>{s.title}</span>
                  </label>
                </li>
              ))}
          </ul>
        </div>
      ))}
    </aside>
  )
}
