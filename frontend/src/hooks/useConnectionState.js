import { useEffect, useState } from 'react'
import { liveSocket, CONNECTION_STATES } from '../services/websocket.js'

export default function useConnectionState() {
  const [state, setState] = useState(CONNECTION_STATES.OFFLINE)

  useEffect(() => {
    liveSocket.connect()
    const unsubscribe = liveSocket.onStateChange(setState)
    return () => unsubscribe()
  }, [])

  return state
}
