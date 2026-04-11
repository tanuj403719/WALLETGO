import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../utils/api'

const AuthContext = createContext()
const SESSION_KEY = 'radar_session'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Restore session from localStorage on mount
    const checkSession = async () => {
      try {
        const saved = localStorage.getItem(SESSION_KEY)
        if (saved) {
          setUser(JSON.parse(saved))
        }
      } catch (error) {
        console.error('Error restoring session:', error)
        localStorage.removeItem(SESSION_KEY)
      } finally {
        setIsLoading(false)
      }
    }

    checkSession()
  }, [])

  const _persistUser = (userData) => {
    setUser(userData)
    localStorage.setItem(SESSION_KEY, JSON.stringify(userData))
  }

  const signUp = async (email, password) => {
    try {
      const response = await authAPI.signUp(email, password)
      const payload = response.data
      const userData = {
        id: payload.user?.id || email,
        email: payload.user?.email || email,
        is_demo: false,
      }
      _persistUser(userData)
      return { data: { user: userData }, error: null }
    } catch (error) {
      return { data: null, error: error.response?.data || error }
    }
  }

  const signIn = async (email, password) => {
    try {
      const response = await authAPI.signIn(email, password)
      const payload = response.data
      const userData = {
        id: payload.user?.id || email,
        email: payload.user?.email || email,
        is_demo: payload.user?.demo || false,
      }

      // Store the access token for future API requests
      if (payload.access_token) {
        localStorage.setItem('auth_token', payload.access_token)
      }

      _persistUser(userData)
      return { data: { user: userData }, error: null }
    } catch (error) {
      return { data: null, error: error.response?.data || error }
    }
  }

  const signInDemo = async () => {
    const demoUser = {
      id: 'demo-user',
      email: 'demo@radar.com',
      is_demo: true,
    }
    _persistUser(demoUser)
    return { data: { user: demoUser }, error: null }
  }

  const signOut = async () => {
    localStorage.removeItem(SESSION_KEY)
    localStorage.removeItem('auth_token')
    setUser(null)
    return { error: null }
  }

  const isAuthenticated = Boolean(user)

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated, signUp, signIn, signInDemo, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
