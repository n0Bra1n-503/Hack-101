import { useEffect } from 'react'
import { liveSocket } from '../services/websocket.js'

// Subscribe a component to one live event type, e.g.:
//   useLiveEvent('anomaly', (payload) => setAnomalies((a) => [payload, ...a]))
export default function useLiveEvent(eventType, handler) {
  useEffect(() => {
    const unsubscribe = liveSocket.on(eventType, handler)
    return () => unsubscribe()
  }, [eventType, handler])
}
