import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileText, Download, Loader2 } from 'lucide-react'
import api from '../utils/api'

interface Report {
  id: number
  vcenter_id: number
  analysis_type: string
  started_at: string
  completed_at: string | null
  summary: any
}

export default function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const { data } = await api.get('/reports/?per_page=20')
      return data
    },
  })

  const reports: Report[] = data?.data || []

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="text-gray-500 mt-1">View and export analysis reports</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No reports available.</p>
          <p className="text-sm text-gray-400 mt-1">Run an analysis to generate your first report.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Report ID</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Completed</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">#{report.id}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{report.analysis_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{report.completed_at || '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <Link
                        to={`/reports/${report.id}`}
                        className="text-primary-600 hover:text-primary-700 text-sm"
                      >
                        View
                      </Link>
                      <a
                        href={`${import.meta.env.VITE_API_BASE_URL || '/api'}/reports/${report.id}/export?format=json`}
                        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Download className="w-3 h-3" />
                        JSON
                      </a>
                      <a
                        href={`${import.meta.env.VITE_API_BASE_URL || '/api'}/reports/${report.id}/export?format=csv`}
                        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Download className="w-3 h-3" />
                        CSV
                      </a>
                    </div>
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
