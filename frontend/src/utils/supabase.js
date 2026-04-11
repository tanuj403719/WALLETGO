import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey)

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase environment variables are missing. Auth flows will be disabled until VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set.')
}

export const supabase = isSupabaseConfigured ? createClient(supabaseUrl, supabaseAnonKey) : null

const missingClientError = new Error('Supabase is not configured')

// Auth functions
export const auth = {
  signUp: async (email, password) => {
    if (!supabase) return { data: null, error: missingClientError }
    const { data, error } = await supabase.auth.signUp({ email, password })
    return { data, error }
  },
  
  signIn: async (email, password) => {
    if (!supabase) return { data: null, error: missingClientError }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    return { data, error }
  },
  
  signOut: async () => {
    if (!supabase) return { error: missingClientError }
    const { error } = await supabase.auth.signOut()
    return { error }
  },
  
  getSession: async () => {
    if (!supabase) return { session: null, error: missingClientError }
    const { data, error } = await supabase.auth.getSession()
    return { session: data.session, error }
  },
}

// Database functions
export const db = {
  getForecast: async (userId) => {
    if (!supabase) return { data: null, error: missingClientError }
    const { data, error } = await supabase
      .from('forecasts')
      .select('*')
      .eq('user_id', userId)
      .single()
    return { data, error }
  },
  
  saveForecast: async (userId, forecastData) => {
    if (!supabase) return { data: null, error: missingClientError }
    const { data, error } = await supabase
      .from('forecasts')
      .upsert({ user_id: userId, forecast_data: forecastData })
    return { data, error }
  },
}
