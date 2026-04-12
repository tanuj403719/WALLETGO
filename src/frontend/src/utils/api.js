import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Forecast API
export const forecastAPI = {
  generate: (days = 42) => api.post('/api/forecast/generate', { days }),
  getCurrent: () => api.get('/api/forecast/current'),
  getHistory: (limit = 10) => api.get(`/api/forecast/history?limit=${limit}`),
}

// Scenario API
export const scenarioAPI = {
  analyze: (description, language = 'en') =>
    api.post('/api/scenarios/analyze', { description, language }),
  getSuggestions: (language = 'en') =>
    api.get(`/api/scenarios/suggestions?language=${language}`),
}

// Transaction API
export const transactionAPI = {
  list: (limit = 100, offset = 0) =>
    api.get(`/api/transactions/list?limit=${limit}&offset=${offset}`),
  getRecurring: () => api.get('/api/transactions/recurring'),
  getStats: () => api.get('/api/transactions/stats'),
  uploadStatement: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/transactions/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// Auth API
export const authAPI = {
  signUp: (email, password) => api.post('/api/auth/signup', { email, password }),
  signIn: (email, password) => api.post('/api/auth/signin', { email, password }),
  getMe: () => api.get('/api/auth/me'),
  logout: () => api.post('/api/auth/logout'),
}

export default api
