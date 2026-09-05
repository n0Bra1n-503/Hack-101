// A single ratio against a 0-100 limit (e.g. Average Trust). The fill carries
// severity; the unfilled track is a lighter step of the SAME hue, so state
// reads across the whole ring rather than needing the number.

const SIZE = 160
const CENTER = SIZE / 2
const RADIUS = 62
const STROKE = 14
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

function toneFor(value) {
  if (value >= 70) return '#9BD8FA' // healthy
  if (value >= 40) return '#CBD9FA' // degrading
  return '#FCDCD8' // critical
}

export default function RadialMeter({ value, label }) {
  const v = Math.max(0, Math.min(100, value ?? 0))
  const color = toneFor(v)
  const len = (v / 100) * CIRCUMFERENCE

  return (
    <div className="relative shrink-0" style={{ width: SIZE, height: SIZE }}>
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label={`${label}: ${v} percent`}>
        <g transform={`rotate(-90 ${CENTER} ${CENTER})`}>
          <circle cx={CENTER} cy={CENTER} r={RADIUS} fill="none" stroke={color} strokeOpacity={0.4} strokeWidth={STROKE} />
          <circle
            cx={CENTER}
            cy={CENTER}
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth={STROKE}
            strokeDasharray={`${len} ${CIRCUMFERENCE - len}`}
            strokeLinecap="round"
          />
        </g>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-3xl font-semibold text-ink">{v}%</div>
        <div className="text-xs text-inkMuted text-center px-4">{label}</div>
      </div>
    </div>
  )
}
