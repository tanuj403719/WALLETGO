import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  LineChart,
  Line,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  FiActivity,
  FiChevronLeft,
  FiChevronRight,
  FiGrid,
  FiLogOut,
  FiMenu,
  FiSettings,
  FiTarget,
  FiTrendingUp,
  FiShield,
  FiFlag,
} from 'react-icons/fi'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { useForecast } from '../context/ForecastContext'
import StatementUploader from '../components/StatementUploader'
import GoalForecaster from '../components/GoalForecaster'
import { transactionAPI } from '../utils/api'

const DEFAULT_FORECAST = [
  { date: '1 May', rawDate: '2024-05-01', balance: 3500, low: 3200, high: 3800, baseline: 3550 },
  { date: '8 May', rawDate: '2024-05-08', balance: 3200, low: 2900, high: 3600, baseline: 3480 },
  { date: '15 May', rawDate: '2024-05-15', balance: 4800, low: 4400, high: 5200, baseline: 3400 },
  { date: '22 May', rawDate: '2024-05-22', balance: 4200, low: 3800, high: 4700, baseline: 3320 },
  { date: '29 May', rawDate: '2024-05-29', balance: 3900, low: 3400, high: 4500, baseline: 3250 },
  { date: '5 Jun', rawDate: '2024-06-05', balance: 4500, low: 4000, high: 5100, baseline: 3180 },
  { date: '12 Jun', rawDate: '2024-06-12', balance: 4100, low: 3600, high: 4700, baseline: 3100 },
]

const LANGUAGE_TEXTS = {
  en: { placeholder: 'What happens if I...' },
  hi: { placeholder: 'यदि मैं...' },
  hinglish: { placeholder: 'Agar main...' },
}

const MENU_ITEMS = [
  { id: 'overview', path: '/dashboard', icon: FiGrid, label: 'Overview' },
  { id: 'forecast', path: '/dashboard/forecast', icon: FiActivity, label: 'Forecast' },
  { id: 'sandbox', path: '/dashboard/sandbox', icon: FiTarget, label: 'What-If Sandbox' },
  { id: 'goal', path: '/dashboard/goal', icon: FiFlag, label: 'Goal Forecaster' },
]

const SETTINGS_ITEM = { id: 'settings', path: '/dashboard/settings', icon: FiSettings, label: 'Settings' }
const PERSONAS = ['professional', 'freelancer', 'student']
const DEFAULT_ALERT_BUFFER = 500
const ALERT_BUFFER_STORAGE_KEY = 'walletgo_alert_buffer'

function formatDateLabel(rawDate) {
  const parsed = new Date(rawDate)
  if (Number.isNaN(parsed.getTime())) return rawDate
  return parsed.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

function readStoredAlertBuffer() {
  if (typeof window === 'undefined') return DEFAULT_ALERT_BUFFER
  const raw = window.localStorage.getItem(ALERT_BUFFER_STORAGE_KEY)
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : DEFAULT_ALERT_BUFFER
}

function normalizeForecastRows(rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return DEFAULT_FORECAST
  }

  const first = toNumber(rows[0]?.balance, 0)
  const last = toNumber(rows[rows.length - 1]?.balance, first)
  const step = rows.length > 1 ? (last - first) / (rows.length - 1) : 0

  return rows.map((row, idx) => {
    const rawDate = row.date
    const balance = toNumber(row.balance, 0)
    const low = toNumber(row.low, balance - 150)
    const high = toNumber(row.high, balance + 150)
    return {
      rawDate,
      date: formatDateLabel(rawDate),
      balance,
      low,
      high,
      baseline: Number((first + step * idx).toFixed(2)),
    }
  })
}

function readScenarioBalance(row, fallback = null) {
  const raw = row?.balance ?? row?.predicted_balance
  return toNumber(raw, fallback)
}

function normalizeIsoDate(rawDate) {
  const parsed = new Date(rawDate)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toISOString().slice(0, 10)
}

function buildAiInsight(payload, currency = 'USD', alertBuffer = DEFAULT_ALERT_BUFFER) {
  const likelyRows = payload?.likely?.forecast_data || []
  if (!likelyRows.length) {
    return ''
  }

  const balances = likelyRows.map((row) => readScenarioBalance(row, 0))
  const minBalance = Math.min(...balances)
  const minIndex = balances.findIndex((value) => value === minBalance)
  const minDateRaw = likelyRows[minIndex]?.date
  const minDate = formatDateLabel(minDateRaw)

  const riskyDays = balances.filter((value) => value < alertBuffer).length
  const riskPct = Math.round((riskyDays / Math.max(balances.length, 1)) * 100)

  const laterIndex = Math.min(minIndex + 7, likelyRows.length - 1)
  const laterBalance = readScenarioBalance(likelyRows[laterIndex], minBalance)
  const laterDate = formatDateLabel(likelyRows[laterIndex]?.date)

  const impact = toNumber(payload?.likely?.net_difference, 0)
  const direction = impact < 0 ? 'lose money' : impact > 0 ? 'gain money' : 'stay about the same'

  return (
    `💡 AI Insight: In this plan, you may ${direction}. `
    + `Your lowest balance is around ${minDate}: ${formatMoney(minBalance, currency)}. `
    + `${riskPct}% of days are in the risk zone (below ${formatMoney(alertBuffer, currency)}). `
    + `By ${laterDate}, your balance is expected to be about ${formatMoney(laterBalance, currency)}.`
  )
}

function countLowBufferDays(rows, alertBuffer) {
  if (!Array.isArray(rows) || !rows.length) return 0
  return rows.filter((row) => readScenarioBalance(row, 0) < alertBuffer).length
}

