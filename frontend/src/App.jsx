import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import DemoPage from './pages/DemoPage'
import SignInPage from './pages/SignInPage'
import PrivacyPage from './pages/PrivacyPage'
import TermsPage from './pages/TermsPage'
import BankLinkingPage from './pages/BankLinkingPage'
import DashboardPage from './pages/DashboardPage'
import { AuthProvider } from './context/AuthContext'
import { ForecastProvider } from './context/ForecastContext'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <ForecastProvider>
        <Router>
          <Navbar />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/demo" element={<DemoPage />} />
            <Route path="/signin" element={<SignInPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route
              path="/privacy"
              element={
                <ProtectedRoute>
                  <PrivacyPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bank-linking"
              element={
                <ProtectedRoute>
                  <BankLinkingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
          </Routes>
          <Toaster />
        </Router>
      </ForecastProvider>
    </AuthProvider>
  )
}

export default App
