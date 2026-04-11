import { createContext, useContext, useState, useEffect } from 'react'
import { supabase, auth as supabaseAuth, isSupabaseConfigured } from '../utils/supabase'

const AuthContext = createContext()
const DEMO_SESSION_KEY = 'radar_demo_session'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const checkSession = async () => {
      try {
        const rawDemoSession = localStorage.getItem(DEMO_SESSION_KEY)
        if (rawDemoSession) {
          setUser(JSON.parse(rawDemoSession))
          return
        }

        const { session } = await supabaseAuth.getSession()
        setUser(session?.user || null)
      } catch (error) {
        console.error('Error checking session:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkSession()

    if (!isSupabaseConfigured || !supabase) {
      return () => {}
    }

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user || null)
      }
    )

    return () => subscription?.unsubscribe()
  }, [])

  const signUp = async (email, password) => {
    return await supabaseAuth.signUp(email, password)
  }

  const signIn = async (email, password) => {
    const result = await supabaseAuth.signIn(email, password)
    if (result?.data?.user) {
      localStorage.removeItem(DEMO_SESSION_KEY)
      setUser(result.data.user)
    }
    return result
  }

  const signInDemo = async () => {
    const demoUser = {
      id: 'demo-user',
      email: 'demo@radar.com',
      is_demo: true,
    }
    localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(demoUser))
    setUser(demoUser)
    return { data: { user: demoUser }, error: null }
  }

  const signOut = async () => {
    localStorage.removeItem(DEMO_SESSION_KEY)
    setUser(null)

    if (!isSupabaseConfigured) {
      return { error: null }
    }

    return await supabaseAuth.signOut()
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
