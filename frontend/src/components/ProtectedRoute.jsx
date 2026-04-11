import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-600">
        Loading your session...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" replace state={{ from: location }} />
  }

  return children
}