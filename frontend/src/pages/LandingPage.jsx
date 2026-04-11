import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function LandingPage() {
  const features = [
    {
      icon: 'Radar',
      title: '6-Week Liquidity Forecast',
      desc: 'Daily projected balance with confidence bands and event markers like payday, rent, and subscriptions.',
    },
    {
      icon: 'What-If',
      title: 'Scenario Sandbox',
      desc: 'Ask questions like "$500 flight today?" and see low, likely, and high outcomes instantly.',
    },
    {
      icon: 'Alerts',
      title: 'Early Warnings',
      desc: 'Proactive cards flag overdraft risk before it happens, with suggested actions to avoid crunch days.',
    },
    {
      icon: 'Languages',
      title: 'English + Hinglish + Hindi',
      desc: 'AI explanations stay in the same language the user typed, including colloquial Hinglish guidance.',
    },
  ]

  const movingStrip = [
    'Stop looking backwards. Start seeing your financial future.',
    'Forecast horizon: 42 days',
    'Scenario engine: Low / Likely / High',
    'Built for NatWest Code for Purpose',
    'Hinglish + Hindi + English support',
  ]

  return (
    <div className="relative min-h-screen overflow-hidden bg-radar-ink text-radar-paper">
      <div className="radar-aurora" aria-hidden="true" />

      <section className="border-b border-white/15 bg-black/20 backdrop-blur-sm">
        <div className="ticker-shell">
          <div className="ticker-track">
            {[...movingStrip, ...movingStrip].map((item, idx) => (
              <span className="ticker-item" key={`${item}-${idx}`}>
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 md:py-20">
        <div className="grid lg:grid-cols-2 gap-10 md:gap-14 items-center">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <p className="uppercase tracking-[0.22em] text-xs md:text-sm text-radar-accent mb-5">Personalized Liquidity Radar</p>
            <h1 className="font-display text-5xl sm:text-6xl md:text-7xl leading-[0.94] mb-6">
              Stop Looking Backwards.
              <span className="block text-radar-sand">Start Seeing Your Financial Future.</span>
            </h1>
            <p className="text-base md:text-lg text-radar-paper/85 leading-relaxed max-w-xl mb-8">
              Radar forecasts your next 6 weeks, catches tight spots early, and lets users simulate decisions before money actually moves.
            </p>

            <div className="flex flex-wrap gap-3 mb-8">
              <span className="chip">42-day projection</span>
              <span className="chip">Scenario forecasting</span>
              <span className="chip">Early warning alerts</span>
              <span className="chip">Hinglish/Hindi/English</span>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link to="/demo" className="btn-hero-primary">
                Open Demo
              </Link>
              <Link to="/signin" className="btn-hero-secondary">
                Sign In
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="relative"
          >
            <div className="dashboard-teaser">
              <div className="teaser-top">
                <p className="text-radar-paper/80 text-xs uppercase tracking-[0.2em]">Today Snapshot</p>
                <span className="teaser-badge">Likely: Stable</span>
              </div>
              <p className="font-display text-4xl md:text-5xl text-radar-sand mb-2">$3,920</p>
              <p className="text-radar-paper/75 mb-6">Min projected balance in 30 days</p>

              <div className="teaser-chart">
                <svg viewBox="0 0 420 170" className="w-full h-full" aria-hidden="true">
                  <defs>
                    <linearGradient id="lineGlow" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#d4e157" />
                      <stop offset="100%" stopColor="#64ffda" />
                    </linearGradient>
                  </defs>
                  <path d="M10 130 C 70 100, 120 145, 180 110 C 250 70, 300 125, 410 95" stroke="url(#lineGlow)" strokeWidth="5" fill="none" strokeLinecap="round" />
                  <path d="M10 145 C 70 120, 120 165, 180 128 C 250 88, 300 145, 410 112" stroke="rgba(255,255,255,0.24)" strokeWidth="2" fill="none" strokeDasharray="6 7" />
                </svg>
              </div>

              <div className="mt-6 grid grid-cols-3 gap-3 text-xs md:text-sm">
                <div className="teaser-pill">Payday +$4,000</div>
                <div className="teaser-pill">Rent -$1,500</div>
                <div className="teaser-pill">Netflix -$15</div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="relative py-10 md:py-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-display text-4xl md:text-5xl mb-8">What Makes Radar Judge-Friendly</h2>
          <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-5 md:gap-6">
            {features.map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 25 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.08, duration: 0.45 }}
                viewport={{ once: true }}
                className="feature-tile"
              >
                <p className="feature-kicker">{feature.icon}</p>
                <h3 className="text-2xl font-semibold mb-3 text-radar-paper">{feature.title}</h3>
                <p className="text-radar-paper/75 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-14 md:py-16">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="cta-panel">
            <p className="uppercase tracking-[0.2em] text-xs text-radar-ink/70 mb-4">Hackathon Launch Mode</p>
            <h2 className="font-display text-4xl md:text-5xl text-radar-ink mb-4">Ready to stress-test your money decisions?</h2>
            <p className="text-radar-ink/80 text-base md:text-lg mb-7">
              Try the demo in one click, then sign in to run your own what-if scenarios and watch the forecast react in real time.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/demo" className="btn-primary text-lg px-8 py-3">
                Try Interactive Demo
              </Link>
              <Link to="/signin" className="btn-secondary text-lg px-8 py-3">
                Create Account
              </Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10 bg-black/25 backdrop-blur-sm py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="font-semibold text-radar-paper">Liquidity Radar</p>
            <p className="text-sm text-radar-paper/70">Forecast engine for the next 6 weeks.</p>
          </div>
          <div className="flex items-center gap-6 text-sm text-radar-paper/75">
            <Link to="/privacy" className="hover:text-radar-paper">Privacy</Link>
            <Link to="/terms" className="hover:text-radar-paper">T&C</Link>
            <span>NatWest Code for Purpose</span>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 text-xs text-radar-paper/50">
          <p>
            Stop looking backwards. Start seeing your financial future.
          </p>
        </div>
      </footer>
    </div>
  )
}
