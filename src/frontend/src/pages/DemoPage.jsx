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
    <div className="min-h-screen bg-gradient-to-br from-light to-gray-50 py-20">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold mb-4">See Radar in Action</h1>
          <p className="text-xl text-gray-600">
            No login required. Just a quick peek at what's possible.
          </p>
        </motion.div>

        {/* Demo Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl shadow-xl p-8 mb-8"
        >
          {/* Chart */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Your 6-Week Forecast</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={demoData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value}`} />
                <Line type="monotone" dataKey="balance" stroke="#2563eb" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* What-If Button */}
          <div className="text-center">
            <button
              onClick={() => setShowScenario(!showScenario)}
              className="btn-primary text-lg px-8 py-3"
            >
              💡 What if I buy a $500 flight?
            </button>
          </div>

          {/* Scenario Results */}
          {showScenario && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-8 pt-8 border-t border-gray-200"
            >
              <h3 className="text-xl font-semibold mb-6">Scenario Analysis</h3>
              
              <div className="grid md:grid-cols-3 gap-4">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-red-50 border-l-4 border-red-500 p-4 rounded"
                >
                  <div className="text-red-600 font-semibold mb-2">🔴 Pessimistic</div>
                  <p className="text-2xl text-red-700 font-bold mb-2">-$680</p>
                  <p className="text-sm text-gray-600">Lowest balance: $2,120 (May 8)</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 0 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded"
                >
                  <div className="text-yellow-600 font-semibold mb-2">🟡 Likely</div>
                  <p className="text-2xl text-yellow-700 font-bold mb-2">-$410</p>
                  <p className="text-sm text-gray-600">Lowest balance: $3,090 (May 8)</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  className="bg-green-50 border-l-4 border-green-500 p-4 rounded"
                >
                  <div className="text-green-600 font-semibold mb-2">🟢 Optimistic</div>
                  <p className="text-2xl text-green-700 font-bold mb-2">-$220</p>
                  <p className="text-sm text-gray-600">Lowest balance: $3,280 (May 8)</p>
                </motion.div>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200"
              >
                <p className="text-blue-900">
                  <strong>💡 AI Insight:</strong> If you book the flight today, you'll hit a tight spot on May 8th when rent is due. Consider booking for May 15th instead—you'd have $4,300 buffer and risk drops to just 12%.
                </p>
              </motion.div>
            </motion.div>
          )}
        </motion.div>

        {/* Ready CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-center bg-primary text-white rounded-xl p-8"
        >
          <h2 className="text-3xl font-bold mb-4">Ready for the full experience?</h2>
          <p className="text-lg mb-6 text-white/90">
            Sign up now and connect your real bank account to get personalized forecasts.
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => navigate('/signin?mode=signup')}
              className="bg-white text-primary px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
            >
              Sign Up Free
            </button>
            <button
              onClick={() => navigate('/signin?demo=1')}
              className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition"
            >
              Try Demo Account
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
