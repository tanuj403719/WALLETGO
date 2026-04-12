import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

function getErrorMessage(error) {
  if (!error) return 'Authentication failed'
  if (typeof error === 'string') return error
  return error.message || error.error_description || 'Authentication failed'
}

function shouldFallbackToSignIn(errorMessage) {
  const text = String(errorMessage || '').toLowerCase()
  return (
    text.includes('email rate limit exceeded') ||
    text.includes('already registered') ||
    text.includes('already exists') ||
    text.includes('user already registered')
  )
}

function isEmailNotConfirmed(errorMessage) {
  return String(errorMessage || '').toLowerCase().includes('email not confirmed')
}

export default function SignInPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState('signin')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { signIn, signUp, signInDemo } = useAuth()

  useEffect(() => {
    const requestedMode = searchParams.get('mode')
    const demo = searchParams.get('demo')
    if (requestedMode === 'signup') {
      setMode('signup')
    }
    if (demo === '1') {
      setEmail('demo@radar.com')
      setPassword('demo123')
      setMode('signin')
      toast('Demo credentials pre-filled', { icon: '🎮' })
    }
  }, [searchParams])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      if (email === 'demo@radar.com' && password === 'demo123') {
        await signInDemo()
        toast.success('Demo account loaded', { id: 'auth-status' })
        navigate('/dashboard')
        return
      }

      if (mode === 'signup') {
        const { error } = await signUp(email, password)
        if (error) {
          const message = getErrorMessage(error)
          if (shouldFallbackToSignIn(message)) {
            const signInAttempt = await signIn(email, password)
            if (!signInAttempt.error) {
              setMode('signin')
              toast.success('Account already exists. Signed in successfully.', { id: 'auth-status' })
              navigate('/dashboard')
              return
            }
            if (isEmailNotConfirmed(getErrorMessage(signInAttempt.error))) {
              throw signInAttempt.error
            }
          }
          throw error
        }
        toast.success('Account created. Upload your first statement to unlock stats.', { id: 'auth-status' })
        navigate('/dashboard')
        return
      }

      const { error } = await signIn(email, password)
      if (error) throw error
      toast.success('Signed in successfully', { id: 'auth-status' })
      navigate('/dashboard')
    } catch (error) {
      const message = getErrorMessage(error)
      if (message.toLowerCase().includes('email rate limit exceeded')) {
        toast.error('Too many signup emails. Please use Sign in or try again in a few minutes.', {
          id: 'auth-error',
        })
      } else if (isEmailNotConfirmed(message)) {
        toast.error('Email not confirmed. Check your inbox and click the verification link, then sign in.', {
          id: 'auth-error',
        })
      } else {
        toast.error(message, { id: 'auth-error' })
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#03141d] text-white relative overflow-hidden">
      <div className="absolute -top-24 -left-24 w-80 h-80 rounded-full bg-cyan-400/20 blur-3xl" />
      <div className="absolute -bottom-28 -right-20 w-96 h-96 rounded-full bg-yellow-300/20 blur-3xl" />

      <div className="max-w-6xl mx-auto px-4 py-10 md:py-16 grid lg:grid-cols-2 gap-8 items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="hidden lg:block"
        >
          <p className="uppercase text-xs tracking-[0.25em] text-cyan-200 mb-4">Personalized Liquidity Radar</p>
          <h1 className="font-display text-6xl leading-[0.94] mb-5">
            Make Better
            <span className="block text-yellow-300">Money Moves</span>
          </h1>
          <p className="text-white/80 text-lg max-w-md mb-8">
            Forecast the next 6 weeks before you spend. See risks early, simulate decisions, and stay in the green.
          </p>

          <div className="space-y-3 text-sm text-white/85">
            <p className="rounded-xl border border-white/15 bg-white/5 px-4 py-3">6-week forecast with confidence range</p>
            <p className="rounded-xl border border-white/15 bg-white/5 px-4 py-3">What-if scenarios in English, Hinglish, Hindi</p>
            <p className="rounded-xl border border-white/15 bg-white/5 px-4 py-3">Early warnings for overdraft cluster days</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md mx-auto"
        >
          <div className="rounded-3xl border border-white/20 bg-slate-900/70 text-white backdrop-blur-sm shadow-2xl p-8">
            <div className="text-center mb-7">
              <div className="text-4xl mb-3">📡</div>
              <h1 className="text-3xl font-bold text-white">
                {mode === 'signin' ? 'Welcome Back' : 'Create Account'}
              </h1>
              <p className="text-slate-300 mt-2">
                {mode === 'signin' ? 'Sign in to continue forecasting' : 'Start your Radar account'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-slate-200 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-4 py-3 border border-white/20 bg-slate-950/50 text-white placeholder:text-slate-400 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-200 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 border border-white/20 bg-slate-950/50 text-white placeholder:text-slate-400 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-xl font-semibold text-lg bg-[#042132] text-white hover:bg-[#073047] transition disabled:opacity-60"
              >
                {isLoading ? 'Working...' : mode === 'signin' ? 'Sign In' : 'Create Account'}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-slate-300">
                {mode === 'signin' ? 'New user?' : 'Already have an account?'}{' '}
                <button
                  type="button"
                  onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
                  className="text-cyan-300 font-semibold hover:underline"
                >
                  {mode === 'signin' ? 'Create account' : 'Sign in'}
                </button>
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
