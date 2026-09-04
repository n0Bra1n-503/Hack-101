import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMaintenance } from '../services/api.js'
import StatusBadge from '../components/StatusBadge.jsx'
import LoadingState from '../components/LoadingState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'

const PRIORITY_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 }

export default function Maintenance() {
  const [queue, setQueue] = useState(null)
  const [error, setError] = useState(null)
  const [priorityFilter, setPriorityFilter] = useState('ALL')
  const [sortBy, setSortBy] = useState('priority')

  function load() {
    setError(null)
    setQueue(null)
    getMaintenance().then(setQueue).catch((err) => setError(err.message))
  }

  useEffect(load, [])

  const rows = useMemo(() => {
    if (!queue) return []
    let filtered = priorityFilter === 'ALL' ? queue : queue.filter((r) => r.priority === priorityFilter)
    filtered = [...filtered].sort((a, b) => {
      if (sortBy === 'priority') return (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9)
      if (sortBy === 'health') return a.health - b.health
      if (sortBy === 'trust') return a.trust - b.trust
      return 0
    })
    return filtered
  }, [queue, priorityFilter, sortBy])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!queue) return <LoadingState label="Loading maintenance queue…" />

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-lg font-semibold">Maintenance Queue</h1>
        <div className="flex gap-2 text-sm">
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-panel border border-hairline rounded-md px-2 py-1"
          >
            <option value="ALL">All priorities</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-panel border border-hairline rounded-md px-2 py-1"
          >
            <option value="priority">Sort: Priority</option>
            <option value="health">Sort: Health</option>
            <option value="trust">Sort: Trust</option>
          </select>
        </div>
      </div>

      {!rows.length ? (
        <EmptyState message="Maintenance queue is empty." />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-hairline">
          <table className="w-full text-sm">
            <thead className="bg-canvas text-inkMuted text-xs uppercase">
              <tr>
                <th className="text-left px-3 py-2">Priority</th>
                <th className="text-left px-3 py-2">Sensor</th>
                <th className="text-left px-3 py-2">Health</th>
                <th className="text-left px-3 py-2">Trust</th>
                <th className="text-left px-3 py-2">Trend</th>
                <th className="text-left px-3 py-2">Faults (30d)</th>
                <th className="text-left px-3 py-2">Reason</th>
                <th className="text-left px-3 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.stationId} className="border-t border-hairline bg-panel hover:bg-canvas">
                  <td className="px-3 py-2"><StatusBadge status={r.priority} /></td>
                  <td className="px-3 py-2 font-medium">{r.stationId}</td>
                  <td className="px-3 py-2">{r.health}</td>
                  <td className="px-3 py-2">{r.trust}</td>
                  <td className="px-3 py-2 capitalize">{r.trend}</td>
                  <td className="px-3 py-2">{r.faults30d}</td>
                  <td className="px-3 py-2 text-inkMuted">{r.reason}</td>
                  <td className="px-3 py-2">
                    <Link to={`/investigation/${r.stationId}`} className="text-accent underline hover:text-accentHover">
                      Investigate
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
