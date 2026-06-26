import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { PlayCircle, Loader2, AlertTriangle } from 'lucide-react'
import api from '../utils/api'

interface AnalysisRun {
  id: number
  vcenter_id: number
  analysis_type: string
  status: string
  started_at: string
  completed_at: string | null
  summary: any
}

export default function AnalysisPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analysis-runs'],
    queryFn: async () => {
      const { data } = await api.get('/analysis/?per_page=20')
      return data
    },
  })

  const runs: AnalysisRun[] = data?.data || []

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
          <p className="text-gray-500 mt-1">Run and monitor compliance analysis</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition-colors">
          <PlayCircle className="w-4 h-4" />
          Run Analysis
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
        </div>
      ) : runs.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No analysis runs yet.</p>
          <p className="text-sm text-gray-400 mt-1">Connect a vCenter and run your first analysis.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
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
              {runs.map((run) => (
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
                    <Link
                      to={`/reports/${run.id}`}
                      className="text-primary-600 hover:text-primary-700 text-sm"
                    >
                      View
                    </Link>
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
