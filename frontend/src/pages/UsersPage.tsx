import { useQuery } from '@tanstack/react-query'
import { Users, Loader2, UserCheck, UserX } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../store/authStore'

interface User {
  id: number
  username: string
  full_name: string | null
  email: string | null
  role: string
  is_active: boolean
  is_ldap: boolean
  created_at: string | null
}

export default function UsersPage() {
  const { isAdmin } = useAuthStore()
  const { data, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await api.get('/users/')
      return data as User[]
    },
    enabled: isAdmin(),
  })

  if (!isAdmin()) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-700">
          Admin role required to manage users.
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <p className="text-gray-500 mt-1">Manage user accounts and roles</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
        </div>
      ) : !data || data.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No users found.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Username</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Full Name</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{user.username}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{user.full_name || '—'}</td>
                  <td className="px-4 py-3">
                    <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-gray-100 capitalize">
                      {user.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {user.is_ldap ? 'LDAP' : 'Local'}
                  </td>
                  <td className="px-4 py-3">
                    {user.is_active ? (
                      <span className="flex items-center gap-1 text-green-600 text-sm">
                        <UserCheck className="w-3 h-3" /> Active
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-500 text-sm">
                        <UserX className="w-3 h-3" /> Inactive
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
