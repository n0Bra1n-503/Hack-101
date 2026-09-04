import { NavLink, Routes, Route } from 'react-router-dom'
import CommandCenter from './pages/CommandCenter.jsx'
import StationMap from './pages/StationMap.jsx'
import Investigation from './pages/Investigation.jsx'
import DigitalTwin from './pages/DigitalTwin.jsx'
import Maintenance from './pages/Maintenance.jsx'
import CascadeSimulator from './pages/CascadeSimulator.jsx'
import DisasterRisk from './pages/DisasterRisk.jsx'
import CitizenSafety from './pages/CitizenSafety.jsx'
import ConnectionIndicator from './components/ConnectionIndicator.jsx'

const NAV_ITEMS = [
  { to: '/', label: 'Command Center', end: true },
  { to: '/map', label: 'Station Map' },
  { to: '/investigation', label: 'Investigation' },
  { to: '/digital-twin', label: 'Digital Twin' },
  { to: '/maintenance', label: 'Maintenance' },
  { to: '/cascade', label: 'Cascade' },
  { to: '/disaster-risk', label: 'Disaster Risk' },
  { to: '/public-safety', label: 'Public Safety' },
]

export default function App() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 shrink-0 border-r border-hairline bg-panel sticky top-0 h-screen flex flex-col">
        <div className="px-4 py-4 border-b border-hairline">
          <div className="font-semibold tracking-tight text-lg">
            SkyGuard <span className="text-inkMuted font-normal">AI</span>
          </div>
        </div>

        <nav className="flex-1 px-2 py-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-accent text-white'
                    : 'text-inkMuted hover:bg-hairline/60'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-3 border-t border-hairline">
          <ConnectionIndicator />
        </div>
      </aside>

      <main className="flex-1 min-w-0 px-6 py-6">
        <Routes>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/map" element={<StationMap />} />
          <Route path="/investigation" element={<Investigation />} />
          <Route path="/investigation/:stationId" element={<Investigation />} />
          <Route path="/digital-twin" element={<DigitalTwin />} />
          <Route path="/digital-twin/:stationId" element={<DigitalTwin />} />
          <Route path="/maintenance" element={<Maintenance />} />
          <Route path="/cascade" element={<CascadeSimulator />} />
          <Route path="/disaster-risk" element={<DisasterRisk />} />
          <Route path="/public-safety" element={<CitizenSafety />} />
        </Routes>
      </main>
    </div>
  )
}
