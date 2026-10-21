import { useEffect, useState } from 'react'

type StreamState = 'connecting' | 'connected' | 'fallback'

export function useWebSocket(url: string | null, onMessage: (data: unknown) => void) {
  const [state, setState] = useState<StreamState>('connecting')
  useEffect(() => {
    if (!url || import.meta.env.VITE_USE_MOCKS === 'true') { setState('fallback'); return }
    let socket: WebSocket | null = null; let retries = 0; let closed = false; let retryTimer = 0
    const connect = () => { if (closed) return; socket = new WebSocket(url); socket.onopen = () => { retries = 0; setState('connected') }; socket.onmessage = (event) => onMessage(JSON.parse(event.data)); socket.onerror = () => socket?.close(); socket.onclose = () => { setState('fallback'); retryTimer = window.setTimeout(connect, Math.min(1000 * 2 ** retries++, 30000)) } }
    connect()
    return () => { closed = true; window.clearTimeout(retryTimer); socket?.close() }
  }, [url, onMessage])
  return state
}
