import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings as SettingsIcon, Plus, Trash2, Loader2, TestTube } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../store/authStore'

interface Setting {
  value: string
  is_encrypted: boolean
  description: string
}

interface Pattern {
  id: number
  name: string
  pattern_type: string
  regex_pattern: string
  description: string | null
  is_active: boolean
}

export default function SettingsPage() {
  const { isAdmin } = useAuthStore()
  const queryClient = useQueryClient()
  const [showPatternModal, setShowPatternModal] = useState(false)
  const [ldapTesting, setLdapTesting] = useState(false)

  // Fetch settings
  const { data: settings, isLoading: loadingSettings } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const { data } = await api.get('/settings/')
      return data as Record<string, Setting>
    },
    enabled: isAdmin(),
  })

  // Fetch patterns
  const { data: patterns, isLoading: loadingPatterns } = useQuery({
    queryKey: ['patterns'],
    queryFn: async () => {
      const { data } = await api.get('/settings/patterns')
      return data as Pattern[]
    },
  })

  // Create pattern mutation
  const createPattern = useMutation({
    mutationFn: async (payload: Partial<Pattern>) => {
      const { data } = await api.post('/settings/patterns', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] })
      setShowPatternModal(false)
    },
  })

  // Delete pattern mutation
  const deletePattern = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/settings/patterns/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] })
    },
  })

  // Test LDAP mutation
  const testLdap = useMutation({
    mutationFn: async () => {
      setLdapTesting(true)
      const { data } = await api.post('/settings/ldap/test')
      return data
    },
    onSuccess: () => {
      alert('LDAP connection successful!')
    },
    onError: () => {
      alert('LDAP connection failed. Check your settings.')
    },
    onSettled: () => {
      setLdapTesting(false)
    },
  })

  const isLoading = loadingSettings || loadingPatterns

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
        <>
          {/* Patterns */}
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="p-5 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <SettingsIcon className="w-5 h-5 text-gray-400" />
                Compliance Patterns
              </h2>
              <button
                onClick={() => setShowPatternModal(true)}
                className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Pattern
              </button>
            </div>
            {!patterns || patterns.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                No patterns configured. Add patterns to match VMs and datastores.
              </div>
            ) : (
              <div className="divide-y">
                {patterns.map((pattern) => (
                  <div key={pattern.id} className="p-4 flex justify-between items-center hover:bg-gray-50">
                    <div>
                      <p className="font-medium text-gray-900">{pattern.name}</p>
                      <p className="text-sm text-gray-500 font-mono">{pattern.regex_pattern}</p>
                      {pattern.description && (
                        <p className="text-xs text-gray-400 mt-1">{pattern.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs bg-gray-100 px-2 py-0.5 rounded capitalize">
                        {pattern.pattern_type}
                      </span>
                      <button
                        onClick={() => deletePattern.mutate(pattern.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* LDAP Test */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TestTube className="w-5 h-5 text-gray-400" />
              LDAP Connection Test
            </h2>
            <button
              onClick={() => testLdap.mutate()}
              disabled={ldapTesting || testLdap.isPending}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {(ldapTesting || testLdap.isPending) && <Loader2 className="w-4 h-4 animate-spin" />}
              Test LDAP Connection
            </button>
          </div>

          {/* Application Settings */}
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="p-5 border-b">
              <h2 className="text-lg font-semibold">Current Configuration</h2>
            </div>
            <div className="divide-y">
              {settings && Object.entries(settings).length > 0 ? (
                Object.entries(settings).map(([key, setting]) => (
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
        </>
      )}

      {/* Add Pattern Modal */}
      {showPatternModal && (
        <AddPatternModal
          onClose={() => setShowPatternModal(false)}
          onSubmit={(data) => createPattern.mutate(data)}
          loading={createPattern.isPending}
        />
      )}
    </div>
  )
}

function AddPatternModal({ onClose, onSubmit, loading }: {
  onClose: () => void
  onSubmit: (data: any) => void
  loading: boolean
}) {
  const [form, setForm] = useState({
    name: '',
    pattern_type: 'vm_name',
    regex_pattern: '',
    description: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Add Pattern</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Web Servers" required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={form.pattern_type}
              onChange={(e) => setForm({ ...form, pattern_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="vm_name">VM Name</option>
              <option value="datastore">Datastore</option>
              <option value="role">Role</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Regex Pattern</label>
            <input
              type="text" value={form.regex_pattern} onChange={(e) => setForm({ ...form, regex_pattern: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono"
              placeholder="^(WEB)-" required
            />
            <p className="text-xs text-gray-400 mt-1">Standard JavaScript regex syntax</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
            <input
              type="text" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Matches all web servers"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button" onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit" disabled={loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Creating...' : 'Create Pattern'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
