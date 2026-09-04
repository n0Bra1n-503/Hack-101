// Centralized API layer. Every network call in the app goes through here —
// do not fetch() directly from components/pages.
//
// USE_MOCKS lets Phase 1 pages run against mockData.js before the backend
// exists. Flip it off (or set VITE_USE_MOCKS=false) once Mitali's endpoints
// are live; page code should not need to change either way.

import {
  mockStations,
  mockSummary,
  mockAnomalies,
  mockMaintenanceQueue,
  mockDigitalTwin,
  mockRisks,
  mockPublicRisk,
  mockCascade,
} from './mockData.js'

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false'
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`API ${res.status} ${res.statusText} on ${path}: ${body}`)
  }
  if (res.status === 204) return null
  return res.json()
}

function delay(value, ms = 300) {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export async function getStations() {
  if (USE_MOCKS) return delay(mockStations)
  return request('/stations')
}

export async function getStation(id) {
  if (USE_MOCKS) return delay(mockStations.find((s) => s.id === id) ?? null)
  return request(`/stations/${id}`)
}

export async function getReadings(id) {
  if (USE_MOCKS) return delay([])
  return request(`/stations/${id}/readings`)
}

export async function getHealth(id) {
  if (USE_MOCKS) return delay(mockDigitalTwin(id))
  return request(`/stations/${id}/health`)
}

export async function getSummary() {
  if (USE_MOCKS) return delay(mockSummary)
  return request('/summary')
}

export async function getAnomalies() {
  if (USE_MOCKS) return delay(mockAnomalies)
  return request('/anomalies')
}

export async function getAnomaly(id) {
  if (USE_MOCKS) return delay(mockAnomalies.find((a) => a.id === id) ?? null)
  return request(`/anomalies/${id}`)
}

export async function getMaintenance() {
  if (USE_MOCKS) return delay(mockMaintenanceQueue)
  return request('/maintenance')
}

export async function submitCorrection(id, action) {
  // action: 'accept' | 'reject' | 'review'
  if (USE_MOCKS) return delay({ id, action, status: 'ok' })
  return request(`/corrections/${id}/${action}`, { method: 'POST' })
}

export async function getCascade(id) {
  if (USE_MOCKS) return delay(mockCascade(id))
  return request(`/cascade/${id}`)
}

// Disaster Risk (validated, station-evidenced events)
export async function getRisks() {
  if (USE_MOCKS) return delay(mockRisks)
  return request('/risks')
}

export async function getRisk(id) {
  if (USE_MOCKS) return delay(mockRisks.find((r) => r.id === id) ?? null)
  return request(`/risks/${id}`)
}

export async function getAreaRisk(area) {
  if (USE_MOCKS) return delay(mockRisks.find((r) => r.area.toLowerCase() === String(area).toLowerCase()) ?? null)
  return request(`/risks/area/${encodeURIComponent(area)}`)
}

// Public/citizen-facing risk — simplified shape, no internal detail.
export async function getPublicRisk(area) {
  if (USE_MOCKS) return delay(mockPublicRisk(area))
  return request(`/public/risk/${encodeURIComponent(area)}`)
}

// Demo/replay controls (Phase 11)
export async function startReplay(speed = 1) {
  if (USE_MOCKS) return delay({ status: 'started', speed })
  return request('/replay/start', { method: 'POST', body: JSON.stringify({ speed }) })
}

export async function stopReplay() {
  if (USE_MOCKS) return delay({ status: 'stopped' })
  return request('/replay/stop', { method: 'POST' })
}

export async function injectScenario(scenario) {
  // scenario: 'spike_55c' | 'genuine_heat_event' | 'degradation'
  if (USE_MOCKS) return delay({ status: 'injected', scenario })
  return request('/scenarios/inject', { method: 'POST', body: JSON.stringify({ scenario }) })
}
