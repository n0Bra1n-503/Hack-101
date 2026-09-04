import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getStations, getHealth } from '../services/api.js'
import TrustScore from '../components/TrustScore.jsx'
import MetricCard from '../components/MetricCard.jsx'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

export default function DigitalTwin() {
  const { stationId: paramId } = useParams()
  const [stations, setStations] = useState(null)
  const [stationId, setStationId] = useState(paramId || null)
  const [twin, setTwin] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getStations().then((s) => {
      setStations(s)
      if (!stationId && s.length) setStationId(s[0].id)
    }).catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!stationId) return
    setTwin(null)
    setError(null)
    getHealth(stationId).then(setTwin).catch((err) => setError(err.message))
  }, [stationId])

  if (error) return <ErrorState message={error} onRetry={() => setError(null)} />
  if (!stations) return <LoadingState label="Loading stations…" />
  if (!stations.length) return <EmptyState message="No stations available." />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Digital Twin</h1>
        <select
          value={stationId ?? ''}
          onChange={(e) => setStationId(e.target.value)}
          className="bg-panel border border-hairline rounded-md px-2 py-1 text-sm"
        >
          {stations.map((s) => (
            <option key={s.id} value={s.id}>{s.id}</option>
          ))}
        </select>
      </div>

      {!twin ? (
        <LoadingState label="Loading digital twin…" />
      ) : (
        <div className="space-y-6">
          <div className="grid sm:grid-cols-3 gap-3">
            <MetricCard label="Health Score" value={twin.health} />
            <div className="rounded-lg border border-hairline bg-panel p-4">
              <div className="text-xs uppercase tracking-wide text-inkMuted mb-1">Trust Score</div>
              <TrustScore value={twin.trust} size="lg" />
            </div>
            <MetricCard label="Trend" value={twin.trend} tone={twin.trend === 'declining' ? 'critical' : 'healthy'} />
          </div>

          <section className="rounded-lg border border-hairline bg-panel p-4">
            <h2 className="text-sm font-medium text-inkMuted mb-3">Fault History</h2>
            {twin.faultHistory?.length ? (
              <ul className="space-y-1 text-sm">
                {twin.faultHistory.map((f, i) => (
                  <li key={i} className="flex justify-between border-b border-hairline py-1">
                    <span className="text-inkMuted">{f.date}</span>
                    <span className="capitalize">{f.type}</span>
                    <span className="text-inkMuted">{f.variable}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState message="No recorded faults." />
            )}
          </section>

          <section className="rounded-lg border border-hairline bg-panel p-4">
            <h2 className="text-sm font-medium text-inkMuted mb-2">Maintenance Priority</h2>
            <div className="text-2xl font-semibold">{twin.maintenancePriority}</div>
          </section>
        </div>
      )}
    </div>
  )
}
