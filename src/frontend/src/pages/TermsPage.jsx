import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

const terms = [
  {
    title: 'Service Scope',
    content:
      'Liquidity Radar provides forecast guidance for educational and planning purposes. It is not financial advice.',
  },
  {
    title: 'Data Handling',
    content:
      'We process transaction signals to compute forecasts. Sensitive credentials are never exposed on the client.',
  },
  {
    title: 'Account Responsibility',
    content:
      'Users are responsible for reviewing forecasts before taking financial actions. Scenario outcomes are probabilistic.',
  },
  {
    title: 'Demo Environment',
    content:
      'Hackathon demo mode may use synthetic data and mocked integration responses to show the full product flow.',
  },
]

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-light to-gray-50 py-16">
      <div className="max-w-4xl mx-auto px-4">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-3">Legal</p>
          <h1 className="font-display text-5xl text-gray-900 mb-3">Terms & Conditions</h1>
          <p className="text-gray-600">Clear, transparent terms for using Liquidity Radar.</p>
        </motion.div>

        <div className="space-y-5 mb-10">
          {terms.map((item, idx) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.06 }}
              className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm"
            >
              <h2 className="text-xl font-semibold mb-2">{item.title}</h2>
              <p className="text-gray-700">{item.content}</p>
            </motion.div>
          ))}
        </div>

        <div className="flex flex-wrap gap-3">
          <Link to="/privacy" className="btn-secondary">Read Privacy</Link>
          <Link to="/signin" className="btn-primary">Back to Sign In</Link>
        </div>
      </div>
    </div>
  )
}