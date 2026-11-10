import { useEffect, useState } from 'react'
import { api } from './api'
import Chat from './components/Chat'
import StagesPanel from './components/StagesPanel'
import type { User } from './types'

export default function App() {
  const [users, setUsers] = useState<User[]>([])
  const [userId, setUserId] = useState<string>('')
  const [refresh, setRefresh] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .users()
      .then((list) => {
        setUsers(list)
        if (list.length) setUserId(list[0].id)
      })
      .catch(() => setError('Не удалось связаться с сервером. Проверь, что backend запущен.'))
  }, [])

  const user = users.find((u) => u.id === userId)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span>AI-buddy</span>
        </div>
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
      </header>

      {error && <div className="banner">{error}</div>}

      {user && (
        <main className="layout">
          <Chat key={user.id} user={user} onChange={() => setRefresh((n) => n + 1)} />
          <StagesPanel user={user} refreshKey={refresh} />
        </main>
      )}
      <footer className="foot">Демо-данные. Тексты и этапы не являются регламентами Авито.</footer>
    </div>
  )
}
