import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

import StatementUploader from '../components/StatementUploader'

export default function BankLinkingPage() {
  const [selected, setSelected] = useState(null)
  const navigate = useNavigate()

  const handleConnectReal = () => {
    setSelected('real')
    toast.success('NatWest sandbox connection simulated')
    navigate('/dashboard')
  }

  const handleDemoData = () => {
    setSelected('demo')
    toast.success('Demo data selected')
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-light to-gray-50 py-20">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold mb-4">Connect Your Bank</h1>
          <p className="text-xl text-gray-600">
            Choose how you want to get started with Radar
          </p>
        </motion.div>

        {/* Options */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Option 1: Real Bank */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={() => setSelected('real')}
            className={`p-8 rounded-xl border-2 cursor-pointer transition ${
              selected === 'real'
                ? 'border-primary bg-blue-50'
                : 'border-gray-200 bg-white hover:border-primary'
            }`}
          >
            <div className="text-5xl mb-4">🏦</div>
            <h2 className="text-2xl font-bold mb-4">Connect NatWest Account</h2>
            <p className="text-gray-600 mb-6">
              Real transactions, real forecasts. We'll securely access your recent transaction history.
            </p>
            <ul className="space-y-2 mb-6 text-sm text-gray-700">
              <li>✅ Read-only access</li>
              <li>✅ Last 3 months of data</li>
              <li>✅ Real-time sync</li>
              <li>✅ Most accurate forecasts</li>
            </ul>
            <button onClick={handleConnectReal} className="w-full btn-primary py-2 font-semibold">
              Connect with NatWest
            </button>
          </motion.div>

          {/* Option 2: Demo Data */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={() => setSelected('demo')}
            className={`p-8 rounded-xl border-2 cursor-pointer transition ${
              selected === 'demo'
                ? 'border-primary bg-blue-50'
                : 'border-gray-200 bg-white hover:border-primary'
            }`}
          >
            <div className="text-5xl mb-4">🎮</div>
            <h2 className="text-2xl font-bold mb-4">Continue with Demo Data</h2>
            <p className="text-gray-600 mb-6">
              Try Radar with realistic synthetic data. Perfect for judges and quick demos.
            </p>
            <ul className="space-y-2 mb-6 text-sm text-gray-700">
              <li>✅ Instant access</li>
              <li>✅ No real data needed</li>
              <li>✅ Full feature access</li>
              <li>✅ Easy for judging</li>
            </ul>
            <button onClick={handleDemoData} className="w-full btn-primary py-2 font-semibold">
              Use Demo Account
            </button>
          </motion.div>
        </div>

        {/* Statement Upload */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-12"
        >
          <div className="glass-card p-8">
            <h2 className="text-2xl font-bold mb-2">Or upload your bank statement</h2>
            <p className="text-gray-600 mb-6">
              Have a CSV or PDF export from your bank? Upload it directly to see a personalised forecast.
            </p>
            <StatementUploader onSuccess={() => navigate('/dashboard')} />
            <div className="soft-panel mt-4 p-3 rounded-lg text-sm text-gray-600">
              Supports NatWest, Monzo, Barclays, and most standard bank CSV exports
            </div>
          </div>
        </motion.div>

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center"
        >
          <p className="text-amber-900">
            <strong>Pro tip:</strong> During the hackathon, most judges prefer the demo data option for faster iteration. You can always switch to real data later!
          </p>
        </motion.div>
      </div>
    </div>
  )
}
