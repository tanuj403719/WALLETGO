import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

const sections = [
  {
    title: 'Bank-Grade Security',
    points: [
      '🔒 Read-only access to your transactions',
      '🛡️ No permanent storage of sensitive data',
      '🔐 End-to-end encryption for all communications',
      '✅ Regular security audits',
    ],
  },
  {
    title: 'Your Data',
    points: [
      '📊 Data processed locally on our secure servers',
      '❌ Never shared with third parties',
      '📝 Your preferences stored with PostgreSQL',
      '🗑️ Can delete your account and data anytime',
    ],
  },
  {
    title: 'Bank Integration',
    points: [
      '🏦 Uses NatWest Blue Bank API (sandbox for demo)',
      '🔗 OAuth 2.0 secure authentication',
      '⚙️ Real production uses only with NatWest',
      '🤝 Fully compliant with Open Banking standards',
    ],
  },
  {
    title: 'No Unexpected Charges',
    points: [
      '💰 Transparent pricing model',
      '🚫 No hidden fees or data sales',
      '🤝 Optional premium features clearly marked',
      '⏰ Cancel subscription anytime, no penalties',
    ],
  },
]

export default function PrivacyPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-light to-gray-50 py-20">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl font-bold mb-4">Privacy & Security</h1>
          <p className="text-xl text-gray-600">
            We're transparent about how we handle your financial data.
          </p>
        </motion.div>

        {/* Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {sections.map((section, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              viewport={{ once: true }}
              className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition"
            >
              <h2 className="text-2xl font-bold mb-4 text-primary">{section.title}</h2>
              <ul className="space-y-3">
                {section.points.map((point, i) => (
                  <li key={i} className="text-gray-700 flex items-start">
                    <span className="mr-3">{point.split(' ')[0]}</span>
                    <span>{point.substring(point.indexOf(' ') + 1)}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Important Note */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-lg mb-12"
        >
          <h3 className="text-lg font-bold text-blue-900 mb-2">For Hackathon Judges</h3>
          <p className="text-blue-800">
            During the hackathon, we use demo data and NatWest's sandbox API. In production, this would connect to your real NatWest account with the same security standards. You maintain full control and can revoke access anytime.
          </p>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center bg-primary text-white rounded-xl p-8"
        >
          <h2 className="text-3xl font-bold mb-4">Ready to build your financial future?</h2>
          <p className="text-white/90 mb-6">By continuing, you agree to Radar privacy terms and data handling policy.</p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => navigate('/bank-linking')}
              className="bg-white text-primary px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
            >
              I Agree, Continue
            </button>
            <button
              onClick={() => navigate('/signin')}
              className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition"
            >
              Back to Sign In
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
