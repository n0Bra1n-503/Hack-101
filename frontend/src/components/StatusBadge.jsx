// The status colors are pale pastels (~2:1 contrast on white) — too light to
// read as text, so the badge wears the color as a background wash and keeps
// the label in `ink`, never in the series color itself.
const STYLES = {
  healthy: 'bg-healthy text-ink border-healthy',
  degrading: 'bg-degrading text-ink border-degrading',
  critical: 'bg-critical text-ink border-critical',
  pending: 'bg-hairline/50 text-inkMuted border-hairline',
  unknown: 'bg-hairline/50 text-inkMuted border-hairline',
}

// status: 'healthy' | 'degrading' | 'critical' | 'pending' | any string
export default function StatusBadge({ status }) {
  const key = (status || 'unknown').toLowerCase()
  const style = STYLES[key] || STYLES.unknown
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full border text-xs font-medium capitalize ${style}`}>
      {status || 'unknown'}
    </span>
  )
}
