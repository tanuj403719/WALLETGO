import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FiTarget, FiTrendingDown, FiCheckCircle, FiAlertTriangle,
  FiLoader, FiCalendar, FiDollarSign, FiArrowRight, FiZap,
  FiPauseCircle, FiScissors, FiRefreshCw,
} from 'react-icons/fi'
import toast from 'react-hot-toast'
import { forecastAPI } from '../utils/api'

function getMinDate() {
  return new Date().toISOString().slice(0, 10)
}

function fmt(value) {
  return `$${Math.round(Number(value) || 0).toLocaleString()}`
}

const STRATEGY_CONFIG = {
  pause: {
    label: 'Pause',
    Icon: FiPauseCircle,
    badge: 'bg-rose-500/15 border-rose-500/30 text-rose-300',
    bar: 'bg-rose-400',
  },
  trim: {
    label: 'Trim',
    Icon: FiScissors,
    badge: 'bg-amber-500/15 border-amber-500/30 text-amber-300',
    bar: 'bg-amber-400',
  },
  swap: {
    label: 'Swap',
    Icon: FiRefreshCw,
    badge: 'bg-violet-500/15 border-violet-500/30 text-violet-300',
    bar: 'bg-violet-400',
  },
}

function strategyConfig(raw) {
  const key = (raw || 'trim').toString().trim().toLowerCase()
  return STRATEGY_CONFIG[key] || STRATEGY_CONFIG.trim
}

const CATEGORY_COLORS = {
  food: { bg: 'bg-orange-500/15', border: 'border-orange-500/30', dot: 'bg-orange-400', text: 'text-orange-400' },
  dining: { bg: 'bg-orange-500/15', border: 'border-orange-500/30', dot: 'bg-orange-400', text: 'text-orange-400' },
  shopping: { bg: 'bg-blue-500/15', border: 'border-blue-500/30', dot: 'bg-blue-400', text: 'text-blue-400' },
  entertainment: { bg: 'bg-purple-500/15', border: 'border-purple-500/30', dot: 'bg-purple-400', text: 'text-purple-400' },
  subscriptions: { bg: 'bg-pink-500/15', border: 'border-pink-500/30', dot: 'bg-pink-400', text: 'text-pink-400' },
  travel: { bg: 'bg-sky-500/15', border: 'border-sky-500/30', dot: 'bg-sky-400', text: 'text-sky-400' },
  transport: { bg: 'bg-cyan-500/15', border: 'border-cyan-500/30', dot: 'bg-cyan-400', text: 'text-cyan-400' },
  general: { bg: 'bg-slate-500/15', border: 'border-slate-500/30', dot: 'bg-slate-400', text: 'text-slate-400' },
}

function categoryStyle(cat) {
  return CATEGORY_COLORS[cat?.toLowerCase()] || CATEGORY_COLORS.general
}

function GoalProgressRing({ delta, target, projected }) {
  const pct = target > 0 ? Math.min(100, Math.round((projected / target) * 100)) : 0
  const r = 54
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - pct / 100)
  const isAhead = delta <= 0

  return (
    <div className="relative flex items-center justify-center" style={{ width: 140, height: 140 }}>
      <svg width="140" height="140" viewBox="0 0 140 140" className="-rotate-90">
        <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(148,163,184,0.12)" strokeWidth="10" />
        <motion.circle
          cx="70" cy="70" r={r}
          fill="none"
          stroke={isAhead ? '#10b981' : '#14b8a6'}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut', delay: 0.2 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <motion.span
          initial={{ opacity: 0, scale: 0.7 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.4 }}
          className="text-3xl font-black text-slate-100"
        >
          {pct}%
        </motion.span>
        <span className="text-xs text-slate-400 mt-0.5">funded</span>
      </div>
    </div>
  )
}

