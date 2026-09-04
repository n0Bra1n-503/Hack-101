import useConnectionState from '../hooks/useConnectionState.js'
import { CONNECTION_STATES } from '../services/websocket.js'

const DOT_COLOR = {
  [CONNECTION_STATES.LIVE]: 'bg-healthy',
  [CONNECTION_STATES.RECONNECTING]: 'bg-degrading animate-pulse',
  [CONNECTION_STATES.OFFLINE]: 'bg-critical',
  [CONNECTION_STATES.REPLAY]: 'bg-accent',
}

export default function ConnectionIndicator() {
  const state = useConnectionState()
  return (
    <div className="flex items-center gap-2 text-xs text-inkMuted shrink-0">
      <span className={`h-2 w-2 rounded-full ${DOT_COLOR[state] || 'bg-inkMuted'}`} />
      {state}
    </div>
  )
}