function computeLiquidityScore(rows, alertBuffer = DEFAULT_ALERT_BUFFER) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return {
      score: 50,
      label: 'Insufficient forecast data',
      tone: 'text-slate-700',
      weather: 'Cloudy',
      weatherKey: 'cloudy',
      weatherClass: 'bg-amber-100 text-amber-800 border-amber-200',
    }
  }

  const balances = rows.map((row) => toNumber(row.balance, 0))
  const minBalance = Math.min(...balances)

  const deltas = balances
    .slice(1)
    .map((balance, idx) => balance - balances[idx])
  const meanDelta = deltas.length
    ? deltas.reduce((sum, value) => sum + value, 0) / deltas.length
    : 0
  const variance = deltas.length
    ? deltas.reduce((sum, value) => sum + (value - meanDelta) ** 2, 0) / deltas.length
    : 0
  const volatility = Math.sqrt(variance)

  const safeDaysRatio = rows.length
    ? rows.filter((row) => toNumber(row.balance, 0) >= alertBuffer).length / rows.length
    : 0

  // Blend solvency floor, consistency, and cushion days into a continuous 0-100 score.
  const floorScore = clamp(((minBalance + 2000) / 8000) * 100, 0, 100)
  const stabilityScore = 100 - clamp((volatility / 700) * 100, 0, 100)
  const bufferScore = clamp(safeDaysRatio * 100, 0, 100)

  const score = Math.round(clamp((floorScore * 0.55) + (bufferScore * 0.25) + (stabilityScore * 0.2), 0, 100))

  let weather = 'Sunny'
  let weatherKey = 'sunny'
  let weatherClass = 'bg-emerald-100 text-emerald-800 border-emerald-200'
  const gapFromBuffer = minBalance - alertBuffer
  if (gapFromBuffer < 0) {
    weather = 'Rainy'
    weatherKey = 'rainy'
    weatherClass = 'bg-pink-100 text-pink-800 border-pink-200'
  } else if (gapFromBuffer <= 250) {
    weather = 'Cloudy'
    weatherKey = 'cloudy'
    weatherClass = 'bg-amber-100 text-amber-800 border-amber-200'
  }

  if (score >= 80) return { score, label: 'Smooth sailing for 6 weeks', tone: 'text-emerald-700', weather, weatherKey, weatherClass }
  if (score >= 60) return { score, label: 'Caution: Tight spot ahead', tone: 'text-amber-700', weather, weatherKey, weatherClass }
  return { score, label: 'Action needed this week', tone: 'text-red-700', weather, weatherKey, weatherClass }
}

function getCurrentTab(pathname) {
  if (pathname === '/dashboard' || pathname === '/dashboard/') return 'overview'
  if (pathname.startsWith('/dashboard/forecast')) return 'forecast'
  if (pathname.startsWith('/dashboard/sandbox')) return 'sandbox'
  if (pathname.startsWith('/dashboard/goal')) return 'goal'
  if (pathname.startsWith('/dashboard/settings')) return 'settings'
  return 'overview'
}

function formatMoney(value, currencyCode = 'USD') {
  const symbols = { USD: '$', GBP: 'GBP ', EUR: 'EUR ' }
  const symbol = symbols[currencyCode] || '$'
  return `${symbol}${Math.round(value).toLocaleString()}`
}

function getTimelineEvent(rawDate) {
  const parsed = new Date(rawDate)
  if (Number.isNaN(parsed.getTime())) return null
  const day = parsed.getDate()
  if (day === 5) return { emoji: '💰', label: 'Payday' }
  if (day === 1) return { emoji: '📅', label: 'Rent' }
  if (day === 10) return { emoji: '🎬', label: 'Subscription' }
  return null
}

function ForecastTooltip({ active, payload, label, currency }) {
  if (!active || !payload || !payload.length) return null
  const row = payload[0]?.payload || {}

  return (
    <div className="rounded-xl border border-slate-200 bg-white/95 px-3 py-2 shadow-md text-sm">
      <p className="font-semibold text-slate-900">{label}</p>
      <p className="text-slate-700">Balance: {formatMoney(row.balance, currency)}</p>
      <p className="text-emerald-700">Inflows: +{formatMoney(row.inflows || 0, currency)}</p>
      <p className="text-rose-700">Outflows: -{formatMoney(row.outflows || 0, currency)}</p>
    </div>
  )
}

