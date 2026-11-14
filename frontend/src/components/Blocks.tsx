import { useState } from 'react'
import { api } from '../api'
import type { ActionCardBlock, Block, SourceItem, User } from '../types'

const KIND: Record<string, string> = { day_off: 'Отгул', vacation: 'Отпуск' }

function formatDate(iso: unknown) {
  if (typeof iso !== 'string') return '—'
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

function ActionCard({
  block,
  user,
  onUpdate,
}: {
  block: ActionCardBlock
  user: User
  onUpdate: (b: ActionCardBlock) => void
}) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  async function run(kind: 'confirm' | 'cancel') {
    setBusy(true)
    setErr('')
    try {
      onUpdate(await api[kind](user.id, block.action_id))
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Не удалось выполнить действие')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className={`card card-${block.status}`} aria-label={block.title}>
      <h3>{block.title}</h3>
      <dl>
        <dt>Тип</dt>
        <dd>{KIND[String(block.params.kind)] ?? '—'}</dd>
        <dt>Дата</dt>
        <dd>{formatDate(block.params.date)}</dd>
      </dl>

      {block.status === 'needs_confirmation' && (
        <div className="card-actions">
          <button className="btn primary" disabled={busy} onClick={() => run('confirm')}>
            Подтвердить
          </button>
          <button className="btn" disabled={busy} onClick={() => run('cancel')}>
            Отменить
          </button>
        </div>
      )}
      {block.status === 'done' && (
        <p className="card-status ok">Заявка {String(block.result?.request_id ?? '')} отправлена</p>
      )}
      {block.status === 'rejected' && <p className="card-status">Заявка отменена</p>}
      {err && <p className="card-status bad">{err}</p>}
    </section>
  )
}

function Sources({ items }: { items: SourceItem[] }) {
  return (
    <div className="sources" aria-label="Источники ответа">
      <span className="sources-label">{items.length > 1 ? 'Источники' : 'Источник'}</span>
      {items.map((s) => (
        <div key={s.id} className={`source-chip${s.synthetic ? ' source-demo' : ''}`}>
          <strong>{s.title}</strong>
          <span>
            {s.source}
            {s.synthetic && <em className="demo-tag">демо</em>}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function Blocks({
  blocks,
  user,
  onUpdate,
}: {
  blocks: Block[]
  user: User
  onUpdate: (index: number, b: ActionCardBlock) => void
}) {
  return (
    <>
      {blocks.map((b, i) => {
        if (b.type === 'text') return <p key={i} className="bubble">{b.text}</p>
        if (b.type === 'error') return <p key={i} className="bubble bubble-error" role="alert">{b.text}</p>
        if (b.type === 'source') return <Sources key={i} items={b.items} />
        return <ActionCard key={i} block={b} user={user} onUpdate={(nb) => onUpdate(i, nb)} />
      })}
    </>
  )
}
