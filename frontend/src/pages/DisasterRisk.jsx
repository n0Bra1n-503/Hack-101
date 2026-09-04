import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRisks } from '../services/api.js'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

// HIGH/MEDIUM/LOW risk levels reuse the same status semantics as everywhere
// else (critical/degrading/healthy tones), just labeled for disaster risk.
// The status colors are pale pastels, so they carry the badge background —
// the label itself always stays `ink`.
const RISK_STYLES = {
  HIGH: 'bg-critical border-critical',
  MEDIUM: 'bg-degrading border-degrading',
  LOW: 'bg-healthy border-healthy',
}

export default function DisasterRisk() {
  const [risks, setRisks] = useState(null)
  const [error, setError] = useState(null)

  function load() {
    setError(null)
    setRisks(null)
    getRisks().then(setRisks).catch((err) => setError(err.message))
  }

  useEffect(load, [])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!risks) return <LoadingState label="Loading disaster risk assessments…" />
  if (!risks.length) return <EmptyState message="No active disaster risk events." />

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Disaster Risk</h1>

      {risks.map((r) => (
        <article key={r.id} className="rounded-lg border border-hairline bg-panel p-5 space-y-4">
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <span className={`inline-block px-2.5 py-1 rounded-full border text-xs font-semibold text-ink ${RISK_STYLES[r.riskLevel] || RISK_STYLES.LOW}`}>
                {r.riskLevel} RISK
              </span>
              <h2 className="text-xl font-semibold mt-2">{r.event}</h2>
            </div>
            <div className="text-right">
              <div className="text-xs uppercase text-inkMuted">Area</div>
              <div className="text-base font-medium">{r.area}</div>
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-xs uppercase text-inkMuted">Reading</div>
              <div className="text-lg font-semibold">{r.value} {r.unit}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-inkMuted">Confidence</div>
              <div className="text-lg font-semibold">{Math.round(r.confidence * 100)}%</div>
            </div>
            <div>
              <div className="text-xs uppercase text-inkMuted">Validated</div>
              <div className="inline-flex items-center gap-1.5 text-lg font-semibold text-ink mt-0.5">
                <span className={`h-2.5 w-2.5 rounded-full ${r.validated ? 'bg-healthy' : 'bg-degrading'}`} />
                {r.validated ? 'Yes' : 'Pending'}
              </div>
            </div>
          </div>

          <div>
            <div className="text-xs uppercase text-inkMuted mb-2">Evidence</div>
            <ul className="space-y-1 text-sm">
              {r.evidence.map((e, i) => (
                <li key={i} className="flex items-center gap-2 text-ink">
                  <span className="flex items-center justify-center h-4 w-4 rounded-full bg-healthy text-[10px]">✓</span> {e}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <div className="text-xs uppercase text-inkMuted mb-2">Affected Stations</div>
            <div className="flex flex-wrap gap-2">
              {r.affectedStations.map((id) => (
                <Link
                  key={id}
                  to={`/investigation/${id}`}
                  className="text-sm px-2 py-1 rounded-md border border-hairline hover:bg-hairline/40 text-ink"
                >
                  {id}
                </Link>
              ))}
            </div>
          </div>
        </article>
      ))}
    </div>
  )
}
