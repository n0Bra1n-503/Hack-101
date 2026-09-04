// Phase 1 mock data — mirrors the shape Mitali's backend contract will return.
// Swap real api.js calls in once /api/* endpoints exist; keep field names identical
// so pages don't need to change when you flip the switch.

export const mockStations = [
  { id: 'AWS-104', name: 'AWS-104', lat: 26.9124, lon: 75.7873, status: 'critical', health: 62, trust: 18, lastAnomaly: '2026-09-04T10:12:00Z' },
  { id: 'AWS-211', name: 'AWS-211', lat: 28.7041, lon: 77.1025, status: 'degrading', health: 78, trust: 54, lastAnomaly: '2026-09-03T22:40:00Z' },
  { id: 'AWS-057', name: 'AWS-057', lat: 19.076, lon: 72.8777, status: 'healthy', health: 96, trust: 91, lastAnomaly: null },
  { id: 'AWS-330', name: 'AWS-330', lat: 22.5726, lon: 88.3639, status: 'healthy', health: 99, trust: 97, lastAnomaly: null },
]

export const mockSummary = {
  totalStations: mockStations.length,
  healthy: mockStations.filter((s) => s.status === 'healthy').length,
  degrading: mockStations.filter((s) => s.status === 'degrading').length,
  critical: mockStations.filter((s) => s.status === 'critical').length,
  activeAnomalies: 3,
  averageTrust: 65,
}

export const mockAnomalies = [
  {
    id: 'AN-1001',
    stationId: 'AWS-104',
    variable: 'temperature',
    detectedAt: '2026-09-04T10:12:00Z',
    decision: 'sensor_fault',
    faultType: 'spike',
    trustScore: 18,
    confidence: 0.91,
    reading: { value: 55.0, unit: '°C' },
    suggestedCorrection: 31.4,
    evidence: {
      isolation_score: 0.91,
      autoencoder_error: 0.83,
      temporal_deviation: 0.94,
      cross_station_agreement: 0.08,
      cross_sensor_agreement: 0.12,
      persistence: 0.2,
    },
    status: 'pending',
  },
  {
    id: 'AN-1002',
    stationId: 'AWS-211',
    variable: 'humidity',
    detectedAt: '2026-09-03T22:40:00Z',
    decision: 'uncertain',
    faultType: 'drift',
    trustScore: 54,
    confidence: 0.62,
    reading: { value: 12.0, unit: '%' },
    suggestedCorrection: 34.5,
    evidence: {
      isolation_score: 0.55,
      autoencoder_error: 0.48,
      temporal_deviation: 0.61,
      cross_station_agreement: 0.4,
      cross_sensor_agreement: 0.3,
      persistence: 0.7,
    },
    status: 'pending',
  },
]

export const mockMaintenanceQueue = [
  {
    priority: 'HIGH',
    stationId: 'AWS-104',
    health: 62,
    trust: 18,
    trend: 'declining',
    faults30d: 11,
    reason: 'Repeated temperature spikes, low cross-sensor agreement',
  },
  {
    priority: 'MEDIUM',
    stationId: 'AWS-211',
    health: 78,
    trust: 54,
    trend: 'declining',
    faults30d: 4,
    reason: 'Slow humidity drift over 6 days',
  },
]

export const mockDigitalTwin = (stationId) => ({
  stationId,
  health: 62,
  trust: 18,
  trend: 'declining',
  faultHistory: [
    { date: '2026-08-28', type: 'spike', variable: 'temperature' },
    { date: '2026-08-30', type: 'spike', variable: 'temperature' },
    { date: '2026-09-04', type: 'spike', variable: 'temperature' },
  ],
  recentAnomalies: mockAnomalies.filter((a) => a.stationId === stationId),
  maintenancePriority: 'HIGH',
})

export const mockRisks = [
  {
    id: 'RISK-1',
    event: 'Extreme Heat',
    riskLevel: 'HIGH',
    area: 'Delhi',
    confidence: 0.96,
    value: 44,
    unit: '°C',
    validated: true,
    evidence: ['Multiple stations agree', 'Event persisted', 'Sensor reliability verified'],
    affectedStations: ['AWS-104', 'AWS-211'],
    updatedAt: '2026-09-04T11:00:00Z',
  },
  {
    id: 'RISK-2',
    event: 'Heavy Rainfall',
    riskLevel: 'MEDIUM',
    area: 'Mumbai',
    confidence: 0.72,
    value: 68,
    unit: 'mm/hr',
    validated: false,
    evidence: ['Two stations agree', 'Event still building'],
    affectedStations: ['AWS-057'],
    updatedAt: '2026-09-04T09:30:00Z',
  },
]

// Simplified public-facing shape derived from a risk event — deliberately
// drops anomaly model names, raw sensor IDs, Trust Score breakdown, fault
// codes, and any backend/debug info per the public-view rules.
export const mockPublicRisk = (area) => {
  const risk = mockRisks.find((r) => r.area.toLowerCase() === String(area).toLowerCase())
  if (!risk) return null
  return {
    area: risk.area,
    riskLevel: risk.riskLevel,
    headline: `${risk.riskLevel} ${risk.event.toUpperCase()} RISK`,
    value: risk.value,
    unit: risk.unit,
    confidence: risk.confidence,
    explanation: 'Multiple nearby weather stations confirm the condition.',
    guidance:
      risk.event === 'Extreme Heat'
        ? ['Stay hydrated', 'Avoid prolonged outdoor exposure']
        : ['Avoid low-lying and flood-prone areas', 'Keep emergency contacts handy'],
    disclaimer:
      'SkyGuard AI is not an official government warning authority. Check official government advisories for authoritative warnings.',
  }
}

export const mockCascade = (anomalyId) => ({
  anomalyId,
  withoutSkyguard: {
    label: 'FALSE HEATWAVE ALERT',
    description: 'Raw 55°C reading propagates directly into the downstream forecast rule.',
  },
  withSkyguard: {
    label: 'NO FALSE ALERT',
    description: 'SkyGuard flags the reading as a sensor fault and substitutes the corrected value.',
  },
  impactSummary: 'One false public alert prevented.',
  illustrative: true,
})
