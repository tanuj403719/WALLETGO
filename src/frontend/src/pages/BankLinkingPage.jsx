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
    <div className="postauth-bg relative overflow-hidden py-14 md:py-20">
      <div className="grain-overlay" />

      <div className="max-w-6xl mx-auto px-4 relative z-10 text-slate-900">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <p className="accent-pill mb-4">Step 2 of 3</p>
          <h1 className="font-display text-5xl md:text-6xl mb-4 leading-[0.92] text-slate-900">
            Choose Your
            <span className="block text-sky-700">Data Path</span>
          </h1>
          <p className="text-slate-600 text-lg max-w-2xl mx-auto">
            Pick the flow that matches your demo style. Both options unlock the full Radar dashboard.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 md:gap-8 mb-10">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={() => setSelected('real')}
            className={`glass-card p-8 cursor-pointer transition-all duration-200 ${
              selected === 'real'
                ? 'ring-2 ring-cyan-300/80'
                : 'hover:ring-2 hover:ring-cyan-200/60'
            }`}
          >
            <div className="text-5xl mb-4">🏦</div>
            <h2 className="text-2xl font-bold mb-3 text-slate-900">Connect NatWest Account</h2>
            <p className="text-slate-600 mb-6">
              Secure bank-link simulation with realistic transaction sync and stronger personalization.
            </p>
            <ul className="space-y-2 mb-6 text-sm text-slate-700">
              <li>Read-only connection model</li>
              <li>Last 3 months transaction ingest</li>
              <li>Continuous refresh behavior</li>
              <li>Highest fidelity forecasting</li>
            </ul>
            <button onClick={handleConnectReal} className="w-full py-3 primary-cta">
              Continue with NatWest
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={() => setSelected('demo')}
            className={`glass-card p-8 cursor-pointer transition-all duration-200 ${
              selected === 'demo'
                ? 'ring-2 ring-orange-300/80'
                : 'hover:ring-2 hover:ring-orange-200/60'
            }`}
          >
            <div className="text-5xl mb-4">🎮</div>
            <h2 className="text-2xl font-bold mb-3 text-slate-900">Use Curated Demo Data</h2>
            <p className="text-slate-600 mb-6">
              Jump in instantly with polished synthetic data designed for judging and walkthroughs.
            </p>
            <ul className="space-y-2 mb-6 text-sm text-slate-700">
              <li>Immediate access</li>
              <li>No external setup needed</li>
              <li>All features enabled</li>
              <li>Ideal for rapid demo loops</li>
            </ul>
            <button onClick={handleDemoData} className="w-full py-3 rounded-xl font-semibold bg-gradient-to-r from-orange-500 to-amber-400 text-white hover:brightness-105 transition">
              Launch Demo Workspace
            </button>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-10"
        >
          <div className="glass-card p-8">
            <h2 className="text-2xl font-bold mb-2 text-slate-900">Or upload your bank statement</h2>
            <p className="text-slate-600 mb-6">
              No login required for demo mode. Upload CSV/PDF and we will generate an in-memory forecast instantly.
            </p>
            <StatementUploader onSuccess={() => navigate('/dashboard')} />
            <div className="soft-panel mt-4 p-3 rounded-lg text-sm text-slate-700">
              Supports NatWest, Monzo, Barclays, and most standard bank CSV exports
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="soft-panel px-6 py-5 text-amber-900"
        >
          <p>
            <strong>Hackathon tip:</strong> Demo mode is fastest for judges. You can switch to a real bank-linked flow later from Settings.
          </p>
        </motion.div>
      </div>
    </div>
  )
}
