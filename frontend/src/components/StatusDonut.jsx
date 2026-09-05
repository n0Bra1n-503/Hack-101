import { useState } from 'react'

// Part-to-whole donut for a small, fixed set of status categories (<=6).
// Segment order is fixed by the caller (Healthy -> Degrading -> Critical),
// never re-sorted by value, so a color always means the same status.

const SIZE = 200
const CENTER = SIZE / 2
const RADIUS = 74
const STROKE = 24
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const GAP = 4 // px of circumference left as a surface gap between segments

// segments: [{ key, label, value, color }]
export default function StatusDonut({ segments, centerLabel }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0)
  const [active, setActive] = useState(null)
  const [showTable, setShowTable] = useState(false)

  let cumulative = 0
  const arcs = segments.map((s) => {
    const rawLen = total > 0 ? (s.value / total) * CIRCUMFERENCE : 0
    const len = Math.max(rawLen - GAP, 0)
    const offset = -cumulative
    cumulative += rawLen
    return { ...s, len, offset }
  })

  const pct = (v) => (total ? Math.round((v / total) * 100) : 0)

  return (
    <div className="flex flex-col sm:flex-row gap-6 items-center">
      <div className="relative shrink-0" style={{ width: SIZE, height: SIZE }}>
        <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
          <g transform={`rotate(-90 ${CENTER} ${CENTER})`}>
            <circle cx={CENTER} cy={CENTER} r={RADIUS} fill="none" stroke="#E4E8FB" strokeWidth={STROKE} strokeOpacity={0.8} />
            {arcs.map((a, i) => (
              <circle
                key={a.key}
                cx={CENTER}
                cy={CENTER}
                r={RADIUS}
                fill="none"
                stroke={a.color}
                strokeWidth={STROKE}
                strokeDasharray={`${a.len} ${CIRCUMFERENCE - a.len}`}
                strokeDashoffset={a.offset}
                strokeLinecap="butt"
                tabIndex={0}
                role="img"
                aria-label={`${a.label}: ${a.value} of ${total} stations, ${pct(a.value)} percent`}
                onMouseEnter={() => setActive(i)}
                onMouseLeave={() => setActive(null)}
                onFocus={() => setActive(i)}
                onBlur={() => setActive(null)}
                style={{
                  cursor: 'pointer',
                  outline: 'none',
                  opacity: active === null || active === i ? 1 : 0.5,
                  transition: 'opacity 120ms',
                }}
              />
            ))}
          </g>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="text-3xl font-semibold text-ink">{total}</div>
          <div className="text-xs text-inkMuted">{centerLabel}</div>
        </div>
        {active !== null && (
          <div className="absolute left-1/2 -translate-x-1/2 bottom-0 translate-y-[110%] bg-ink text-white text-xs rounded-md px-2 py-1 shadow-md whitespace-nowrap pointer-events-none z-10">
            <span className="font-semibold">{segments[active].value}</span> {segments[active].label} · {pct(segments[active].value)}%
          </div>
        )}
      </div>

      <div className="flex-1 w-full">
        <ul className="space-y-1.5 text-sm">
          {segments.map((s, i) => (
            <li key={s.key} className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2 text-ink">
                <span className="h-2.5 w-2.5 rounded-sm shrink-0" style={{ backgroundColor: s.color }} />
                {s.label}
              </span>
              <span className="text-inkMuted">{s.value} · {pct(s.value)}%</span>
            </li>
          ))}
        </ul>
        <button
          onClick={() => setShowTable((v) => !v)}
          className="mt-3 text-xs text-accent underline hover:text-accentHover"
        >
          {showTable ? 'Hide table view' : 'View as table'}
        </button>
        {showTable && (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-xs border border-hairline rounded-md overflow-hidden">
              <thead className="bg-canvas text-inkMuted">
                <tr>
                  <th className="text-left px-2 py-1">Status</th>
                  <th className="text-left px-2 py-1">Stations</th>
                  <th className="text-left px-2 py-1">Share</th>
                </tr>
              </thead>
              <tbody>
                {segments.map((s) => (
                  <tr key={s.key} className="border-t border-hairline">
                    <td className="px-2 py-1">{s.label}</td>
                    <td className="px-2 py-1">{s.value}</td>
                    <td className="px-2 py-1">{pct(s.value)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
