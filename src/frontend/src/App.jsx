import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import { ForecastProvider } from './context/ForecastContext'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import DemoPage from './pages/DemoPage'
import SignInPage from './pages/SignInPage'
import PrivacyPage from './pages/PrivacyPage'
import TermsPage from './pages/TermsPage'
import BankLinkingPage from './pages/BankLinkingPage'
import DashboardPage from './pages/DashboardPage'

export default function App() {
  useEffect(() => {
    const savedTheme = localStorage.getItem('radar_theme')
    const initialTheme = savedTheme || 'dark'
    document.documentElement.setAttribute('data-theme', initialTheme)
    if (!savedTheme) {
      localStorage.setItem('radar_theme', 'dark')
    }
  }, [])

  return (
    <BrowserRouter>
      <AuthProvider>
        <ForecastProvider>
          <Navbar />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/demo" element={<DemoPage />} />
            <Route path="/signin" element={<SignInPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/bank-linking" element={<BankLinkingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dashboard/forecast" element={<DashboardPage />} />
            <Route path="/dashboard/sandbox" element={<DashboardPage />} />
            <Route path="/dashboard/goal" element={<DashboardPage />} />
            <Route path="/dashboard/alerts" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard/settings"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
          </Routes>
          <Toaster position="top-right" />
        </ForecastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
