import { useQuery } from '@tanstack/react-query'
import { Settings as SettingsIcon, Loader2 } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../store/authStore'

interface Setting {
  value: string
  is_encrypted: boolean
  description: string
}

export default function SettingsPage() {
  const { isAdmin } = useAuthStore()
  const { data, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const { data } = await api.get('/settings/')
      return data as Record<string, Setting>
    },
    enabled: isAdmin(),
  })

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Application configuration</p>
      </div>

      {!isAdmin() ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-700">
          Admin role required to view settings.
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-5 border-b">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <SettingsIcon className="w-5 h-5 text-gray-400" />
              Current Configuration
            </h2>
          </div>
          <div className="divide-y">
            {data && Object.entries(data).length > 0 ? (
              Object.entries(data).map(([key, setting]) => (
                <div key={key} className="px-5 py-3 flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium text-gray-700">{key}</p>
                    {setting.description && (
                      <p className="text-xs text-gray-400 mt-0.5">{setting.description}</p>
                    )}
                  </div>
                  <span className="text-sm text-gray-500 font-mono">
                    {setting.value}
                    {setting.is_encrypted && ' 🔒'}
                  </span>
                </div>
              ))
            ) : (
              <p className="px-5 py-8 text-center text-gray-400 text-sm">
                No settings configured yet.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
