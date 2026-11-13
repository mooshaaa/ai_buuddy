import type { DebugInfo } from '../types'

export default function DebugLine({ info }: { info: DebugInfo }) {
  const fellBack = info.source === 'stub' && info.note
  const label =
    info.source === 'llm' ? `модель ${info.model}` : info.source === 'error' ? 'ошибка' : fellBack ? 'заглушка (откат)' : 'заглушка'
  return (
    <p className={`debug-line debug-${info.source}${fellBack ? ' debug-fallback' : ''}`} title={info.note || undefined}>
      <span className="dot" aria-hidden="true" />
      {label} · {info.intent} · {info.latency_ms} мс
      {fellBack && <span className="debug-note"> · {info.note}</span>}
    </p>
  )
}
