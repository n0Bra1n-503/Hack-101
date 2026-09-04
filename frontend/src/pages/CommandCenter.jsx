import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSummary, getAnomalies, getMaintenance } from '../services/api.js'
import MetricCard from '../components/MetricCard.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import StatusDonut from '../components/StatusDonut.jsx'
import RadialMeter from '../components/RadialMeter.jsx'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

export default function CommandCenter() {
  const [summary, setSummary] = useState(null)
  const [anomalies, setAnomalies] = useState(null)
  const [maintenance, setMaintenance] = useState(null)
  const [error, setError] = useState(null)

  function load() {
    setError(null)
    setSummary(null)
    setAnomalies(null)
    setMaintenance(null)
    Promise.all([getSummary(), getAnomalies(), getMaintenance()])
      .then(([s, a, m]) => {
        setSummary(s)
        setAnomalies(a)
        setMaintenance(m)
      })
      .catch((err) => setError(err.message))
  }

  useEffect(load, [])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!summary) return <LoadingState label="Loading network status…" />

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-lg font-semibold mb-3">Network Status</h1>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <MetricCard label="Total Stations" value={summary.totalStations} />
          <MetricCard label="Healthy" value={summary.healthy} tone="healthy" />
          <MetricCard label="Degrading" value={summary.degrading} tone="degrading" />
          <MetricCard label="Critical" value={summary.critical} tone="critical" />
          <MetricCard label="Active Anomalies" value={summary.activeAnomalies} />
          <MetricCard label="Average Trust" value={`${summary.averageTrust}%`} />
        </div>
      </section>

      <section>
        <h1 className="text-lg font-semibold mb-3">Network Health</h1>
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 rounded-lg border border-hairline bg-panel p-4">
            <h2 className="text-sm font-medium text-inkMuted mb-3">Station Status Breakdown</h2>
            <StatusDonut
              centerLabel="Stations"
              segments={[
                { key: 'healthy', label: 'Healthy', value: summary.healthy, color: '#9BD8FA' },
                { key: 'degrading', label: 'Degrading', value: summary.degrading, color: '#CBD9FA' },
                { key: 'critical', label: 'Critical', value: summary.critical, color: '#FCDCD8' },
              ]}
            />
          </div>
          <div className="rounded-lg border border-hairline bg-panel p-4 flex flex-col items-center justify-center">
            <h2 className="text-sm font-medium text-inkMuted mb-3 self-start">Average Trust</h2>
            <RadialMeter value={summary.averageTrust} label="Average Trust" />
          </div>
        </div>
      </section>

      <div className="grid lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 rounded-lg border border-hairline bg-panel p-4">
          <h2 className="text-sm font-medium text-inkMuted mb-3">Station Map</h2>
          <div className="text-inkMuted text-sm">
            See <Link to="/map" className="underline text-accent hover:text-accentHover">Station Map</Link> for the full live map.
          </div>
        </section>

        <section className="rounded-lg border border-hairline bg-panel p-4">
          <h2 className="text-sm font-medium text-inkMuted mb-3">Live Anomaly Feed</h2>
          {anomalies?.length ? (
            <ul className="space-y-2">
              {anomalies.map((a) => (
                <li key={a.id}>
                  <Link
                    to={`/investigation/${a.stationId}`}
                    className="block rounded-md border border-hairline p-2 hover:bg-hairline/40"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{a.stationId}</span>
                      <StatusBadge status={a.decision} />
                    </div>
                    <div className="text-xs text-inkMuted mt-1">
                      {a.variable} · {a.faultType} · trust {a.trustScore}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState message="No active anomalies." />
          )}
        </section>
      </div>

      <section className="rounded-lg border border-hairline bg-panel p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-inkMuted">Maintenance Preview</h2>
          <Link to="/maintenance" className="text-xs text-accent underline hover:text-accentHover">
            View full queue
          </Link>
        </div>
        {maintenance?.length ? (
          <ul className="space-y-2">
            {maintenance.slice(0, 3).map((m) => (
              <li key={m.stationId} className="flex items-center justify-between text-sm border border-hairline rounded-md p-2">
                <span className="font-medium">{m.stationId}</span>
                <span className="text-inkMuted">{m.reason}</span>
                <StatusBadge status={m.priority} />
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState message="Maintenance queue is empty." />
        )}
      </section>
    </div>
  )
}
