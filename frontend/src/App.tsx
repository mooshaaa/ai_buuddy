import { useEffect, useState } from 'react'
import { api } from './api'
import Chat from './components/Chat'
import DebugLog from './components/DebugLog'
import StagesPanel from './components/StagesPanel'
import type { Health, User } from './types'

export default function App() {
  const [users, setUsers] = useState<User[]>([])
  const [userId, setUserId] = useState<string>('')
  const [refresh, setRefresh] = useState(0)
  const [error, setError] = useState('')
  const [health, setHealth] = useState<Health | null>(null)
  const [showLog, setShowLog] = useState(false)

  useEffect(() => {
    api
      .users()
      .then((list) => {
        setUsers(list)
        if (list.length) setUserId(list[0].id)
      })
      .catch(() => setError('Не удалось связаться с сервером. Проверь, что backend запущен.'))
  }, [])

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
  }, [])

  const user = users.find((u) => u.id === userId)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span>AI-buddy</span>
        </div>
        <div className="topbar-right">
          {health && (
            <span className={`pill ${health.llm === 'stub' ? 'pill-stub' : 'pill-llm'}`} title="Режим бота">
              {health.llm === 'stub' ? 'Бот: заглушка' : `Бот: ${health.llm.replace('openai_compat:', '')}`}
            </span>
          )}
        <label className="user-switch">
          <span>Войти как</span>
          <select value={userId} onChange={(e) => setUserId(e.target.value)} disabled={!users.length}>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </label>
        </div>
      </header>

      {error && <div className="banner">{error}</div>}

      {user && (
        <main className="layout">
          <Chat key={user.id} user={user} onChange={() => setRefresh((n) => n + 1)} />
          <StagesPanel user={user} refreshKey={refresh} />
        </main>
      )}
      {health?.debug && (
        <div className="debug-wrap">
          <button className="btn" onClick={() => setShowLog((v) => !v)}>
            {showLog ? 'Скрыть лог' : 'Показать лог'}
          </button>
          {showLog && <DebugLog />}
        </div>
      )}
      <footer className="foot">Демо-данные. Тексты и этапы не являются регламентами Авито.</footer>
    </div>
  )
}
