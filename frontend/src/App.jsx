import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import WeekCalendar from './pages/WeekCalendar'
import Transactions from './pages/Transactions'
import Loans from './pages/Loans'
import Budget from './pages/Budget'
import Import from './pages/Import'
import Reports from './pages/Reports'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen"><div className="text-xl">Loading...</div></div>
  if (!user) return <Navigate to="/login" />
  return children
}

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/calendar', label: 'Calendar', icon: '📅' },
  { path: '/transactions', label: 'Transactions', icon: '💳' },
  { path: '/loans', label: 'Loans', icon: '🏦' },
  { path: '/budget', label: 'Budget', icon: '📋' },
  { path: '/import', label: 'Import', icon: '📤' },
  { path: '/reports', label: 'Reports', icon: '📈' },
]

function Layout({ children }) {
  const { logout, user } = useAuth()
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-gray-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <span className="text-2xl">🐵</span>
              <span className="font-bold text-lg">Stop The Monkey</span>
            </Link>
            <div className="hidden md:flex items-center gap-1">
              {NAV_ITEMS.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  {item.icon} {item.label}
                </Link>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400">{user?.username}</span>
              <button
                onClick={logout}
                className="text-sm text-gray-400 hover:text-white"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
        {/* Mobile nav */}
        <div className="md:hidden flex overflow-x-auto px-2 pb-2 gap-1">
          {NAV_ITEMS.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-1 rounded-md text-xs whitespace-nowrap ${
                location.pathname === item.path
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400'
              }`}
            >
              {item.icon} {item.label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={
        <ProtectedRoute>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/calendar" element={<WeekCalendar />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/loans" element={<Loans />} />
              <Route path="/budget" element={<Budget />} />
              <Route path="/import" element={<Import />} />
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </Layout>
        </ProtectedRoute>
      } />
    </Routes>
  )
}
