import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, PlayCircle, Loader2, RefreshCw, Server } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../store/authStore'

interface VCenterConnection {
  id: number
  name: string
  host: string
  port: number
  username: string
  verify_ssl: boolean
  is_active: boolean
  version: string | null
  last_connected: string | null
}

export default function AnalysisPage() {
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedVcenter, setSelectedVcenter] = useState<number | null>(null)
  const [analysisType, setAnalysisType] = useState('full')
  const { isOperator } = useAuthStore()
  const queryClient = useQueryClient()

  // Fetch vCenters
  const { data: vcenters, isLoading: loadingVcenters } = useQuery({
    queryKey: ['vcenters'],
    queryFn: async () => {
      const { data } = await api.get('/vcenter/')
      return data as VCenterConnection[]
    },
  })

  // Fetch analysis runs
  const { data: runsData, isLoading: loadingRuns } = useQuery({
    queryKey: ['analysis-runs'],
    queryFn: async () => {
      const { data } = await api.get('/analysis/?per_page=20')
      return data
    },
  })

  // Add vCenter mutation
  const addVcenter = useMutation({
    mutationFn: async (payload: Partial<VCenterConnection>) => {
      const { data } = await api.post('/vcenter/', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vcenters'] })
      setShowAddModal(false)
    },
  })

  // Delete vCenter mutation
  const deleteVcenter = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/vcenter/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vcenters'] })
    },
  })

  // Test connection mutation
  const testConnection = useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/vcenter/${id}/test`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vcenters'] })
    },
  })

  // Run analysis mutation
  const runAnalysis = useMutation({
    mutationFn: async () => {
      if (!selectedVcenter) return
      const { data } = await api.post('/analysis/run', {
        vcenter_id: selectedVcenter,
        analysis_type: analysisType,
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-runs'] })
    },
  })

  const runs = runsData?.data || []

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-700'
      case 'running': return 'bg-blue-100 text-blue-700'
      case 'failed': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis</h1>
          <p className="text-gray-500 mt-1">Manage vCenter connections and run compliance analysis</p>
        </div>
        {isOperator() && (
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add vCenter
          </button>
        )}
      </div>

      {/* vCenter Connections */}
      <div className="bg-white rounded-xl shadow-sm border">
        <div className="p-5 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Server className="w-5 h-5 text-gray-400" />
            vCenter Connections
          </h2>
        </div>
        {loadingVcenters ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
          </div>
        ) : !vcenters || vcenters.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No vCenter connections. Add one to start analyzing.
          </div>
        ) : (
          <div className="divide-y">
            {vcenters.map((vc) => (
              <div key={vc.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-4">
                  <div className={`w-2 h-2 rounded-full ${vc.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <div>
                    <p className="font-medium text-gray-900">{vc.name}</p>
                    <p className="text-sm text-gray-500">{vc.host}:{vc.port}</p>
                  </div>
                  {vc.version && (
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{vc.version}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {isOperator() && (
                    <>
                      <button
                        onClick={() => testConnection.mutate(vc.id)}
                        disabled={testConnection.isPending}
                        className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors"
                        title="Test connection"
                      >
                        <RefreshCw className={`w-4 h-4 ${testConnection.isPending ? 'animate-spin' : ''}`} />
                      </button>
                      <button
                        onClick={() => deleteVcenter.mutate(vc.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Run Analysis */}
      {isOperator() && vcenters && vcenters.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <PlayCircle className="w-5 h-5 text-gray-400" />
            Run Analysis
          </h2>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">vCenter</label>
              <select
                value={selectedVcenter || ''}
                onChange={(e) => setSelectedVcenter(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Select vCenter...</option>
                {vcenters.filter(vc => vc.is_active).map(vc => (
                  <option key={vc.id} value={vc.id}>{vc.name}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Analysis Type</label>
              <select
                value={analysisType}
                onChange={(e) => setAnalysisType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="full">Full (DRS + Storage)</option>
                <option value="drs">DRS Only</option>
                <option value="storage">Storage Only</option>
              </select>
            </div>
            <button
              onClick={() => runAnalysis.mutate()}
              disabled={!selectedVcenter || runAnalysis.isPending}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {runAnalysis.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {runAnalysis.isPending ? 'Starting...' : 'Run Analysis'}
            </button>
          </div>
          {runAnalysis.data && (
            <p className="mt-3 text-sm text-green-600">
              Analysis started! Run ID: {runAnalysis.data.run_id}
            </p>
          )}
        </div>
      )}

      {/* Analysis Runs */}
      <div className="bg-white rounded-xl shadow-sm border">
        <div className="p-5 border-b">
          <h2 className="text-lg font-semibold">Analysis History</h2>
        </div>
        {loadingRuns ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
          </div>
        ) : runs.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No analysis runs yet.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Started</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {runs.map((run: any) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">#{run.id}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{run.analysis_type}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${statusColor(run.status)}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">{run.started_at || '—'}</td>
                  <td className="px-4 py-3">
                    <a href={`/reports/${run.id}`} className="text-primary-600 hover:text-primary-700 text-sm">
                      View
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add vCenter Modal */}
      {showAddModal && (
        <AddVcenterModal
          onClose={() => setShowAddModal(false)}
          onSubmit={(data) => addVcenter.mutate(data)}
          loading={addVcenter.isPending}
        />
      )}
    </div>
  )
}

function AddVcenterModal({ onClose, onSubmit, loading }: {
  onClose: () => void
  onSubmit: (data: any) => void
  loading: boolean
}) {
  const [form, setForm] = useState({
    name: '',
    host: '',
    port: 443,
    username: '',
    password: '',
    verify_ssl: false,
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Add vCenter Connection</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Production vCenter" required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
            <input
              type="text" value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="vcenter.example.com" required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
              <input
                type="number" value={form.port} onChange={(e) => setForm({ ...form, port: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Verify SSL</label>
              <label className="flex items-center gap-2 mt-2">
                <input
                  type="checkbox" checked={form.verify_ssl}
                  onChange={(e) => setForm({ ...form, verify_ssl: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-600">Enable SSL verification</span>
              </label>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              type="text" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="administrator@vsphere.local" required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
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
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Adding...' : 'Add Connection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
