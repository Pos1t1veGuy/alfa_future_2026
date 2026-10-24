import axios from 'axios'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api/v1', headers: { 'Content-Type': 'application/json' } })
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('alfa-access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config
  if (error.response?.status === 401 && original && !original._retry) {
    original._retry = true
    const refresh = localStorage.getItem('alfa-refresh')
    if (refresh) {
      try {
        const { data } = await axios.post(`${api.defaults.baseURL}/auth/refresh/`, { refresh })
        localStorage.setItem('alfa-access', data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        localStorage.removeItem('alfa-access'); localStorage.removeItem('alfa-refresh'); localStorage.removeItem('alfa-user')
      }
    }
  }
  return Promise.reject(error)
})
export function errorMessage(error: any): string {
  const data = error?.response?.data
  if (typeof data?.message === 'string') return data.message
  if (typeof data?.detail === 'string') return data.detail
  if (data && typeof data === 'object') {
    const first = Object.values(data).flat().find((v) => typeof v === 'string')
    if (first) return String(first)
  }
  if (!error?.response) return 'Не удалось связаться с сервером. Проверьте, что backend запущен.'
  return 'Не удалось выполнить действие. Попробуйте ещё раз.'
}
