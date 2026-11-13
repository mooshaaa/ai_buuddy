import { useEffect, useState } from 'react'
import { api } from '../api'
import type { DebugEvent } from '../types'

export default function DebugLog() {
  const [events, setEvents] = useState<DebugEvent[]>([])
  const [error, setError] = useState('')

  const load = () =>
    api
      .debugEvents()
      .then((e) => {
        setEvents(e)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить лог'))

  useEffect(() => {
    load()
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="debug-log">
      {error && <p className="bubble bubble-error">{error}</p>}
      {events.length === 0 && !error && <p className="muted">Пока нет событий. Напишите что-нибудь в чат.</p>}
      {events.length > 0 && (
        <table>
          <thead>
            <tr><th>Время</th><th>Запрос</th><th>Намерение</th><th>Источник</th><th>мс</th><th>Заметка</th></tr>
          </thead>
          <tbody>
            {events.map((e, i) => (
              <tr key={i}>
                <td>{e.ts.slice(11)}</td>
                <td>{e.message}</td>
                <td>{e.intent}</td>
                <td>{e.source === 'llm' ? e.model : e.source}</td>
                <td>{e.latency_ms}</td>
                <td>{e.note || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
