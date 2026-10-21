import { useEffect } from 'react'

export function usePolling(callback: () => void, enabled: boolean, interval = 30000) {
  useEffect(() => {
    if (!enabled) return
    const timer = window.setInterval(callback, interval)
    return () => window.clearInterval(timer)
  }, [callback, enabled, interval])
}
