import { AlertTriangle, Inbox } from 'lucide-react'

export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="state-panel">
      <Inbox size={28} aria-hidden="true" />
      <h2>{title}</h2>
      {detail ? <p>{detail}</p> : null}
    </div>
  )
}

export function ErrorState({ title = 'Service unavailable', detail }: { title?: string; detail?: string }) {
  return (
    <div className="state-panel state-error">
      <AlertTriangle size={28} aria-hidden="true" />
      <h2>{title}</h2>
      {detail ? <p>{detail}</p> : <p>The screen is wired to the Gateway and will recover when the endpoint responds.</p>}
    </div>
  )
}

export function LoadingState({ label }: { label: string }) {
  return <div className="loading-line">{label}</div>
}
