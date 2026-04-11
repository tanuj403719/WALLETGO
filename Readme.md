# Personalized Liquidity Radar 🎯

An AI-powered financial forecasting tool for the NatWest Code for Purpose Hackathon that predicts your bank balance for the next 1-6 weeks with intelligent scenario forecasting.

## 🚀 Features

- **6-Week Liquidity Forecast**: AI-powered predictions using Prophet with confidence intervals
- **Scenario Forecasting**: "What if" analysis to explore outcomes of financial decisions
- **Multilingual Support**: English, Hinglish, and Hindi explanations powered by GPT-4o-mini
- **Real-time Alerts**: Early warnings about overdraft risks and bill clusters
- **NatWest Integration**: Secure bank data access via NatWest Blue Bank API (sandbox)
- **Interactive Visualizations**: Beautiful charts with Recharts and animations with Framer Motion

## 📋 Tech Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Framer Motion** - Animations
- **Supabase JS** - Authentication & DB client

### Backend
- **Python FastAPI** - API framework
- **SQLAlchemy** - ORM
- **Prophet** - Time series forecasting
- **OpenAI** - AI explanations
- **Supabase** - Auth & PostgreSQL database
- **NatWest API** - Bank data (sandbox)

## 🏗️ Project Structure

```
WALLETGO/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── context/         # Context providers
│   │   ├── utils/           # Utility functions
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/                  # Python FastAPI backend
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utilities
│   │   ├── __init__.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
│
├── configs/                  # Configuration files
├── .env.example
└── README.md
```

## 🚦 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL (via Supabase or local)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`

## 📱 User Flow

1. **Landing Page** - About & features overview
2. **Demo Tab** - Interactive teaser without login
3. **Sign In/Up** - Supabase authentication
4. **Privacy & T&C** - Transparency & opt-out
5. **Bank Linking** - Connect via NatWest (or demo data)
6. **Dashboard** - Main product with 6 components:
   - Liquidity Radar Gauge
   - Forecast Timeline Graph
   - What-If Sandbox
   - Early Warning Alerts
   - Baseline Comparison
   - Confidence Badge

## 🔑 Key Components

### Dashboard Components

#### 1. Liquidity Radar Gauge
Circular speedometer (0-100) showing financial health
- Green (80-100): "Smooth sailing"
- Yellow (50-79): "Caution!"
- Red (0-49): "Action needed"

#### 2. Forecast Timeline
6-week line chart with confidence bands and transaction icons

#### 3. What-If Sandbox
Ask in English/Hinglish/Hindi, see three scenario outcomes (Low/Likely/High)

#### 4. Early Warnings
Proactive alerts about overdraft risks and bill clusters

#### 5. Baseline Comparison
Toggle to show simple naive forecast vs. AI forecast

#### 6. Confidence Badge
Transparency about prediction certainty

## 🔐 Authentication

- **Supabase** for auth and PostgreSQL database
- **JWT tokens** for API security
- **Demo account** for quick testing: `demo@radar.com` / `demo123`

## 📊 Forecasting Logic

1. **Data Input**: Get last 3 months of transactions + recurring bills
2. **Feature Engineering**: Extract patterns, seasonality, recurring items
3. **Prophet Model**: Baseline forecast with confidence intervals
4. **Scenario Runtime**: Inject user's "what if" into model
5. **Explanation Gen**: Use GPT-4o-mini to explain in user's language

## 🏦 NatWest Integration

Using NatWest Blue Bank API (sandbox mode):
- Read-only transaction access
- No data stored permanently
- Opt-out anytime
- HTTPS + OAuth2 for security

## 📌 Environment Variables

See `.env.example` for complete setup. Key variables:

```env
VITE_SUPABASE_URL=<your-supabase-url>
VITE_SUPABASE_ANON_KEY=<anon-key>
OPENAI_API_KEY=<your-api-key>
NATWEST_API_KEY=<sandbox-key>
```

## 📈 Demo Data

Test account comes pre-loaded with 3 months of realistic synthetic transactions including:
- Monthly salary deposits
- Rent, utilities, subscriptions
- Grocery, dining, transport expenses
- Special spending events

## 🎯 Hackathon Focus

**Why we win:**
1. **Scenario Forecasting** - Users see outcomes before making decisions
2. **Multilingual Support** - Inclusive for diverse UK/India audience
3. **Real NatWest Integration** - Impressive tech depth
4. **Early Warnings** - Proactive, not reactive
5. **Beautiful UX** - Modern, engaging, delightful

## 🛠️ Development

### Running Tests

```bash
# Backend (when tests are added)
cd backend
pytest
```

### Building for Production

```bash
# Frontend
cd frontend
npm run build

# Backend
# Configure ENVIRONMENT=production in .env
```

## 📝 License

Built for NatWest Code for Purpose Hackathon 2024

## 👥 Team

Your team details here