function LiquidityGauge({ score, label, isDark, minBalanceText }) {
  const clamped = Math.max(0, Math.min(100, score))
  const angleRad = Math.PI * (1 - clamped / 100)
  const centerX = 120
  const centerY = 110
  const needleRadius = 52
  const needleX = centerX + needleRadius * Math.cos(angleRad)
  const needleY = centerY - needleRadius * Math.sin(angleRad)
  const tone = clamped >= 80 ? 'text-emerald-300' : clamped >= 50 ? 'text-amber-300' : 'text-red-300'
  const needleColor = isDark ? '#f8fafc' : '#0f172a'
  const progress = clamped / 100

  return (
    <div className="w-full max-w-[18.5rem] mx-auto px-2 pt-2 pb-1 overflow-hidden">
      <svg viewBox="0 0 240 150" className="w-full h-[11.5rem] relative z-10">
        <defs>
          <linearGradient id="gaugeArcGradient" x1="20" y1="110" x2="220" y2="110" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="52%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
          <filter id="needleGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#38bdf8" floodOpacity="0.55" />
          </filter>
        </defs>

        <path d="M20 110 A100 100 0 0 1 220 110" fill="none" stroke="rgba(148,163,184,0.26)" strokeWidth="10" strokeLinecap="round" />
        <motion.path
          d="M20 110 A100 100 0 0 1 220 110"
          fill="none"
          stroke="url(#gaugeArcGradient)"
          strokeWidth="10"
          strokeLinecap="round"
          pathLength="100"
          strokeDasharray="100"
          initial={{ strokeDashoffset: 100 }}
          animate={{ strokeDashoffset: 100 - progress * 100 }}
          transition={{ type: 'spring', stiffness: 60, damping: 20 }}
        />

        <motion.line
          x1={centerX}
          y1={centerY}
          initial={{ x2: centerX - needleRadius, y2: centerY }}
          animate={{ x2: needleX, y2: needleY }}
          transition={{ type: 'spring', stiffness: 60, damping: 14 }}
          stroke={needleColor}
          strokeWidth="4"
          strokeLinecap="round"
          filter="url(#needleGlow)"
        />
        <circle cx={centerX} cy={centerY} r="7" fill={needleColor} />
      </svg>
      <div className="text-center -mt-2 px-1">
        <p className={`text-6xl leading-none font-semibold tracking-tight drop-shadow-sm ${tone}`}>{clamped}</p>
        <p className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-medium ${isDark ? 'bg-white/10 text-slate-200' : 'bg-slate-900/5 text-slate-700'}`}>
          {label}
        </p>
        <motion.p
          className={`text-base font-medium mt-2 whitespace-nowrap ${isDark ? 'text-slate-200/95' : 'text-slate-700'}`}
          animate={{ opacity: [0.75, 1, 0.75], scale: [1, 1.02, 1] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
        >
          Minimum 30-day balance: {minBalanceText}
        </motion.p>
      </div>
    </div>
  )
}

function MetricCard({ title, value, note, tone }) {
  return (
    <div className="glass-card p-5 hover:shadow-[0_14px_34px_rgba(15,23,42,0.14)] transition-shadow">
      <p className="text-xs uppercase tracking-[0.12em] text-slate-500 mb-2">{title}</p>
      <p className={`text-4xl font-bold ${tone || 'text-slate-900'}`}>{value}</p>
      <p className="text-sm text-gray-600 mt-2">{note}</p>
    </div>
  )
}

function MenuButton({ item, isMenuCollapsed, onClick }) {
  return (
    <NavLink
      to={item.path}
      onClick={onClick}
      className={({ isActive }) =>
        `menu-button w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition ${isActive ? 'menu-button-active' : ''}`
      }
      end={item.path === '/dashboard'}
    >
      <item.icon size={18} />
      {!isMenuCollapsed && <span>{item.label}</span>}
    </NavLink>
  )
}

export default function DashboardPage() {
  const [language, setLanguage] = useState('en')
  const [showBaseline, setShowBaseline] = useState(false)
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [scenarioInput, setScenarioInput] = useState('')
  const [scenarioTitle, setScenarioTitle] = useState('')
  const [lastExecutedScenarioText, setLastExecutedScenarioText] = useState('')
  const [forecastRows, setForecastRows] = useState(DEFAULT_FORECAST)
  const [scenarioRows, setScenarioRows] = useState({ low: [], likely: [], high: [] })
  const [latestScenarioPayload, setLatestScenarioPayload] = useState(null)
  const [isScenarioActive, setIsScenarioActive] = useState(false)
  const [isScenarioRunning, setIsScenarioRunning] = useState(false)
  const [isScenarioSaving, setIsScenarioSaving] = useState(false)
  const [leftScenarioId, setLeftScenarioId] = useState('')
  const [rightScenarioId, setRightScenarioId] = useState('')
  const [isComparingScenarios, setIsComparingScenarios] = useState(false)
  const [isForecastLoading, setIsForecastLoading] = useState(true)
  const [confidence, setConfidence] = useState(72)
  const [minBalance, setMinBalance] = useState(2120)
  const [minBalanceDate, setMinBalanceDate] = useState('May 8')
  const [scenarioNote, setScenarioNote] = useState('Try a scenario to overlay low/likely/high dotted lines on the graph.')
  const [scenarioInsight, setScenarioInsight] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [alertBuffer, setAlertBuffer] = useState(() => readStoredAlertBuffer())
  const [theme, setTheme] = useState(() => localStorage.getItem('radar_theme') || 'dark')
  const [persona, setPersona] = useState('professional')
  const [isTransactionCheckLoading, setIsTransactionCheckLoading] = useState(false)
  const [hasTransactions, setHasTransactions] = useState(null)

  const { signOut, user, isAuthenticated } = useAuth()
  const {
    generateForecast,
    runScenario,
    clearEphemeralTransactions,
    ephemeralTransactions,
    savedScenarios,
    scenarioComparison,
    loadSavedScenarios,
    saveScenario,
    compareSavedScenarios,
  } = useForecast()
  const navigate = useNavigate()
  const location = useLocation()

  const currentTab = getCurrentTab(location.pathname)
  const contentContainerClass = currentTab === 'forecast' || currentTab === 'settings'
    ? 'w-full max-w-[1600px] mx-auto p-4 md:p-8'
    : currentTab === 'goal'
      ? 'max-w-3xl mx-auto p-4 md:p-8'
      : 'max-w-7xl mx-auto p-4 md:p-8'
  const liquidity = useMemo(
    () => computeLiquidityScore(forecastRows, alertBuffer),
    [forecastRows, alertBuffer]
  )
  const hasFetchedForecast = useRef(false)
  const isDark = theme === 'dark'
  const greenZoneStreak = useMemo(() => {
    let streak = 0
    for (let i = forecastRows.length - 1; i >= 0; i -= 1) {
      if (forecastRows[i].balance >= alertBuffer) streak += 1
      else break
    }
    return Math.max(1, streak)
  }, [forecastRows, alertBuffer])

  useEffect(() => {
    localStorage.setItem('radar_theme', theme)
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem(ALERT_BUFFER_STORAGE_KEY, String(alertBuffer))
  }, [alertBuffer])

  useEffect(() => {
    if (!latestScenarioPayload) {
      setScenarioInsight('')
      return
    }
    setScenarioInsight(buildAiInsight(latestScenarioPayload, currency, alertBuffer))
  }, [latestScenarioPayload, currency, alertBuffer])

  useEffect(() => {
    if (currentTab === 'settings' && !isAuthenticated) {
      navigate('/signin', { replace: true, state: { from: location } })
    }
  }, [currentTab, isAuthenticated, navigate, location])

  useEffect(() => {
    if (!isAuthenticated) {
      setHasTransactions(null)
      setIsTransactionCheckLoading(false)
      return
    }

    let cancelled = false

    const checkTransactionHistory = async () => {
      setIsTransactionCheckLoading(true)
      try {
        const response = await transactionAPI.list(1, 0)
        const rows = Array.isArray(response.data)
          ? response.data
          : (response.data?.transactions || [])
        if (!cancelled) {
          setHasTransactions(rows.length > 0)
        }
      } catch (error) {
        if (!cancelled) {
          // Fallback to existing-user view if lookup fails.
          setHasTransactions(true)
        }
      } finally {
        if (!cancelled) {
          setIsTransactionCheckLoading(false)
        }
      }
    }

    checkTransactionHistory()

    return () => {
      cancelled = true
    }
  }, [isAuthenticated])

  const fetchForecast = useCallback(async () => {
    setIsForecastLoading(true)
    try {
      const payload = await generateForecast(42)
      const normalizedRows = normalizeForecastRows(payload.forecast_data)
      setForecastRows(normalizedRows)
      setConfidence(toNumber(payload.confidence, 72))
      setMinBalance(
        toNumber(
          payload.min_balance,
          normalizedRows.reduce((m, r) => Math.min(m, r.balance), normalizedRows[0].balance)
        )
      )
      setMinBalanceDate(formatDateLabel(payload.min_balance_date || normalizedRows[0].rawDate))
    } catch (error) {
      toast.error('Could not load live forecast, showing demo data')
    } finally {
      setIsForecastLoading(false)
    }
  }, [generateForecast])

  useEffect(() => {
    if (hasFetchedForecast.current) return
    if (isAuthenticated && (isTransactionCheckLoading || hasTransactions === false)) return

    hasFetchedForecast.current = true
    fetchForecast()
  }, [fetchForecast, hasTransactions, isAuthenticated, isTransactionCheckLoading])

  useEffect(() => {
    loadSavedScenarios(12).catch(() => {
      // Ignore load errors here; save/compare actions will surface explicit toasts.
    })
  }, [loadSavedScenarios])

  const handleStatementUploaded = useCallback(async () => {
    if (isAuthenticated) {
      setHasTransactions(true)
    }
    hasFetchedForecast.current = false
    await fetchForecast()
  }, [fetchForecast, isAuthenticated])

  const scenarioData = useMemo(() => {
    const lowMap = new Map(scenarioRows.low.map((row) => [row.date, readScenarioBalance(row, null)]))
    const likelyMap = new Map(scenarioRows.likely.map((row) => [row.date, readScenarioBalance(row, null)]))
    const highMap = new Map(scenarioRows.high.map((row) => [row.date, readScenarioBalance(row, null)]))

    return forecastRows.map((row, idx) => {
      const lowByDate = lowMap.get(row.rawDate)
      const likelyByDate = likelyMap.get(row.rawDate)
      const highByDate = highMap.get(row.rawDate)

      const lowByIndex = scenarioRows.low[idx] ? readScenarioBalance(scenarioRows.low[idx], row.balance) : null
      const likelyByIndex = scenarioRows.likely[idx] ? readScenarioBalance(scenarioRows.likely[idx], row.balance) : null
      const highByIndex = scenarioRows.high[idx] ? readScenarioBalance(scenarioRows.high[idx], row.balance) : null

      return {
        ...row,
        scenarioLow: lowByDate ?? lowByIndex ?? row.balance,
        scenarioLikely: likelyByDate ?? likelyByIndex ?? row.balance,
        scenarioHigh: highByDate ?? highByIndex ?? row.balance,
        baselinePlot: toNumber(row.balance, 0),
        scenarioPlot: toNumber(likelyByDate ?? likelyByIndex ?? row.balance, 0),
        inflows: Math.max(0, row.balance - toNumber(forecastRows[idx - 1]?.balance, row.balance)),
        outflows: Math.max(0, toNumber(forecastRows[idx - 1]?.balance, row.balance) - row.balance),
        marker: getTimelineEvent(row.rawDate),
      }
    })
  }, [forecastRows, scenarioRows])

  const plottedEvents = useMemo(
    () => scenarioData
      .filter((row) => row.marker)
      .map((row) => ({
        key: `${row.rawDate}-${row.marker.label}`,
        date: row.date,
        balance: row.balance,
        marker: row.marker,
      })),
    [scenarioData]
  )

  const forecastHighlights = useMemo(() => {
    const byLabel = new Map()
    plottedEvents.forEach((event) => {
      if (!byLabel.has(event.marker.label)) {
        byLabel.set(event.marker.label, event)
      }
    })

    return [
      byLabel.get('Payday') || { marker: { emoji: '💰', label: 'Payday' }, date: 'N/A' },
      byLabel.get('Rent') || { marker: { emoji: '📅', label: 'Rent Debited' }, date: 'N/A' },
      byLabel.get('Subscription') || { marker: { emoji: '🎬', label: 'Subscriptions' }, date: 'N/A' },
    ]
  }, [plottedEvents])

  const chartLegendPayload = useMemo(() => {
    const payload = [
      { value: 'Projected Balance', type: 'line', id: 'balance', color: '#2563eb' },
    ]

    if (isScenarioActive) {
      payload.push(
        { value: 'Scenario Low', type: 'line', id: 'scenarioLow', color: '#ef4444' },
        { value: 'Scenario Likely', type: 'line', id: 'scenarioLikely', color: isDark ? '#e2e8f0' : '#111827' },
        { value: 'Scenario High', type: 'line', id: 'scenarioHigh', color: '#16a34a' },
      )
    }

    if (showBaseline) {
      payload.push({ value: 'Baseline', type: 'line', id: 'baseline', color: '#9ca3af' })
    }

    return payload
  }, [isDark, isScenarioActive, showBaseline])

  const scenarioPlotDomain = useMemo(() => {
    if (!scenarioData.length) {
      return ['auto', 'auto']
    }

    const values = scenarioData.flatMap((row) => [
      toNumber(row.balance, 0),
      toNumber(row.scenarioLow, 0),
      toNumber(row.scenarioLikely, 0),
      toNumber(row.scenarioHigh, 0),
    ])
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)
    const pad = Math.max(120, (maxValue - minValue) * 0.18)

    return [Math.floor(minValue - pad), Math.ceil(maxValue + pad)]
  }, [scenarioData])

  const comparisonChartData = useMemo(() => {
    const leftRows = scenarioComparison?.left?.likely?.forecast_data || []
    const rightRows = scenarioComparison?.right?.likely?.forecast_data || []
    if (!leftRows.length && !rightRows.length) return []

    const allDatesValid = [...leftRows, ...rightRows].every((row) => normalizeIsoDate(row?.date))

    if (allDatesValid) {
      const leftMap = new Map(
        leftRows.map((row) => [normalizeIsoDate(row.date), toNumber(row.predicted_balance ?? row.balance, 0)])
      )
      const rightMap = new Map(
        rightRows.map((row) => [normalizeIsoDate(row.date), toNumber(row.predicted_balance ?? row.balance, 0)])
      )
      const allDates = Array.from(new Set([...leftMap.keys(), ...rightMap.keys()]))
        .filter(Boolean)
        .sort((a, b) => a.localeCompare(b))

      return allDates.map((date) => ({
        date: formatDateLabel(date),
        left: leftMap.has(date) ? leftMap.get(date) : null,
        right: rightMap.has(date) ? rightMap.get(date) : null,
      }))
    }

    const length = Math.max(leftRows.length, rightRows.length)
    return Array.from({ length }, (_, idx) => ({
      date: formatDateLabel(leftRows[idx]?.date || rightRows[idx]?.date || `Day ${idx + 1}`),
      left: idx < leftRows.length ? toNumber(leftRows[idx]?.predicted_balance ?? leftRows[idx]?.balance, 0) : null,
      right: idx < rightRows.length ? toNumber(rightRows[idx]?.predicted_balance ?? rightRows[idx]?.balance, 0) : null,
    }))
  }, [scenarioComparison])

  const leftScenarioLabel = useMemo(() => {
    const match = savedScenarios.find((item) => String(item.id) === String(leftScenarioId))
    return match?.title || match?.description || 'Left scenario'
  }, [savedScenarios, leftScenarioId])

  const rightScenarioLabel = useMemo(() => {
    const match = savedScenarios.find((item) => String(item.id) === String(rightScenarioId))
    return match?.title || match?.description || 'Right scenario'
  }, [savedScenarios, rightScenarioId])

  const comparisonLowBufferDays = useMemo(() => {
    const leftRows = scenarioComparison?.left?.likely?.forecast_data || []
    const rightRows = scenarioComparison?.right?.likely?.forecast_data || []

    const left = leftRows.length
      ? countLowBufferDays(leftRows, alertBuffer)
      : (scenarioComparison?.comparison?.left_low_buffer_days ?? 0)
    const right = rightRows.length
      ? countLowBufferDays(rightRows, alertBuffer)
      : (scenarioComparison?.comparison?.right_low_buffer_days ?? 0)

    return { left, right }
  }, [scenarioComparison, alertBuffer])

  const scenarioLikelyStroke = useMemo(() => {
    const color = String(latestScenarioPayload?.likely?.line_color || '').toLowerCase()
    if (color === 'red') return '#ef4444'
    if (color === 'green') return '#22c55e'

    if (!scenarioData.length) return '#f8fafc'
    const last = scenarioData[scenarioData.length - 1]
    const delta = toNumber(last?.scenarioLikely, 0) - toNumber(last?.balance, 0)
    if (delta < 0) return '#ef4444'
    if (delta > 0) return '#22c55e'
    return '#f8fafc'
  }, [latestScenarioPayload, scenarioData])

  const handleSignOut = async () => {
    localStorage.removeItem(ALERT_BUFFER_STORAGE_KEY)
    await signOut()
    navigate('/signin')
  }

  const handleExitDemo = () => {
    localStorage.removeItem(ALERT_BUFFER_STORAGE_KEY)
    clearEphemeralTransactions()
    navigate('/')
  }

  const evaluateScenario = async (text) => {
    const trimmed = (text || '').trim()
    if (!trimmed) {
      toast.error('Enter a scenario first')
      return
    }

    setIsScenarioRunning(true)
    try {
      const payload = await runScenario(trimmed, language)
      const lowRows = payload.low?.forecast_data || []
      const likelyRows = payload.likely?.forecast_data || []
      const highRows = payload.high?.forecast_data || []

      if (!lowRows.length || !likelyRows.length || !highRows.length) {
        toast.error('Scenario response was incomplete')
        return
      }

      setScenarioRows({ low: lowRows, likely: likelyRows, high: highRows })
      setLatestScenarioPayload(payload)
      setLastExecutedScenarioText(trimmed)
      setIsScenarioActive(true)
      setScenarioNote(payload.explanation || 'Scenario applied successfully.')
      setScenarioInsight(buildAiInsight(payload, currency, alertBuffer))
      toast.success('Scenario updated on chart')
    } catch (error) {
      setScenarioInsight('')
      toast.error('Failed to run scenario. Please try again.')
    } finally {
      setIsScenarioRunning(false)
    }
  }

  const handleSaveScenario = async () => {
    if (!latestScenarioPayload || !isScenarioActive) {
      toast.error('Run a scenario first, then save it.')
      return
    }

    setIsScenarioSaving(true)
    try {
      const trimmedTitle = scenarioTitle.trim()
      const executedDescription = (
        latestScenarioPayload?.intent?.description
        || lastExecutedScenarioText
        || scenarioInput.trim()
        || 'What-if scenario'
      )
      await saveScenario({
        title: trimmedTitle || undefined,
        description: executedDescription,
        language,
        analysis: latestScenarioPayload,
      })
      await loadSavedScenarios(12)
      setScenarioTitle('')
      toast.success('Scenario saved')
    } catch (error) {
      toast.error('Could not save scenario')
    } finally {
      setIsScenarioSaving(false)
    }
  }

  const handleCompareScenarios = async () => {
    if (!leftScenarioId || !rightScenarioId) {
      toast.error('Select two saved scenarios to compare')
      return
    }
    if (leftScenarioId === rightScenarioId) {
      toast.error('Pick two different scenarios')
      return
    }

    setIsComparingScenarios(true)
    try {
      await compareSavedScenarios(leftScenarioId, rightScenarioId)
      toast.success('Scenario comparison ready')
    } catch (error) {
      toast.error('Could not compare selected scenarios')
    } finally {
      setIsComparingScenarios(false)
    }
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {(!isAuthenticated || hasTransactions) && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <div className="mb-4">
            <h2 className="text-xl font-bold text-slate-900">Upload Statement</h2>
            <p className="text-sm text-slate-600 mt-1">
              {isAuthenticated
                ? 'Add another CSV or PDF anytime to keep your forecast and stats updated.'
                : 'Upload a CSV or PDF in demo mode and regenerate your forecast from parsed statement transactions.'}
            </p>
          </div>
          <StatementUploader onSuccess={handleStatementUploaded} />
        </motion.div>
      )}

      <div className="grid lg:grid-cols-3 gap-5">
        <MetricCard
          title="Liquidity Score"
          value={liquidity.score}
          note={liquidity.label}
          tone={liquidity.tone}
        />
        <MetricCard
          title="Minimum 30-Day Balance"
          value={formatMoney(minBalance, currency)}
          note={`Expected on ${minBalanceDate}`}
          tone="text-amber-700"
        />
        <MetricCard
          title="Model Confidence"
          value={`${Math.round(confidence)}%`}
          note="Adjusted for unusual spending last month"
          tone="text-blue-700"
        />
      </div>

      <div className="grid xl:grid-cols-3 gap-6">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card xl:col-span-2 p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-slate-900">Liquidity Radar Gauge</h2>
            <span className="text-xs uppercase tracking-[0.16em] text-slate-500">0-100 score</span>
          </div>
          <div className="grid md:grid-cols-2 gap-6 items-center">
            <div className="p-1">
              <LiquidityGauge
                score={liquidity.score}
                label={liquidity.label}
                isDark={isDark}
                minBalanceText={formatMoney(minBalance, currency)}
              />
            </div>

            <div className="space-y-3">
              <div className="soft-panel px-4 py-3">
                <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Current Status</p>
                <p className="text-lg font-semibold text-slate-900">Stable with mild volatility</p>
              </div>
              <div className="soft-panel px-4 py-3">
                <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Closest Risk Window</p>
                <p className="text-lg font-semibold text-slate-900">{minBalanceDate}</p>
              </div>
              <div className="soft-panel px-4 py-3">
                <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Confidence</p>
                <p className="text-lg font-semibold text-slate-900">{Math.round(confidence)}% model confidence</p>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="health-card rounded-2xl p-6 text-slate-900 border border-amber-200 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 shadow-[0_14px_30px_rgba(0,0,0,0.08)]">
          <p className="text-sm uppercase tracking-[0.14em] text-sky-700 mb-4">Current Health</p>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <FiTrendingUp className="text-sky-600" />
              <p className="text-sm">Trend: stable with payday uplift in week 2</p>
            </div>
            <div className="flex items-center gap-3">
              <FiShield className="text-teal-600" />
              <p className="text-sm">Buffer above threshold for most days</p>
            </div>
            <div className="rounded-xl bg-white border border-amber-200 px-4 py-3 health-next-step">
              <p className="text-xs uppercase tracking-[0.12em] text-amber-700">Suggested Next Step</p>
              <p className="mt-1 font-semibold">Run a what-if for one high-value purchase</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )

  const renderForecast = () => (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6 w-full">
      <div className="glass-card p-6 w-full">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-slate-900">Forecast Timeline</h2>
            <span
              title="Lower confidence due to unusual spending last month"
              className="rounded-full px-3 py-1 text-xs font-semibold bg-sky-100 text-sky-800 border border-sky-200"
            >
              {Math.round(confidence)}% confidence
            </span>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showBaseline}
              onChange={(e) => setShowBaseline(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm font-medium text-gray-700">Show baseline</span>
          </label>
        </div>
        <ResponsiveContainer width="100%" height={370}>
          <AreaChart data={scenarioData}>
            <defs>
              <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={isDark ? 'rgba(148,163,184,0.22)' : '#e2e8f0'} />
            <XAxis dataKey="date" stroke={isDark ? '#cbd5e1' : '#475569'} />
            <YAxis stroke={isDark ? '#cbd5e1' : '#475569'} />
            <Tooltip
              content={<ForecastTooltip currency={currency} />}
            />
            <Legend
              payload={chartLegendPayload}
              iconType="line"
              wrapperStyle={{ fontSize: '12px', color: isDark ? '#cbd5e1' : '#475569' }}
            />
            <Area type="monotone" dataKey="balance" stroke="#2563eb" strokeWidth={3} fillOpacity={1} fill="url(#colorBalance)" />
            {scenarioData.map((row) =>
              row.marker ? (
                <ReferenceDot
                  key={`${row.date}-${row.marker.label}`}
                  x={row.date}
                  y={row.balance}
                  r={6}
                  fill="#0ea5e9"
                  stroke="#ffffff"
                  label={{ value: row.marker.emoji, position: 'top', fontSize: 14 }}
                />
              ) : null
            )}
            {isScenarioActive && (
              <>
                <Line type="monotone" dataKey="scenarioLow" stroke="#ef4444" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="scenarioLikely" stroke={isDark ? '#e2e8f0' : '#111827'} strokeDasharray="5 5" strokeWidth={2.4} dot={false} />
                <Line type="monotone" dataKey="scenarioHigh" stroke="#16a34a" strokeDasharray="5 5" strokeWidth={2} dot={false} />
              </>
            )}
            {showBaseline && (
              <Line type="monotone" dataKey="baseline" stroke="#9ca3af" strokeDasharray="6 6" strokeWidth={2} dot={false} />
            )}
          </AreaChart>
        </ResponsiveContainer>
        {isForecastLoading && <p className="mt-4 text-sm text-gray-500">Loading live forecast...</p>}
      </div>

      <div className="grid md:grid-cols-3 gap-4 text-sm w-full">
        <div className="soft-panel px-4 py-3 font-medium text-slate-800">{forecastHighlights[0].marker.emoji} {forecastHighlights[0].marker.label}: {forecastHighlights[0].date}</div>
        <div className="soft-panel px-4 py-3 font-medium text-slate-800">{forecastHighlights[1].marker.emoji} {forecastHighlights[1].marker.label}: {forecastHighlights[1].date}</div>
        <div className="soft-panel px-4 py-3 font-medium text-slate-800">{forecastHighlights[2].marker.emoji} {forecastHighlights[2].marker.label}: {forecastHighlights[2].date}</div>
      </div>
    </motion.div>
  )

  const renderSandbox = () => (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="grid xl:grid-cols-3 gap-6 items-start">
        <section className="sandbox-panel glass-card xl:col-span-2 p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-bold text-slate-900">What-If Sandbox</h2>
            <div className="flex flex-wrap gap-2">
              {[
                { code: 'en', label: '🌐 English' },
                { code: 'hinglish', label: '🇮🇳 Hinglish' },
                { code: 'hi', label: '🇮🇳 Hindi' },
              ].map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className={`sandbox-chip px-3 py-1 rounded-full text-sm font-medium transition ${language === lang.code ? 'sandbox-chip-active' : ''}`}
                >
                  {lang.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-[1fr_auto]">
            <input
              type="text"
              value={scenarioInput}
              onChange={(e) => setScenarioInput(e.target.value)}
              placeholder={LANGUAGE_TEXTS[language].placeholder}
              className="sandbox-input w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
            />
            <button
              onClick={() => evaluateScenario(scenarioInput)}
              disabled={isScenarioRunning}
              className="w-full md:w-auto px-6 py-2.5 primary-cta"
            >
              {isScenarioRunning ? 'Running...' : 'Run Scenario'}
            </button>
          </div>

          <div className="grid gap-3 md:grid-cols-[1fr_auto]">
            <input
              type="text"
              value={scenarioTitle}
              onChange={(e) => setScenarioTitle(e.target.value)}
              placeholder="Optional title (e.g., Buy car now)"
              className="sandbox-input w-full px-4 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
            />
            <button
              onClick={handleSaveScenario}
              disabled={!isScenarioActive || isScenarioSaving}
              className="w-full md:w-auto px-5 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 font-medium hover:bg-slate-50 disabled:opacity-50"
            >
              {isScenarioSaving ? 'Saving...' : 'Save Scenario'}
            </button>
          </div>

          <p className="sandbox-note text-sm text-gray-700">{scenarioNote}</p>
          {!!scenarioInsight && (
            <div className="rounded-xl border border-teal-300/40 bg-teal-500/10 px-4 py-3 text-sm text-teal-100">
              {scenarioInsight}
            </div>
          )}
        </section>

        <aside className="guide-card rounded-2xl p-6 text-slate-900 border border-sky-200 bg-gradient-to-br from-sky-50 via-cyan-50 to-teal-50 shadow-[0_14px_30px_rgba(0,0,0,0.08)]">
          <p className="text-xs uppercase tracking-[0.14em] text-sky-700 mb-4">Quick Guide</p>
          <div className="space-y-3 text-sm">
            <p>1. Type a scenario and run it</p>
            <p>2. Give it a title and save it</p>
            <p>3. Compare any two saved futures</p>
          </div>
          <div className="mt-5 rounded-xl bg-white border border-sky-200 p-4 text-sm space-y-2">
            <p>Red dotted line: downside</p>
            <p>Dark dotted line: likely path</p>
            <p>Green dotted line: upside</p>
          </div>
        </aside>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-xl border border-slate-700/40 bg-slate-950/30 p-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-slate-300">Scenario Plot</p>
          {isScenarioActive && <span className="text-xs text-slate-300">Original (white) vs Scenario (red/green)</span>}
        </div>

        {isScenarioActive ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={scenarioData}>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? 'rgba(148,163,184,0.22)' : '#e2e8f0'} />
              <XAxis dataKey="date" stroke={isDark ? '#cbd5e1' : '#475569'} />
              <YAxis stroke={isDark ? '#cbd5e1' : '#475569'} domain={scenarioPlotDomain} />
              <Tooltip content={<ForecastTooltip currency={currency} />} />
              <Legend iconType="line" wrapperStyle={{ fontSize: '12px', color: isDark ? '#cbd5e1' : '#475569' }} />
              <Line
                type="monotone"
                dataKey="baselinePlot"
                name="Original (baseline)"
                stroke="#f8fafc"
                strokeWidth={2.6}
                connectNulls
                dot={false}
                isAnimationActive={false}
                activeDot={{ r: 4.2 }}
              />
              <Line
                type="monotone"
                dataKey="scenarioPlot"
                name="Scenario"
                stroke={scenarioLikelyStroke}
                strokeWidth={3.4}
                connectNulls
                dot={false}
                isAnimationActive={false}
                activeDot={{ r: 4.2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-slate-400">Run a scenario to generate the plot.</p>
        )}
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="soft-panel rounded-xl p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Saved Scenario Comparison</p>
          <button
            onClick={handleCompareScenarios}
            disabled={isComparingScenarios || !leftScenarioId || !rightScenarioId}
            className="px-5 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 font-medium hover:bg-slate-50 disabled:opacity-50"
          >
            {isComparingScenarios ? 'Comparing...' : 'Compare Scenarios'}
          </button>
        </div>

        <div className="grid gap-2 md:grid-cols-2">
          <select
            value={leftScenarioId}
            onChange={(e) => setLeftScenarioId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 bg-white"
          >
            <option value="">Select left scenario</option>
            {savedScenarios.map((item) => (
              <option key={`left-${item.id}`} value={item.id}>
                {item.title || item.description}
              </option>
            ))}
          </select>
          <select
            value={rightScenarioId}
            onChange={(e) => setRightScenarioId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 bg-white"
          >
            <option value="">Select right scenario</option>
            {savedScenarios.map((item) => (
              <option key={`right-${item.id}`} value={item.id}>
                {item.title || item.description}
              </option>
            ))}
          </select>
        </div>

        {scenarioComparison?.comparison && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-800 space-y-1">
            <p>
              Winner: <strong>{scenarioComparison.comparison.winner}</strong>
            </p>
            <p>
              Final balance diff: <strong>{formatMoney(scenarioComparison.comparison.difference, currency)}</strong>
            </p>
            <p>
              Left final: {formatMoney(scenarioComparison.comparison.left_final_balance, currency)} | Right final: {formatMoney(scenarioComparison.comparison.right_final_balance, currency)}
            </p>
            <p>
              Left risk score: <strong>{scenarioComparison.comparison.left_risk_adjusted_score}</strong> | Right risk score: <strong>{scenarioComparison.comparison.right_risk_adjusted_score}</strong>
            </p>
            <p>
              Overdraft days: Left <strong>{scenarioComparison.comparison.left_negative_days}</strong> | Right <strong>{scenarioComparison.comparison.right_negative_days}</strong>
            </p>
            <p>
              Low-buffer days (&lt; {formatMoney(alertBuffer, currency)}): Left <strong>{comparisonLowBufferDays.left}</strong> | Right <strong>{comparisonLowBufferDays.right}</strong>
            </p>
            <p>
              Net scenario impact: Left <strong>{formatMoney(scenarioComparison.comparison.left_net_difference, currency)}</strong> | Right <strong>{formatMoney(scenarioComparison.comparison.right_net_difference, currency)}</strong>
            </p>
            <p>{scenarioComparison.summary_text}</p>
          </div>
        )}

        {comparisonChartData.length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-3">
            <p className="text-xs uppercase tracking-[0.12em] text-slate-500 mb-2">Graphical comparison (likely path)</p>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={comparisonChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? 'rgba(148,163,184,0.22)' : '#e2e8f0'} />
                <XAxis dataKey="date" stroke={isDark ? '#cbd5e1' : '#475569'} />
                <YAxis stroke={isDark ? '#cbd5e1' : '#475569'} />
                <Tooltip content={<ForecastTooltip currency={currency} />} />
                <Legend />
                <Line type="monotone" dataKey="left" name={leftScenarioLabel} stroke="#2563eb" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="right" name={rightScenarioLabel} stroke="#f97316" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </motion.div>
    </div>
  )

  const renderSettings = () => (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full space-y-6">
      <div className="glass-card p-7 md:p-9">
        <div className="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-6">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-sky-700 mb-2">Personalization</p>
            <h2 className="font-display text-4xl md:text-5xl leading-[0.95] text-slate-900">Settings Studio</h2>
            <p className="text-slate-600 mt-3 max-w-2xl">
              Shape your Radar experience for how you plan money day-to-day. Changes apply instantly across forecast, alerts, and scenario views.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 min-w-[280px]">
            <div className="soft-panel px-4 py-3">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Theme</p>
              <p className="mt-1 font-semibold text-slate-900">{theme === 'dark' ? 'Dark' : 'Light'}</p>
            </div>
            <div className="soft-panel px-4 py-3">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Currency</p>
              <p className="mt-1 font-semibold text-slate-900">{currency}</p>
            </div>
            <div className="soft-panel px-4 py-3 col-span-2">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Active Buffer</p>
              <p className="mt-1 font-semibold text-slate-900">{formatMoney(alertBuffer, currency)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid xl:grid-cols-3 gap-6 items-start">
        <div className="guide-card rounded-2xl p-6 border border-sky-200 bg-gradient-to-br from-sky-50 via-cyan-50 to-teal-50 shadow-[0_14px_30px_rgba(0,0,0,0.08)]">
          <p className="text-xs uppercase tracking-[0.14em] text-sky-700 mb-4">Personalization Tips</p>
          <div className="space-y-3 text-sm">
            <p>Pick your preferred currency before sharing screenshots or exports.</p>
            <p>Dark mode helps during demos and low-light judging sessions.</p>
            <p>Increase alert buffer if you want earlier warnings before tight days.</p>
          </div>
          <div className="mt-6 rounded-xl bg-white border border-sky-200 p-4 text-sm">
            Signed in as <span className="font-semibold">{user?.email || 'Unknown user'}</span>
          </div>
        </div>

        <div className="glass-card xl:col-span-2 p-7 md:p-8 space-y-8">
          <section className="space-y-3">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Display Currency</p>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 bg-white font-medium"
            >
              <option value="USD">USD ($)</option>
              <option value="GBP">GBP (GBP)</option>
              <option value="EUR">EUR (EUR)</option>
            </select>
          </section>

          <section className="space-y-3">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Appearance</p>
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-5 py-4">
              <div>
                <p className="font-semibold text-slate-800">Dark Mode</p>
                <p className="text-sm text-slate-600 mt-0.5">Switch between light and dark UI themes</p>
              </div>
              <button
                type="button"
                onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
                className={`w-16 h-9 rounded-full p-1 transition ${theme === 'dark' ? 'bg-teal-600' : 'bg-slate-300'}`}
                aria-label="Toggle dark mode"
              >
                <span
                  className={`block h-7 w-7 rounded-full bg-white transition-transform ${theme === 'dark' ? 'translate-x-7' : 'translate-x-0'}`}
                />
              </button>
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-4">
              <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Low Balance Alert Buffer</p>
              <span className="accent-pill">{formatMoney(alertBuffer, currency)}</span>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white px-5 py-4">
              <input
                type="range"
                min="200"
                max="3000"
                step="100"
                value={alertBuffer}
                onChange={(e) => setAlertBuffer(Number(e.target.value))}
                className="w-full accent-range"
              />
              <p className="text-sm text-slate-600 mt-2">
                Alert me when projected balance falls below <span className="font-semibold">{formatMoney(alertBuffer, currency)}</span>
              </p>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  )

  const renderFirstUploadStep = () => (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl">
      <div className="glass-card p-8">
        <p className="text-xs uppercase tracking-[0.14em] text-sky-700 mb-3">Account Setup</p>
        <h2 className="text-3xl font-bold text-slate-900 mb-3">Upload your first statement</h2>
        <p className="text-slate-600 mb-6">
          Once uploaded, your dashboard stats and forecast will appear automatically.
        </p>
        <StatementUploader onSuccess={handleStatementUploaded} />
      </div>
    </motion.div>
  )

  const renderTransactionCheck = () => (
    <div className="max-w-3xl glass-card p-8">
      <h2 className="text-2xl font-bold text-slate-900 mb-2">Preparing your dashboard</h2>
      <p className="text-slate-600">Checking your account data to decide the best starting view...</p>
    </div>
  )

  const renderGoal = () => (
    <motion.div
      key="goal"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <GoalForecaster ephemeralTransactions={ephemeralTransactions} />
    </motion.div>
  )

  const contentByTab = {
    overview: renderOverview(),
    forecast: renderForecast(),
    sandbox: renderSandbox(),
    goal: renderGoal(),
    settings: isAuthenticated ? renderSettings() : renderOverview(),
  }

  return (
    <div className="postauth-bg relative flex h-screen overflow-hidden">
      <div className="grain-overlay" />
      <aside className={`dashboard-sidebar hidden md:flex h-full shrink-0 flex-col overflow-hidden bg-white/75 backdrop-blur-sm text-slate-900 border-r border-white/70 transition-all duration-300 relative z-10 ${isMenuCollapsed ? 'w-20' : 'w-72'}`}>
        <div className="h-16 px-4 flex items-center justify-between border-b border-white/10">
          {!isMenuCollapsed && <p className="font-display text-xl">Liquidity Radar</p>}
          <button onClick={() => setIsMenuCollapsed((v) => !v)} className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition">
            {isMenuCollapsed ? <FiChevronRight /> : <FiChevronLeft />}
          </button>
        </div>

        <div className="p-3 space-y-1">
          {MENU_ITEMS.map((item) => (
            <MenuButton key={item.id} item={item} isMenuCollapsed={isMenuCollapsed} onClick={() => setMobileMenuOpen(false)} />
          ))}
        </div>

        <div className="mt-auto p-3 border-t border-slate-200 space-y-2">
          {isAuthenticated ? (
            <>
              <MenuButton item={SETTINGS_ITEM} isMenuCollapsed={isMenuCollapsed} onClick={() => setMobileMenuOpen(false)} />
              <button onClick={handleSignOut} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-red-100 text-left text-red-700">
                <FiLogOut size={18} />
                {!isMenuCollapsed && <span>Sign Out</span>}
              </button>
            </>
          ) : (
            <button onClick={handleExitDemo} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100 text-left text-slate-700">
              <FiLogOut size={18} />
              {!isMenuCollapsed && <span>Exit Demo</span>}
            </button>
          )}
        </div>
      </aside>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-30 md:hidden bg-black/45" onClick={() => setMobileMenuOpen(false)}>
          <div className="dashboard-sidebar w-64 h-full bg-white text-slate-900 p-4" onClick={(e) => e.stopPropagation()}>
            <p className="font-display text-xl mb-4">Liquidity Radar</p>
            <div className="space-y-1">
              {[...MENU_ITEMS, ...(isAuthenticated ? [SETTINGS_ITEM] : [])].map((item) => (
                <NavLink
                  key={item.id}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `menu-button w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left block ${isActive ? 'menu-button-active' : ''}`
                  }
                  end={item.path === '/dashboard'}
                >
                  <item.icon size={18} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
            {isAuthenticated ? (
              <button onClick={handleSignOut} className="mt-5 w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-red-100 text-left text-red-700">
                <FiLogOut size={18} />
                <span>Sign Out</span>
              </button>
            ) : (
              <button onClick={handleExitDemo} className="mt-5 w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100 text-left text-slate-700">
                <FiLogOut size={18} />
                <span>Exit Demo</span>
              </button>
            )}
          </div>
        </div>
      )}

      <main className="relative z-10 flex h-full min-w-0 flex-1 flex-col overflow-y-auto">
        <div className="dashboard-topbar h-16 px-4 md:px-8 bg-white/70 backdrop-blur border-b border-white/70 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileMenuOpen(true)} className="md:hidden p-2 rounded-lg border border-gray-200">
              <FiMenu />
            </button>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Dashboard</p>
              <p className="font-semibold text-gray-900 capitalize">{currentTab === 'overview' ? 'Overview' : currentTab}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              className="rounded-full px-3 py-1 text-sm border border-slate-300 bg-white"
              title="Demo persona"
            >
              {PERSONAS.map((p) => (
                <option key={p} value={p}>{p[0].toUpperCase() + p.slice(1)}</option>
              ))}
            </select>
            <div className="rounded-full px-3 py-1 text-sm bg-lime-100 text-lime-800 border border-lime-200">{greenZoneStreak}-day green zone streak</div>
            <div className={`weather-pill weather-${liquidity.weatherKey} rounded-full px-3 py-1 text-sm border ${liquidity.weatherClass}`}>
              Financial Weather: {liquidity.weather}
            </div>
          </div>
        </div>

        <div className={contentContainerClass}>
          {isAuthenticated && isTransactionCheckLoading
            ? renderTransactionCheck()
            : isAuthenticated && hasTransactions === false
              ? renderFirstUploadStep()
              : (contentByTab[currentTab] || contentByTab.overview)}
        </div>
      </main>
    </div>
  )
}
