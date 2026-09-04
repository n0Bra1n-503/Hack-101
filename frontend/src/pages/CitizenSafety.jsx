import { useEffect, useState } from 'react'
import { getPublicRisk } from '../services/api.js'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

// Public/citizen-facing view. Deliberately simpler than every other page:
// NO anomaly model names, raw sensor IDs, Trust Score breakdown, fault
// codes, or backend/debug info. SkyGuard is never presented as an official
// government warning authority — the disclaimer always ships with the card.
const AREAS = ['Delhi', 'Mumbai', 'Bengaluru'] // Bengaluru has no mock risk — demonstrates the empty state

// The status pastels are too pale to read as text, so the headline sits on
// a colored banner instead — text stays `ink`.
const RISK_BANNER = {
  HIGH: 'bg-critical',
  MEDIUM: 'bg-degrading',
  LOW: 'bg-healthy',
}

export default function CitizenSafety() {
  const [area, setArea] = useState(AREAS[0])
  const [risk, setRisk] = useState(undefined) // undefined = loading, null = no data for area
  const [error, setError] = useState(null)

  function load(a) {
    setError(null)
    setRisk(undefined)
    getPublicRisk(a).then(setRisk).catch((err) => setError(err.message))
  }

  useEffect(() => load(area), [area])

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Public Safety</h1>
        <select
          value={area}
          onChange={(e) => setArea(e.target.value)}
          className="bg-panel border border-hairline rounded-md px-2 py-1 text-sm"
        >
          {AREAS.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={() => load(area)} />
      ) : risk === undefined ? (
        <LoadingState label="Checking conditions…" />
      ) : risk === null ? (
        <EmptyState message={`No risk information available for ${area} right now.`} />
      ) : (
        <div className="rounded-2xl border border-hairline bg-panel p-8 text-center space-y-6">
          <div className="text-2xl font-semibold">{risk.area}</div>

          <div className={`inline-block text-3xl font-bold text-ink px-6 py-3 rounded-xl ${RISK_BANNER[risk.riskLevel] || 'bg-hairline'}`}>
            {risk.headline}
          </div>

          <div className="text-5xl font-bold text-ink">{risk.value}{risk.unit}</div>

          <div className="text-sm text-inkMuted">Confidence: {Math.round(risk.confidence * 100)}%</div>

          <p className="text-base text-ink">{risk.explanation}</p>

          <div className="text-left bg-canvas rounded-lg p-4">
            <div className="text-sm font-medium text-inkMuted mb-2">General guidance</div>
            <ul className="space-y-1 text-sm text-ink">
              {risk.guidance.map((g, i) => (
                <li key={i}>• {g}</li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-inkMuted border-t border-hairline pt-4">{risk.disclaimer}</p>
        </div>
      )}
    </div>
  )
}
