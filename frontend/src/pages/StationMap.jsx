import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import { Link } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import { getStations } from '../services/api.js'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

const STATUS_COLOR = {
  healthy: '#9BD8FA',
  degrading: '#CBD9FA',
  critical: '#FCDCD8',
}

export default function StationMap() {
  const [stations, setStations] = useState(null)
  const [error, setError] = useState(null)

  function load() {
    setError(null)
    setStations(null)
    getStations().then(setStations).catch((err) => setError(err.message))
  }

  useEffect(load, [])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!stations) return <LoadingState label="Loading stations…" />
  if (!stations.length) return <EmptyState message="No stations reporting." />

  const center = [stations[0].lat, stations[0].lon]

  return (
    <div className="space-y-3">
      <h1 className="text-lg font-semibold">Station Map</h1>
      <div className="rounded-lg overflow-hidden border border-hairline" style={{ height: '65vh' }}>
        <MapContainer center={center} zoom={5} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {stations.map((s) => (
            <CircleMarker
              key={s.id}
              center={[s.lat, s.lon]}
              radius={9}
              pathOptions={{ color: STATUS_COLOR[s.status] || '#7A7189', fillColor: STATUS_COLOR[s.status] || '#7A7189', fillOpacity: 0.8 }}
            >
              <Popup>
                <div className="text-sm space-y-1">
                  <div className="font-semibold">{s.id}</div>
                  <div>Trust: {s.trust} · Health: {s.health}</div>
                  <div>Status: {s.status}</div>
                  <div>Last anomaly: {s.lastAnomaly ?? 'none'}</div>
                  <Link to={`/investigation/${s.id}`} className="underline" style={{ color: '#9A57BD' }}>
                    Investigate →
                  </Link>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}
