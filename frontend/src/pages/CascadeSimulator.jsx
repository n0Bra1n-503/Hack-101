import { useEffect, useState } from 'react'
import { getAnomalies, getCascade, startReplay, stopReplay, injectScenario } from '../services/api.js'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

export default function CascadeSimulator() {
  const [anomalies, setAnomalies] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [cascade, setCascade] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null) // which control button is running

  useEffect(() => {
    getAnomalies().then((a) => {
      setAnomalies(a)
      if (a.length) setSelectedId(a[0].id)
    }).catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    setCascade(null)
    getCascade(selectedId).then(setCascade).catch((err) => setError(err.message))
  }, [selectedId])

  async function runControl(name, fn, ...args) {
    setBusy(name)
    try {
      await fn(...args)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  if (error) return <ErrorState message={error} onRetry={() => setError(null)} />
  if (!anomalies) return <LoadingState label="Loading scenarios…" />
  if (!anomalies.length) return <EmptyState message="No anomaly scenarios available to simulate." />

  const controls = [
    { key: 'start', label: 'Start Replay', fn: () => startReplay() },
    { key: 'pause', label: 'Pause', fn: () => stopReplay() },
    { key: 'reset', label: 'Reset', fn: () => stopReplay() },
    { key: 'spike', label: 'Inject 55°C Spike', fn: () => injectScenario('spike_55c') },
    { key: 'heat', label: 'Run Genuine Heat Event', fn: () => injectScenario('genuine_heat_event') },
    { key: 'degrade', label: 'Run Degradation Scenario', fn: () => injectScenario('degradation') },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-lg font-semibold">Cascade Simulator</h1>
        <select
          value={selectedId ?? ''}
          onChange={(e) => setSelectedId(e.target.value)}
          className="bg-panel border border-hairline rounded-md px-2 py-1 text-sm"
        >
          {anomalies.map((a) => (
            <option key={a.id} value={a.id}>{a.id} — {a.stationId}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap gap-2">
        {controls.map((c) => (
          <button
            key={c.key}
            disabled={busy !== null}
            onClick={() => runControl(c.key, c.fn)}
            className="px-3 py-1.5 rounded-md border border-hairline text-sm hover:bg-hairline/40 disabled:opacity-50"
          >
            {busy === c.key ? '…' : c.label}
          </button>
        ))}
      </div>

      {!cascade ? (
        <LoadingState label="Loading cascade impact…" />
      ) : (
        <div className="space-y-4">
          <div className="text-center text-sm text-inkMuted">BAD READING → SkyGuard →</div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="rounded-lg border border-hairline bg-panel p-5">
              <div className="inline-block bg-critical text-ink text-xs uppercase font-semibold px-2 py-1 rounded-md mb-2">Without SkyGuard</div>
              <div className="text-xl font-semibold text-ink">{cascade.withoutSkyguard.label}</div>
              <p className="text-sm text-inkMuted mt-2">{cascade.withoutSkyguard.description}</p>
            </div>
            <div className="rounded-lg border border-hairline bg-panel p-5">
              <div className="inline-block bg-healthy text-ink text-xs uppercase font-semibold px-2 py-1 rounded-md mb-2">With SkyGuard</div>
              <div className="text-xl font-semibold text-ink">{cascade.withSkyguard.label}</div>
              <p className="text-sm text-inkMuted mt-2">{cascade.withSkyguard.description}</p>
            </div>
          </div>
          <div className="rounded-lg border border-hairline bg-panel p-4 text-sm">
            <span className="font-medium">Impact summary: </span>
            {cascade.impactSummary}
          </div>
          {cascade.illustrative && (
            <p className="text-xs text-inkMuted">
              Note: this downstream effect is an illustrative simulation, not the real IMD forecasting model.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
