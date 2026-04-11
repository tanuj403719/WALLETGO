import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { FiMenu, FiX } from 'react-icons/fi'

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  if (location.pathname === '/dashboard') {
    return null
  }

  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              📡 Radar
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              to="/"
              className={`${
                isActive('/') ? 'text-primary font-semibold' : 'text-gray-700'
              } hover:text-primary transition`}
            >
              About
            </Link>
            <Link
              to="/demo"
              className={`${
                isActive('/demo') ? 'text-primary font-semibold' : 'text-gray-700'
              } hover:text-primary transition`}
            >
              Demo
            </Link>
            <Link
              to="/privacy"
              className={`${
                isActive('/privacy') ? 'text-primary font-semibold' : 'text-gray-700'
              } hover:text-primary transition`}
            >
              Privacy
            </Link>
            <Link to="/signin" className="btn-primary">
              Sign In
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-gray-700"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden pb-4 space-y-2">
            <Link
              to="/"
              className="block px-4 py-2 text-gray-700 hover:text-primary"
            >
              About
            </Link>
            <Link
              to="/demo"
              className="block px-4 py-2 text-gray-700 hover:text-primary"
            >
              Demo
            </Link>
            <Link
              to="/privacy"
              className="block px-4 py-2 text-gray-700 hover:text-primary"
            >
              Privacy
            </Link>
            <Link
              to="/signin"
              className="block px-4 py-2 text-gray-700 hover:text-primary"
            >
              Sign In
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
