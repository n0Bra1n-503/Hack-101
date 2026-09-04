// Renders a Trust Score received from the backend. Never compute the score
// here — this component only displays trust (0-100) supplied by the API.
export default function TrustScore({ value, size = 'md' }) {
  const v = Math.max(0, Math.min(100, value ?? 0))
  const dims = size === 'lg' ? 'text-4xl' : size === 'sm' ? 'text-base' : 'text-2xl'

  return (
    <div>
      {/* the pastel status colors are too pale for text — number stays ink, the bar below carries tone */}
      <div className={`font-semibold text-ink ${dims}`}>{v}</div>
      <div className="w-24 h-1.5 bg-hairline rounded-full overflow-hidden mt-1">
        <div
          className={`h-full rounded-full ${v >= 70 ? 'bg-healthy' : v >= 40 ? 'bg-degrading' : 'bg-critical'}`}
          style={{ width: `${v}%` }}
        />
      </div>
    </div>
  )
}
