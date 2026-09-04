// label: string, value: string|number, tone: 'default'|'healthy'|'degrading'|'critical'
// The number always stays `ink` (the pastel status colors are too pale to
// read as text) — tone shows as a colored left border instead.
const TONE_BORDER = {
  default: 'border-l-hairline',
  healthy: 'border-l-healthy',
  degrading: 'border-l-degrading',
  critical: 'border-l-critical',
}

export default function MetricCard({ label, value, tone = 'default' }) {
  return (
    <div className={`rounded-lg border border-hairline border-l-4 ${TONE_BORDER[tone] || TONE_BORDER.default} bg-panel p-4`}>
      <div className="text-xs uppercase tracking-wide text-inkMuted">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-ink">{value}</div>
    </div>
  )
}
