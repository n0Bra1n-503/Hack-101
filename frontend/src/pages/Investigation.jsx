import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getAnomalies, submitCorrection } from '../services/api.js'
import TrustScore from '../components/TrustScore.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

export default function Investigation() {
  const { stationId } = useParams()
  const [anomalies, setAnomalies] = useState(null)
  const [error, setError] = useState(null)
  const [actionMsg, setActionMsg] = useState(null)

  function load() {
    setError(null)
    setAnomalies(null)
    getAnomalies().then(setAnomalies).catch((err) => setError(err.message))
  }

  useEffect(load, [])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!anomalies) return <LoadingState label="Loading anomaly evidence…" />

  const scoped = stationId ? anomalies.filter((a) => a.stationId === stationId) : anomalies

  if (!scoped.length) return <EmptyState message="No anomalies to investigate for this station." />

  async function handleAction(id, action) {
    setActionMsg(null)
    try {
      await submitCorrection(id, action)
      setActionMsg(`Recorded "${action}" for ${id}.`)
    } catch (err) {
      setActionMsg(`Failed to record action: ${err.message}`)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Investigation{stationId ? ` — ${stationId}` : ''}</h1>
      {actionMsg && (
        <div className="text-sm rounded-md border border-hairline bg-panel px-3 py-2 text-inkMuted">
          {actionMsg}
        </div>
      )}

      {scoped.map((a) => (
        <article key={a.id} className="rounded-lg border border-hairline bg-panel p-5 space-y-4">
          {/* 1. What happened? */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase text-inkMuted">Station · Variable</div>
              <div className="text-base font-medium">{a.stationId} · {a.variable}</div>
            </div>
            <StatusBadge status={a.status} />
          </div>
          <div className="text-sm text-inkMuted">
            Raw reading: <span className="text-ink font-medium">{a.reading.value} {a.reading.unit}</span>
            {' '}at {new Date(a.detectedAt).toLocaleString()}
          </div>

          {/* 2. Weather or sensor? + 3. Confidence */}
          <div className="grid sm:grid-cols-3 gap-4">
            <div>
              <div className="text-xs uppercase text-inkMuted">Decision</div>
              <div className="mt-1"><StatusBadge status={a.decision} /></div>
            </div>
            <div>
              <div className="text-xs uppercase text-inkMuted">Trust Score</div>
              <TrustScore value={a.trustScore} />
            </div>
            <div>
              <div className="text-xs uppercase text-inkMuted">Confidence</div>
              <div className="text-lg font-semibold mt-1">{Math.round(a.confidence * 100)}%</div>
            </div>
          </div>

          {/* 4. Why? Evidence */}
          <div>
            <div className="text-xs uppercase text-inkMuted mb-2">Evidence</div>
            <div className="grid sm:grid-cols-3 gap-2 text-sm">
              {Object.entries(a.evidence).map(([k, v]) => (
                <div key={k} className="flex justify-between rounded-md border border-hairline px-2 py-1">
                  <span className="text-inkMuted">{k.replace(/_/g, ' ')}</span>
                  <span className="font-medium">{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 5. Suggested correction */}
          <div className="rounded-md border border-hairline p-3 grid sm:grid-cols-3 gap-3 text-sm">
            <div>
              <div className="text-xs uppercase text-inkMuted">Original value</div>
              <div className="inline-flex items-center gap-1.5 mt-0.5">
                <span className="h-2 w-2 rounded-full bg-critical" />
                <span className="font-semibold text-ink">{a.reading.value} {a.reading.unit}</span>
              </div>
            </div>
            <div>
              <div className="text-xs uppercase text-inkMuted">Suggested value</div>
              <div className="inline-flex items-center gap-1.5 mt-0.5">
                <span className="h-2 w-2 rounded-full bg-healthy" />
                <span className="font-semibold text-ink">{a.suggestedCorrection} {a.reading.unit}</span>
              </div>
            </div>
            <div>
              <div className="text-xs uppercase text-inkMuted">Fault type</div>
              <div className="font-medium capitalize">{a.faultType}</div>
            </div>
          </div>

          {/* 6. What should I do? */}
          <div className="flex gap-2">
            <button
              onClick={() => handleAction(a.id, 'accept')}
              className="px-3 py-1.5 rounded-md bg-healthy text-ink border border-healthy text-sm font-medium hover:opacity-80"
            >
              ACCEPT
            </button>
            <button
              onClick={() => handleAction(a.id, 'reject')}
              className="px-3 py-1.5 rounded-md bg-critical text-ink border border-critical text-sm font-medium hover:opacity-80"
            >
              REJECT
            </button>
            <button
              onClick={() => handleAction(a.id, 'review')}
              className="px-3 py-1.5 rounded-md bg-hairline/50 text-inkMuted border border-hairline text-sm hover:bg-hairline"
            >
              REVIEW
            </button>
          </div>
        </article>
      ))}
    </div>
  )
}
