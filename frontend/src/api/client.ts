import axios from 'axios'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api/v1', headers: { 'Content-Type': 'application/json' } })
api.interceptors.request.use((config) => { const token = localStorage.getItem('alfa-access'); if (token) config.headers.Authorization = `Bearer ${token}`; return config })
api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config
  if (error.response?.status === 401 && !original?._retry) {
    original._retry = true
    const refresh = localStorage.getItem('alfa-refresh')
    if (refresh) try { const { data } = await axios.post(`${api.defaults.baseURL}/auth/refresh/`, { refresh }); localStorage.setItem('alfa-access', data.access); original.headers.Authorization = `Bearer ${data.access}`; return api(original) } catch { localStorage.removeItem('alfa-access'); localStorage.removeItem('alfa-refresh') }
  }
  return Promise.reject(error)
})
