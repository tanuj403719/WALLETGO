import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { FiChevronLeft, FiChevronRight, FiGrid, FiAlertTriangle, FiTarget, FiActivity, FiLogOut, FiMenu } from 'react-icons/fi'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { forecastAPI, scenarioAPI } from '../utils/api'

const DEFAULT_FORECAST = [
  { date: '1 May', rawDate: '2024-05-01', balance: 3500, low: 3200, high: 3800, baseline: 3550 },
  { date: '8 May', rawDate: '2024-05-08', balance: 3200, low: 2900, high: 3600, baseline: 3480 },
  { date: '15 May', rawDate: '2024-05-15', balance: 4800, low: 4400, high: 5200, baseline: 3400 },
  { date: '22 May', rawDate: '2024-05-22', balance: 4200, low: 3800, high: 4700, baseline: 3320 },
  { date: '29 May', rawDate: '2024-05-29', balance: 3900, low: 3400, high: 4500, baseline: 3250 },
  { date: '5 Jun', rawDate: '2024-06-05', balance: 4500, low: 4000, high: 5100, baseline: 3180 },
  { date: '12 Jun', rawDate: '2024-06-12', balance: 4100, low: 3600, high: 4700, baseline: 3100 },
]

function formatDateLabel(rawDate) {
  const parsed = new Date(rawDate)
  if (Number.isNaN(parsed.getTime())) return rawDate
  return parsed.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
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

function computeLiquidityScore(minBalance) {
  if (minBalance >= 2500) return { score: 88, label: 'Smooth sailing for 6 weeks' }
  if (minBalance >= 1000) return { score: 68, label: 'Caution: Tight spot ahead' }
  return { score: 38, label: 'Action needed this week' }
}

export default function DashboardPage() {
  const [language, setLanguage] = useState('en')
  const [showBaseline, setShowBaseline] = useState(false)
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [scenarioInput, setScenarioInput] = useState('')
  const [forecastRows, setForecastRows] = useState(DEFAULT_FORECAST)
  const [scenarioRows, setScenarioRows] = useState({ low: [], likely: [], high: [] })
  const [isScenarioActive, setIsScenarioActive] = useState(false)
  const [isScenarioRunning, setIsScenarioRunning] = useState(false)
  const [isForecastLoading, setIsForecastLoading] = useState(true)
  const [confidence, setConfidence] = useState(72)
  const [minBalance, setMinBalance] = useState(2120)
  const [minBalanceDate, setMinBalanceDate] = useState('May 8')
  const [scenarioNote, setScenarioNote] = useState('Try a scenario to overlay low/likely/high dotted lines on the graph.')
  const { signOut } = useAuth()
  const navigate = useNavigate()

  const texts = {
    en: { placeholder: "What happens if I...", examples: ["$500 flight", "Skip coffee 2 weeks", "Payday 3 days late"] },
    hi: { placeholder: "यदि मैं...", examples: ["$500 फ्लाइट", "2 सप्ताह कॉफी छोड़ें", "3 दिन देर से तनख्वाह"] },
    hinglish: { placeholder: "Agar main...", examples: ["$500 ka flight book karoo", "2 hafte coffee skip karoo", "Salary 3 din late ho"] },
  }

  const menuItems = [
    { id: 'overview', icon: FiGrid, label: 'Overview' },
    { id: 'forecast', icon: FiActivity, label: 'Forecast' },
    { id: 'sandbox', icon: FiTarget, label: 'What-If Sandbox' },
    { id: 'alerts', icon: FiAlertTriangle, label: 'Alerts' },
  ]

  const liquidity = useMemo(() => computeLiquidityScore(minBalance), [minBalance])

  useEffect(() => {
    const loadForecast = async () => {
      setIsForecastLoading(true)
      try {
        const response = await forecastAPI.getCurrent()
        const payload = response.data || {}
        const normalizedRows = normalizeForecastRows(payload.forecast_data)
        setForecastRows(normalizedRows)
        setConfidence(toNumber(payload.confidence, 72))
        setMinBalance(toNumber(payload.min_balance, normalizedRows.reduce((m, r) => Math.min(m, r.balance), normalizedRows[0].balance)))
        setMinBalanceDate(formatDateLabel(payload.min_balance_date || normalizedRows[0].rawDate))
      } catch (error) {
        toast.error('Could not load live forecast, showing demo data')
      } finally {
        setIsForecastLoading(false)
      }
    }

    loadForecast()
  }, [])

  const scenarioData = useMemo(() => {
    const lowMap = new Map(scenarioRows.low.map((row) => [row.date, toNumber(row.balance, null)]))
    const likelyMap = new Map(scenarioRows.likely.map((row) => [row.date, toNumber(row.balance, null)]))
    const highMap = new Map(scenarioRows.high.map((row) => [row.date, toNumber(row.balance, null)]))

    return forecastRows.map((row, idx) => {
      const lowByDate = lowMap.get(row.rawDate)
      const likelyByDate = likelyMap.get(row.rawDate)
      const highByDate = highMap.get(row.rawDate)

      const lowByIndex = scenarioRows.low[idx] ? toNumber(scenarioRows.low[idx].balance, row.balance) : null
      const likelyByIndex = scenarioRows.likely[idx] ? toNumber(scenarioRows.likely[idx].balance, row.balance) : null
      const highByIndex = scenarioRows.high[idx] ? toNumber(scenarioRows.high[idx].balance, row.balance) : null

      return {
        ...row,
        scenarioLow: lowByDate ?? lowByIndex ?? row.balance,
        scenarioLikely: likelyByDate ?? likelyByIndex ?? row.balance,
        scenarioHigh: highByDate ?? highByIndex ?? row.balance,
      }
    })
  }, [forecastRows, scenarioRows])

  const handleSignOut = async () => {
    await signOut()
    navigate('/signin')
  }

  const evaluateScenario = async (text) => {
    const trimmed = (text || '').trim()
    if (!trimmed) {
      toast.error('Enter a scenario first')
      return
    }

    setIsScenarioRunning(true)
    try {
      const response = await scenarioAPI.analyze(trimmed, language)
      const payload = response.data || {}
      const lowRows = payload.low?.forecast_data || []
      const likelyRows = payload.likely?.forecast_data || []
      const highRows = payload.high?.forecast_data || []

      if (!lowRows.length || !likelyRows.length || !highRows.length) {
        toast.error('Scenario response was incomplete')
        return
      }

      setScenarioRows({ low: lowRows, likely: likelyRows, high: highRows })
      setIsScenarioActive(true)
      setScenarioNote(payload.explanation || 'Scenario applied successfully.')
      toast.success('Scenario updated on chart')
    } catch (error) {
      toast.error('Failed to run scenario. Please try again.')
    } finally {
      setIsScenarioRunning(false)
    }
  }

  const jumpTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setMobileMenuOpen(false)
  }

  const handleMoveBill = () => {
    const preset = 'Payday 3 days late'
    setScenarioInput(preset)
    evaluateScenario(preset)
    toast.success('Applied suggested scenario')
    jumpTo('sandbox')
  }

  return (
    <div className="min-h-screen bg-[#edf2f5] flex">
      <aside
        className={`hidden md:flex flex-col bg-[#071922] text-white border-r border-white/10 transition-all duration-300 ${
          isMenuCollapsed ? 'w-20' : 'w-72'
        }`}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-white/10">
          {!isMenuCollapsed && <p className="font-display text-xl">Liquidity Radar</p>}
          <button
            onClick={() => setIsMenuCollapsed((v) => !v)}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
          >
            {isMenuCollapsed ? <FiChevronRight /> : <FiChevronLeft />}
          </button>
        </div>

        <div className="p-3 space-y-1">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => jumpTo(item.id)}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 text-left"
            >
              <item.icon size={18} />
              {!isMenuCollapsed && <span>{item.label}</span>}
            </button>
          ))}
        </div>

        <div className="mt-auto p-3 border-t border-white/10">
          <button
            onClick={handleSignOut}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-red-500/20 text-left"
          >
            <FiLogOut size={18} />
            {!isMenuCollapsed && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-30 md:hidden bg-black/45" onClick={() => setMobileMenuOpen(false)}>
          <div className="w-64 h-full bg-[#071922] text-white p-4" onClick={(e) => e.stopPropagation()}>
            <p className="font-display text-xl mb-4">Liquidity Radar</p>
            <div className="space-y-1">
              {menuItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => jumpTo(item.id)}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 text-left"
                >
                  <item.icon size={18} />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
            <button
              onClick={handleSignOut}
              className="mt-5 w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-red-500/20 text-left"
            >
              <FiLogOut size={18} />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}

      <main className="flex-1 min-w-0">
        <div className="h-16 px-4 md:px-8 bg-white border-b border-gray-200 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg border border-gray-200"
            >
              <FiMenu />
            </button>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Dashboard</p>
              <p className="font-semibold text-gray-900">May 2024 • Demo Account</p>
            </div>
          </div>
          <div className="rounded-full px-3 py-1 text-sm bg-green-100 text-green-700">Financial Weather: Sunny</div>
        </div>

        <div className="max-w-7xl mx-auto p-4 md:p-8">
          <div id="overview" className="grid lg:grid-cols-3 gap-5 mb-8">
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
              <p className="text-sm text-gray-500 mb-2">Liquidity Score</p>
              <p className="text-4xl font-bold text-[#0f766e]">{liquidity.score}</p>
              <p className="text-sm text-gray-600 mt-2">{liquidity.label}</p>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
              <p className="text-sm text-gray-500 mb-2">Min 30-Day Balance</p>
              <p className="text-4xl font-bold text-[#b45309]">${Math.round(minBalance).toLocaleString()}</p>
              <p className="text-sm text-gray-600 mt-2">Expected on {minBalanceDate}</p>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
              <p className="text-sm text-gray-500 mb-2">Confidence</p>
              <p className="text-4xl font-bold text-[#1d4ed8]">{Math.round(confidence)}%</p>
              <p className="text-sm text-gray-600 mt-2">Lower due to unusual spending last month</p>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
            {/* Liquidity Gauge Component */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6"
            >
              <h2 className="text-2xl font-bold mb-6">Liquidity Score</h2>
              <div className="flex items-center justify-center">
                <div className="relative w-48 h-48 mx-auto">
                  <svg viewBox="0 0 200 120" className="w-full h-full">
                    {/* Gauge background */}
                    <path d="M 20 100 A 80 80 0 0 1 180 100" stroke="#e5e7eb" strokeWidth="20" fill="none" />
                    {/* Red arc (0-33) */}
                    <path d="M 20 100 A 80 80 0 0 1 73 28" stroke="#dc2626" strokeWidth="20" fill="none" />
                    {/* Yellow arc (33-66) */}
                    <path d="M 73 28 A 80 80 0 0 1 127 28" stroke="#ea580c" strokeWidth="20" fill="none" />
                    {/* Green arc (66-100) */}
                    <path d="M 127 28 A 80 80 0 0 1 180 100" stroke="#16a34a" strokeWidth="20" fill="none" />
                    {/* Needle */}
                    <line x1="100" y1="100" x2="130" y2="50" stroke="#1f2937" strokeWidth="3" strokeLinecap="round" />
                    {/* Center dot */}
                    <circle cx="100" cy="100" r="4" fill="#1f2937" />
                  </svg>
                </div>
              </div>
              <div className="text-center mt-6">
                <div className="text-5xl font-bold text-secondary mb-2">{liquidity.score}</div>
                <p className="text-gray-600 text-lg">{liquidity.label}</p>
                <p className="text-sm text-gray-500 mt-2">Min balance (30d): <strong>${Math.round(minBalance).toLocaleString()}</strong> on {minBalanceDate}</p>
              </div>
            </motion.div>

            {/* Forecast Graph */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              id="forecast"
              className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">6-Week Forecast</h2>
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
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={scenarioData}>
                  <defs>
                    <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value) => `$${value}`} />
                  <Area type="monotone" dataKey="balance" stroke="#2563eb" strokeWidth={3} fillOpacity={1} fill="url(#colorBalance)" />
                  {isScenarioActive && (
                    <>
                      <Line type="monotone" dataKey="scenarioLow" stroke="#ef4444" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="scenarioLikely" stroke="#111827" strokeDasharray="5 5" strokeWidth={2.4} dot={false} />
                      <Line type="monotone" dataKey="scenarioHigh" stroke="#16a34a" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                    </>
                  )}
                  {showBaseline && (
                    <Line
                      type="monotone"
                      dataKey="baseline"
                      stroke="#9ca3af"
                      strokeDasharray="6 6"
                      strokeWidth={2}
                      dot={false}
                    />
                  )}
                </AreaChart>
              </ResponsiveContainer>
              <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                <div>💰 Payday: May 5</div>
                <div>📅 Rent: May 1</div>
                <div>🎬 Netflix: May 10</div>
              </div>
              {isForecastLoading && <p className="mt-4 text-sm text-gray-500">Loading live forecast...</p>}
            </motion.div>

            {/* Early Warnings */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              id="alerts"
              className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6"
            >
              <h2 className="text-2xl font-bold mb-4">⚠️ Early Warnings</h2>
              <div className="space-y-3">
                <div className="border-l-4 border-red-500 bg-red-50 p-4 rounded">
                  <p className="font-semibold text-red-900">Overdraft Risk on May 8</p>
                  <p className="text-sm text-red-800">Rent ($1500) + Netflix ($15) cluster. Balance drops to $2,120.</p>
                  <button onClick={handleMoveBill} className="text-sm text-red-700 font-semibold mt-2 hover:underline">Move bill →</button>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Sidebar (Right) */}
          <div className="space-y-8">
            {/* What-If Sandbox */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              id="sandbox"
              className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6"
            >
              <h2 className="text-xl font-bold mb-4">💡 What-If Sandbox</h2>
              
              {/* Language toggle */}
              <div className="flex gap-2 mb-4">
                {[
                  { code: 'en', label: '🌐 English' },
                  { code: 'hinglish', label: '🇮🇳 Hinglish' },
                  { code: 'hi', label: '🇭🇰 Hindi' },
                ].map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setLanguage(lang.code)}
                    className={`px-3 py-1 rounded text-sm font-medium transition ${
                      language === lang.code
                        ? 'bg-primary text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>

              {/* Input */}
              <input
                type="text"
                value={scenarioInput}
                onChange={(e) => setScenarioInput(e.target.value)}
                placeholder={texts[language].placeholder}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none mb-4"
              />

              <button
                onClick={() => evaluateScenario(scenarioInput)}
                disabled={isScenarioRunning}
                className="w-full mb-4 py-2.5 rounded-lg bg-[#042132] text-white font-medium hover:bg-[#073047] transition"
              >
                {isScenarioRunning ? 'Running...' : 'Run Scenario'}
              </button>

              {/* Examples */}
              <div className="space-y-2">
                {texts[language].examples.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setScenarioInput(example)
                      evaluateScenario(example)
                    }}
                    className="w-full text-left px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded text-sm font-medium transition truncate"
                  >
                    {example}
                  </button>
                ))}
              </div>

              <p className="mt-4 text-sm text-gray-600">{scenarioNote}</p>
            </motion.div>

            {/* Confidence Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-gradient-to-br from-[#042132] to-[#0b4a5f] text-white rounded-2xl shadow-sm p-6"
            >
              <h3 className="font-semibold mb-2">Confidence Level</h3>
              <p className="text-3xl font-bold mb-2">{Math.round(confidence)}%</p>
              <p className="text-sm text-white/80">
                Lower due to unusual spending pattern last month
              </p>
            </motion.div>

            {/* Account Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-white rounded-2xl border border-gray-200 p-6"
            >
              <h3 className="font-semibold mb-3">Account</h3>
              <p className="text-sm text-gray-700 mb-3">demo@radar.com</p>
              <button onClick={handleSignOut} className="w-full btn-secondary py-2 text-sm">Sign Out</button>
            </motion.div>
          </div>
        </div>
      </div>
      </main>
    </div>
  )
}
