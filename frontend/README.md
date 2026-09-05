# SkyGuard AI — Frontend

## Setup
```bash
cd frontend
npm install
npm run dev
```
Open the printed localhost URL.

## Mocks vs real backend
The app runs entirely on mock data by default (`VITE_USE_MOCKS=true`), so you
can build every page before Mitali's backend exists.

Once `/api/*` and `/ws/live` are live:
1. Copy `.env.example` to `.env.local`.
2. Set `VITE_USE_MOCKS=false`.
3. Set `VITE_API_BASE_URL` / `VITE_WS_URL` if not proxying through Vite.

No page code should need to change — `services/api.js` and
`services/websocket.js` are the only files that know about mocks vs. real
endpoints.

## Structure
```
src/
├── components/   reusable UI: TrustScore, StatusBadge, MetricCard, etc.
├── pages/        CommandCenter, StationMap, Investigation, DigitalTwin,
│                 Maintenance, CascadeSimulator
├── hooks/        useConnectionState, useLiveEvent
├── services/      api.js (REST), websocket.js (live socket), mockData.js
├── utils/
└── types/
```

## Notes
- Never compute the Trust Score in the frontend — always render what the
  backend returns.
- Connection states to always surface: `LIVE / RECONNECTING / OFFLINE /
  REPLAY MODE` (see `ConnectionIndicator`).
- Cascade view must label the downstream effect as illustrative, not the
  real IMD model.
