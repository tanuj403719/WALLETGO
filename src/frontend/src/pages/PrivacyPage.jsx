import { motion } from 'framer-motion'

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
  return (
    <div className="postauth-bg relative overflow-hidden py-14 md:py-20">
      <div className="grain-overlay" />

      <div className="max-w-6xl mx-auto px-4 relative z-10 text-slate-900">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-14"
        >
          <h1 className="font-display text-5xl md:text-6xl leading-[0.93] mb-4 text-slate-900">
            Privacy & Security,
            <span className="block text-teal-700">Without Legal Fog</span>
          </h1>
          <p className="text-slate-600 text-lg max-w-2xl mx-auto">
            Your financial timeline is sensitive. Radar keeps control transparent, consent-driven, and auditable.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 mb-10">
          {sections.map((section, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.08 }}
              viewport={{ once: true }}
              className="glass-card p-6"
            >
              <h2 className="text-2xl font-bold mb-4 text-slate-900">{section.title}</h2>
              <ul className="space-y-3">
                {section.points.map((point, i) => (
                  <li key={i} className="text-slate-700 flex items-start">
                    <span className="mr-3">{point.split(' ')[0]}</span>
                    <span>{point.substring(point.indexOf(' ') + 1)}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