function CutCard({ cut, index, totalRequired }) {
  const style = categoryStyle(cut.category)
  const strat = strategyConfig(cut.strategy_type)
  const pct = Math.min(100, Math.round(cut.cut_percentage || 0))
  const impact = totalRequired > 0 ? Math.min(100, Math.round((cut.monthly_savings / totalRequired) * 100)) : 0

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.35 }}
      className={`relative overflow-hidden rounded-2xl border p-4 ${style.bg} ${style.border}`}
    >
      {/* header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${style.dot}`} />
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className={`text-sm font-bold capitalize ${style.text}`}>{cut.category}</p>
              {/* strategy badge */}
              <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${strat.badge}`}>
                <strat.Icon size={9} />
                {strat.label}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-slate-400 leading-relaxed">{cut.action}</p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-base font-black text-emerald-400">+{fmt(cut.monthly_savings)}</p>
          <p className="text-xs text-slate-500">/month</p>
        </div>
      </div>

      {/* progress row */}
      <div className="mt-3 space-y-1.5">
        <div className="flex justify-between text-xs text-slate-500">
          <span>{fmt(cut.current_monthly_spend)} now</span>
          <span className={`font-semibold ${style.text}`}>
            {pct}% cut → {fmt(cut.recommended_monthly_spend)}
          </span>
        </div>
        <div className="h-1 w-full rounded-full bg-white/10">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ delay: index * 0.08 + 0.25, duration: 0.7, ease: 'easeOut' }}
            className={`h-1 rounded-full ${strat.bar}`}
          />
        </div>
        <p className="text-right text-xs text-slate-500">covers {impact}% of monthly target</p>
      </div>
    </motion.div>
  )
}

export default function GoalForecaster({ ephemeralTransactions = null }) {
  const [targetAmount, setTargetAmount] = useState('')
  const [targetDate, setTargetDate] = useState('')
  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const goal = result?.goal
  const cuts = result?.suggested_cuts || []
  const totalSavings = cuts.reduce((s, c) => s + (c.monthly_savings || 0), 0)
  const coveragePct = goal?.required_monthly_savings > 0
    ? Math.min(100, Math.round((totalSavings / goal.required_monthly_savings) * 100))
    : 100

  async function handleSubmit(e) {
    e.preventDefault()
    const amount = parseFloat(targetAmount)
    if (!amount || amount <= 0) { toast.error('Enter a valid target amount'); return }
    if (!targetDate || targetDate < getMinDate()) { toast.error('Target date must be today or in the future'); return }

    setLoading(true)
    setResult(null)
    try {
      const res = await forecastAPI.goal(amount, targetDate, language, ephemeralTransactions)
      setResult(res.data)
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Failed to generate goal forecast'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const LANGS = [
    { code: 'en', label: 'English' },
    { code: 'hinglish', label: 'Hinglish' },
    { code: 'hi', label: 'Hindi' },
  ]

  return (
    <div className="space-y-5">

      {/* ── Form card ─────────────────────────────────────────────── */}
      <div className="glass-card overflow-hidden">
        {/* gradient banner */}
        <div
          className="px-6 py-5"
          style={{ background: 'linear-gradient(135deg, rgba(15,118,110,0.22) 0%, rgba(14,165,233,0.14) 100%)' }}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{ background: 'linear-gradient(135deg, #0f766e, #0ea5e9)' }}>
              <FiTarget size={18} color="#fff" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Goal-Based Forecaster</h2>
              <p className="text-xs text-slate-400">Set a savings target and get an AI-powered spending plan</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">

              {/* Amount input */}
              <div className="group">
                <label className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <FiDollarSign size={12} /> Target Balance
                </label>
                <div className="relative">
                  <span className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-lg font-bold text-teal-400">$</span>
                  <input
                    type="number" min="1" step="any"
                    value={targetAmount}
                    onChange={(e) => setTargetAmount(e.target.value)}
                    placeholder="10,000"
                    className="w-full rounded-xl border border-slate-700/60 bg-slate-800/40 py-3 pl-8 pr-4 text-lg font-bold text-slate-100 placeholder-slate-600 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
                    required
                  />
                </div>
              </div>

              {/* Date input */}
              <div>
                <label className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <FiCalendar size={12} /> Target Date
                </label>
                <input
                  type="date"
                  min={getMinDate()}
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="w-full rounded-xl border border-slate-700/60 bg-slate-800/40 px-4 py-3 text-sm font-medium text-slate-100 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 [color-scheme:dark]"
                  required
                />
              </div>
            </div>

            {/* Language selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 mr-1">Language:</span>
              {LANGS.map(({ code, label }) => (
                <button key={code} type="button" onClick={() => setLanguage(code)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold transition-all ${
                    language === code
                      ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/25'
                      : 'bg-slate-800/60 text-slate-400 hover:bg-slate-700/60 hover:text-slate-200'
                  }`}>
                  {label}
                </button>
              ))}
            </div>

            {/* Submit */}
            <button type="submit" disabled={loading}
              className="primary-cta flex w-full items-center justify-center gap-2.5 px-6 py-3.5 text-sm font-bold disabled:opacity-50"
            >
              {loading ? (
                <><FiLoader className="animate-spin" size={16} /> Analysing your finances...</>
              ) : (
                <><FiZap size={16} /> Analyse Goal <FiArrowRight size={14} /></>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* ── Results ───────────────────────────────────────────────── */}
      <AnimatePresence>
        {result && goal && (
          <motion.div key="results"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="space-y-5"
          >

            {/* Hero summary card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
              className="glass-card overflow-hidden"
            >
              {/* status banner */}
              <div className={`px-6 py-3 flex items-center gap-2.5 text-sm font-semibold ${
                goal.is_achievable
                  ? 'bg-emerald-500/10 text-emerald-400 border-b border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-b border-amber-500/20'
              }`}>
                {goal.is_achievable
                  ? <><FiCheckCircle size={16} /> Goal is achievable with the recommended changes</>
                  : <><FiAlertTriangle size={16} /> This goal is ambitious — here&apos;s an optimised plan</>}
              </div>

              <div className="p-6">
                <div className="flex flex-col sm:flex-row items-center gap-6">

                  {/* Ring */}
                  <div className="shrink-0">
                    <GoalProgressRing
                      delta={goal.delta}
                      target={goal.target_amount}
                      projected={goal.current_projected_balance}
                    />
                    <p className="mt-2 text-center text-xs text-slate-500">current trajectory</p>
                  </div>

                  {/* Stats grid */}
                  <div className="grid w-full grid-cols-2 gap-3">
                    <HeroStat
                      label="Target" icon="🎯"
                      value={fmt(goal.target_amount)}
                      sub={`by ${goal.target_date}`}
                      accent="teal"
                    />
                    <HeroStat
                      label="Projected (no changes)" icon="📈"
                      value={fmt(goal.current_projected_balance)}
                      sub={`in ${goal.days_remaining} days`}
                      accent="slate"
                    />
                    <HeroStat
                      label="Savings Gap" icon="⚡"
                      value={fmt(goal.delta)}
                      sub={goal.delta <= 0 ? 'already on track!' : 'shortfall to cover'}
                      accent={goal.delta <= 0 ? 'green' : 'rose'}
                    />
                    <HeroStat
                      label="Monthly Savings Needed" icon="📅"
                      value={fmt(goal.required_monthly_savings) + '/mo'}
                      sub={`${fmt(goal.required_daily_savings)}/day`}
                      accent="violet"
                    />
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Already on track */}
            {cuts.length === 0 && goal.delta <= 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
                className="glass-card p-8 text-center"
              >
                <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/15">
                  <FiCheckCircle size={32} className="text-emerald-400" />
                </div>
                <p className="text-xl font-black text-slate-100">You&apos;re already on track!</p>
                <p className="mt-1 text-sm text-slate-400">
                  Your projected balance of {fmt(goal.current_projected_balance)} already meets the {fmt(goal.target_amount)} target. Keep it up.
                </p>
              </motion.div>
            )}

            {/* Spending cuts */}
            {cuts.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, duration: 0.4 }}
                className="glass-card p-6"
              >
                {/* Header */}
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <FiTrendingDown className="text-rose-400" size={18} />
                      <h3 className="font-bold text-slate-100">AI-Recommended Spending Cuts</h3>
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {Object.keys(result?.goal?.category_spending || {}).length > 0
                        ? 'Gemini analysed your spending history to find the highest-impact cuts'
                        : 'No transaction history found — suggestions based on typical spending patterns'}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-lg font-black text-emerald-400">{fmt(totalSavings)}<span className="text-xs font-normal text-slate-500">/mo</span></p>
                    <p className="text-xs text-slate-500">total recoverable</p>
                  </div>
                </div>

                {/* Coverage bar */}
                <div className="mb-5 rounded-xl bg-slate-800/40 p-4 border border-slate-700/40">
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span>Plan coverage</span>
                    <span className={coveragePct >= 90 ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
                      {coveragePct}% of {fmt(goal.required_monthly_savings)}/mo goal
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-700/60">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${coveragePct}%` }}
                      transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
                      className={`h-2 rounded-full ${coveragePct >= 90 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                    />
                  </div>
                </div>

                {/* Cut cards — 2-col on larger screens */}
                <div className="grid gap-3 sm:grid-cols-2">
                  {cuts.map((cut, i) => (
                    <CutCard key={cut.category + i} cut={cut} index={i} totalRequired={goal.required_monthly_savings} />
                  ))}
                </div>

                {/* Gap warning */}
                {totalSavings < goal.required_monthly_savings * 0.9 && (
                  <motion.div
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
                    className="mt-4 flex gap-3 rounded-xl border border-amber-500/25 bg-amber-500/8 px-4 py-3"
                  >
                    <FiAlertTriangle className="shrink-0 mt-0.5 text-amber-400" size={16} />
                    <p className="text-xs text-amber-300/80">
                      These cuts cover {fmt(totalSavings)}/mo of the {fmt(goal.required_monthly_savings)}/mo needed.
                      Consider extending your target date or finding additional income sources to bridge the remaining {fmt(goal.required_monthly_savings - totalSavings)}/mo gap.
                    </p>
                  </motion.div>
                )}
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function HeroStat({ label, value, sub, accent, icon }) {
  const accents = {
    teal:   'border-teal-500/25 bg-teal-500/8',
    slate:  'border-slate-500/25 bg-slate-500/8',
    rose:   'border-rose-500/25 bg-rose-500/8',
    green:  'border-emerald-500/25 bg-emerald-500/8',
    violet: 'border-violet-500/25 bg-violet-500/8',
  }
  const valueColors = {
    teal: 'text-teal-300', slate: 'text-slate-200', rose: 'text-rose-300',
    green: 'text-emerald-300', violet: 'text-violet-300',
  }
  return (
    <div className={`rounded-xl border p-3.5 ${accents[accent] || accents.slate}`}>
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-sm">{icon}</span>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-black leading-tight ${valueColors[accent] || 'text-slate-200'}`}>{value}</p>
      <p className="text-xs text-slate-600 mt-0.5">{sub}</p>
    </div>
  )
}
