import { motion } from 'framer-motion'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const demoData = [
  { date: '1 May', balance: 3500 },
  { date: '8 May', balance: 3200 },
  { date: '15 May', balance: 4800 },
  { date: '22 May', balance: 4200 },
  { date: '29 May', balance: 3900 },
  { date: '5 Jun', balance: 4500 },
  { date: '12 Jun', balance: 4100 },
]

export default function DemoPage() {
  const [showScenario, setShowScenario] = useState(false)
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#03141d] text-white relative overflow-hidden py-20">
      <div className="absolute -top-20 -left-20 w-80 h-80 rounded-full bg-cyan-400/15 blur-3xl" />
      <div className="absolute -bottom-24 -right-20 w-96 h-96 rounded-full bg-lime-300/12 blur-3xl" />
      <div className="max-w-6xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold mb-4">See Radar in Action</h1>
          <p className="text-xl text-slate-300">
            No login required. Just a quick peek at what's possible.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl border border-white/15 bg-white/5 backdrop-blur-sm shadow-xl p-8 mb-8"
        >
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Your 6-Week Forecast</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={demoData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.28)" />
                <XAxis dataKey="date" stroke="#cbd5e1" />
                <YAxis stroke="#cbd5e1" />
                <Tooltip
                  formatter={(value) => `$${value}`}
                  contentStyle={{ background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(148,163,184,0.35)', borderRadius: '12px', color: '#e2e8f0' }}
                  labelStyle={{ color: '#cbd5e1' }}
                />
                <Line type="monotone" dataKey="balance" stroke="#38bdf8" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="text-center">
            <button
              onClick={() => setShowScenario(!showScenario)}
              className="btn-primary text-lg px-8 py-3"
            >
              💡 What if I buy a $500 flight?
            </button>
          </div>

          {showScenario && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-8 pt-8 border-t border-white/15"
            >
              <h3 className="text-xl font-semibold mb-6">Scenario Analysis</h3>

              <div className="grid md:grid-cols-3 gap-4">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-red-500/12 border-l-4 border-red-400 p-4 rounded"
                >
                  <div className="text-red-300 font-semibold mb-2">🔴 Pessimistic</div>
                  <p className="text-2xl text-red-200 font-bold mb-2">-$680</p>
                  <p className="text-sm text-slate-300">Lowest balance: $2,120 (May 8)</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 0 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-yellow-500/12 border-l-4 border-yellow-400 p-4 rounded"
                >
                  <div className="text-yellow-200 font-semibold mb-2">🟡 Likely</div>
                  <p className="text-2xl text-yellow-100 font-bold mb-2">-$410</p>
                  <p className="text-sm text-slate-300">Lowest balance: $3,090 (May 8)</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  className="bg-green-500/12 border-l-4 border-green-400 p-4 rounded"
                >
                  <div className="text-green-300 font-semibold mb-2">🟢 Optimistic</div>
                  <p className="text-2xl text-green-200 font-bold mb-2">-$220</p>
                  <p className="text-sm text-slate-300">Lowest balance: $3,280 (May 8)</p>
                </motion.div>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="mt-6 p-4 bg-sky-500/12 rounded-lg border border-sky-300/35"
              >
                <p className="text-sky-100">
                  <strong>💡 AI Insight:</strong> If you book the flight today, you'll hit a tight spot on May 8th when rent is due. Consider booking for May 15th instead—you'd have $4,300 buffer and risk drops to just 12%.
                </p>
              </motion.div>
            </motion.div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-center rounded-xl p-8 border border-white/20 bg-gradient-to-r from-cyan-500/20 to-lime-400/20"
        >
          <h2 className="text-3xl font-bold mb-4">Ready for the full experience?</h2>
          <p className="text-lg mb-6 text-white/90">
            Upload a statement in demo mode to get personalized forecasts without creating an account.
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => navigate('/bank-linking?mode=upload')}
              className="bg-white text-primary px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
            >
              Upload Statement Demo
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition"
            >
              Continue with Sample Data
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
