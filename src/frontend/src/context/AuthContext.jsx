import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../utils/api'
import { auth as supabaseAuth, isSupabaseConfigured } from '../utils/supabase'

const AuthContext = createContext()
const SESSION_KEY = 'radar_session'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Prefer Supabase session restore when configured, with local fallback.
    const checkSession = async () => {
      try {
        if (isSupabaseConfigured) {
          const { session, error } = await supabaseAuth.getSession()
          if (error) throw error

          if (session?.access_token && session?.user) {
            localStorage.setItem('auth_token', session.access_token)
            const userData = {
              id: session.user.id,
              email: session.user.email || '',
              is_demo: false,
            }
            _persistUser(userData)
            return
          }
        }

        const saved = localStorage.getItem(SESSION_KEY)
        if (saved) {
          setUser(JSON.parse(saved))
        }
      } catch (error) {
        console.error('Error restoring session:', error)
        localStorage.removeItem(SESSION_KEY)
        localStorage.removeItem('auth_token')
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
      if (isSupabaseConfigured) {
        const { data, error } = await supabaseAuth.signUp(email, password)
        if (error) return { data: null, error }

        const session = data?.session
        const supabaseUser = data?.user

        // Some Supabase setups require email confirmation before a session is issued.
        if (!session?.access_token || !supabaseUser) {
          return {
            data: null,
            error: { message: 'Account created. Please verify your email, then sign in.' },
          }
        }

        localStorage.setItem('auth_token', session.access_token)
        const userData = {
          id: supabaseUser.id,
          email: supabaseUser.email || email,
          is_demo: false,
        }
        _persistUser(userData)
        return { data: { user: userData }, error: null }
      }

      const response = await authAPI.signUp(email, password)
      const payload = response.data
      const userData = {
        id: payload.user?.id || email,
        email: payload.user?.email || email,
        is_demo: false,
      }
      if (payload.access_token) {
        localStorage.setItem('auth_token', payload.access_token)
      }
      _persistUser(userData)
      return { data: { user: userData }, error: null }
    } catch (error) {
      return { data: null, error: error.response?.data || error }
    }
  }

  const signIn = async (email, password) => {
    try {
      if (isSupabaseConfigured) {
        const { data, error } = await supabaseAuth.signIn(email, password)
        if (error) return { data: null, error }

        const session = data?.session
        const supabaseUser = data?.user
        if (!session?.access_token || !supabaseUser) {
          return {
            data: null,
            error: { message: 'Supabase sign in succeeded but no session was returned.' },
          }
        }

        localStorage.setItem('auth_token', session.access_token)
        const userData = {
          id: supabaseUser.id,
          email: supabaseUser.email || email,
          is_demo: false,
        }
        _persistUser(userData)
        return { data: { user: userData }, error: null }
      }

      const response = await authAPI.signIn(email, password)
      const payload = response.data
      const userData = {
        id: payload.user?.id || email,
        email: payload.user?.email || email,
        is_demo: payload.user?.demo || false,
      }

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
    localStorage.setItem('auth_token', 'demo-token')
    _persistUser(demoUser)
    return { data: { user: demoUser }, error: null }
  }

  const signOut = async () => {
    if (isSupabaseConfigured) {
      await supabaseAuth.signOut()
    }
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
