import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import {
  LayoutDashboard, PlayCircle, FileText,
  Settings, Users, LogOut, Shield
} from 'lucide-react'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analysis',  icon: PlayCircle,      label: 'Analysis' },
  { to: '/reports',   icon: FileText,        label: 'Reports' },
  { to: '/settings',  icon: Settings,        label: 'Settings' },
  { to: '/users',     icon: Users,           label: 'Users', adminOnly: true },
]

export default function Layout() {
  const { user, logout, isAdmin } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-64 bg-primary-800 text-white flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-primary-700">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-300" />
            <div>
              <div className="font-bold text-sm leading-tight">vSphere Compliance</div>
              <div className="text-xs text-blue-300">Manager</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {nav.map(({ to, icon: Icon, label, adminOnly }) => {
            if (adminOnly && !isAdmin()) return null
            return (
              <NavLink
                key={to} to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-blue-200 hover:bg-primary-700 hover:text-white'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                {label}
              </NavLink>
            )
          })}
        </nav>

        {/* User */}
        <div className="px-4 py-4 border-t border-primary-700">
          <div className="text-xs text-blue-300 mb-1">{user?.full_name || user?.username}</div>
          <div className="flex items-center justify-between">
            <span className="text-xs bg-primary-600 px-2 py-0.5 rounded capitalize">{user?.role}</span>
            <button onClick={handleLogout} className="text-blue-300 hover:text-white transition-colors">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
