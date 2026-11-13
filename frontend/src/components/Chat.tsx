import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Message, User } from '../types'
import Blocks from './Blocks'
import DebugLine from './DebugLine'

const SUGGESTIONS: Record<User['role'], string[]> = {
  intern: ['Хочу отгул 20 ноября', 'Что мне делать дальше?', 'Как получить доступы?', 'Покажи прогресс стажёра'],
  mentor: ['Покажи прогресс стажёра', 'Что мне делать дальше?', 'Что такое экватор?'],
}

export default function Chat({ user, onChange }: { user: User; onChange: () => void }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const nextId = useRef(1)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' })
  }, [messages, busy])

  async function send(raw: string) {
    const message = raw.trim()
    if (!message || busy) return
    setText('')
    setMessages((m) => [...m, { id: nextId.current++, from: 'user', blocks: [{ type: 'text', text: message }] }])
    setBusy(true)
    try {
      const { blocks, debug } = await api.chat(user.id, message)
      setMessages((m) => [...m, { id: nextId.current++, from: 'bot', blocks, debug }])
    } catch {
      setMessages((m) => [
        ...m,
        { id: nextId.current++, from: 'bot', blocks: [{ type: 'error', text: 'Сервер не ответил. Попробуй ещё раз через минуту.' }] },
      ])
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="chat" aria-label="Чат с помощником">
      <div className="chat-scroll">
        {messages.length === 0 && (
          <div className="empty">
            <h2>Привет, {user.name.split(' ')[0]}</h2>
            <p>Спроси про адаптацию или попроси оформить отгул.</p>
            <div className="chips">
              {SUGGESTIONS[user.role].map((s) => (
                <button key={s} className="chip" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`msg msg-${m.from}`}>
            <Blocks
              blocks={m.blocks}
              user={user}
              onUpdate={(i, nb) => {
                setMessages((all) =>
                  all.map((x) => (x.id === m.id ? { ...x, blocks: x.blocks.map((b, j) => (j === i ? nb : b)) } : x)),
                )
                onChange()
              }}
            />
            {m.debug && <DebugLine info={m.debug} />}
          </div>
        ))}
        {busy && <div className="msg msg-bot"><p className="bubble typing" aria-live="polite">Думаю…</p></div>}
        <div ref={endRef} />
      </div>

      <div className="composer">
        <input
          value={text}
          placeholder="Напиши сообщение"
          aria-label="Сообщение"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send(text)}
        />
        <button className="btn primary" disabled={busy || !text.trim()} onClick={() => send(text)}>
          Отправить
        </button>
      </div>
    </section>
  )
}
