// WebSocket client for /ws/live. Wrapped as a small pub/sub so multiple
// components (feed, map, digital twin, maintenance queue) can subscribe to
// the same live connection without opening duplicate sockets.

const WS_URL = import.meta.env.VITE_WS_URL || `${location.origin.replace('http', 'ws')}/ws/live`

export const CONNECTION_STATES = {
  LIVE: 'LIVE',
  RECONNECTING: 'RECONNECTING',
  OFFLINE: 'OFFLINE',
  REPLAY: 'REPLAY MODE',
}

class LiveSocket {
  constructor() {
    this.socket = null
    this.listeners = new Map() // eventType -> Set<fn>
    this.stateListeners = new Set()
    this.state = CONNECTION_STATES.OFFLINE
    this.reconnectAttempts = 0
    this.manualClose = false
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return
    }
    this.manualClose = false
    this._setState(this.reconnectAttempts > 0 ? CONNECTION_STATES.RECONNECTING : CONNECTION_STATES.LIVE)

    try {
      this.socket = new WebSocket(WS_URL)
    } catch (err) {
      this._setState(CONNECTION_STATES.OFFLINE)
      this._scheduleReconnect()
      return
    }

    this.socket.onopen = () => {
      this.reconnectAttempts = 0
      this._setState(CONNECTION_STATES.LIVE)
    }

    this.socket.onmessage = (event) => {
      let msg
      try {
        msg = JSON.parse(event.data)
      } catch {
        return
      }
      const { type, payload } = msg
      const handlers = this.listeners.get(type)
      if (handlers) handlers.forEach((fn) => fn(payload))
    }

    this.socket.onclose = () => {
      if (this.manualClose) {
        this._setState(CONNECTION_STATES.OFFLINE)
        return
      }
      this._setState(CONNECTION_STATES.OFFLINE)
      this._scheduleReconnect()
    }

    this.socket.onerror = () => {
      this.socket?.close()
    }
  }

  _scheduleReconnect() {
    this.reconnectAttempts += 1
    const backoff = Math.min(1000 * 2 ** this.reconnectAttempts, 15000)
    this._setState(CONNECTION_STATES.RECONNECTING)
    setTimeout(() => this.connect(), backoff)
  }

  disconnect() {
    this.manualClose = true
    this.socket?.close()
  }

  _setState(state) {
    this.state = state
    this.stateListeners.forEach((fn) => fn(state))
  }

  onStateChange(fn) {
    this.stateListeners.add(fn)
    fn(this.state)
    return () => this.stateListeners.delete(fn)
  }

  // event types: reading | anomaly | trust_update | digital_twin_update |
  // maintenance_update | cascade_ready
  on(eventType, fn) {
    if (!this.listeners.has(eventType)) this.listeners.set(eventType, new Set())
    this.listeners.get(eventType).add(fn)
    return () => this.listeners.get(eventType)?.delete(fn)
  }
}

export const liveSocket = new LiveSocket()
