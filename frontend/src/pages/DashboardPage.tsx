import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Activity, AlertTriangle, Server, Database, Clock } from 'lucide-react'
import api from '../utils/api'

interface DashboardSummary {
  total_vcenters: number
  total_analysis_runs: number
  open_findings: number
  critical_findings: number
  last_run: { id: number; status: string; started_at: string } | null
  findings_by_type: Record<string, number>
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/summary')
      return data as DashboardSummary
    },
  })

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  const summary = data || {
    total_vcenters: 0,
    total_analysis_runs: 0,
    open_findings: 0,
    critical_findings: 0,
    last_run: null,
    findings_by_type: {},
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">vSphere Compliance Overview</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg">
              <Server className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">vCenters</p>
              <p className="text-2xl font-bold">{summary.total_vcenters}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-50 rounded-lg">
              <Activity className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Analysis Runs</p>
              <p className="text-2xl font-bold">{summary.total_analysis_runs}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-50 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Open Findings</p>
              <p className="text-2xl font-bold">{summary.open_findings}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-50 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Critical</p>
              <p className="text-2xl font-bold text-red-600">{summary.critical_findings}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Last Run & Findings by Type */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-400" />
            Last Analysis Run
          </h2>
          {summary.last_run ? (
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Run #{summary.last_run.id}</p>
              <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                summary.last_run.status === 'completed'
                  ? 'bg-green-100 text-green-700'
                  : summary.last_run.status === 'failed'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-yellow-100 text-yellow-700'
              }`}>
                {summary.last_run.status}
              </span>
              <p className="text-xs text-gray-400">{summary.last_run.started_at}</p>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No analysis runs yet.</p>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-gray-400" />
            Findings by Type
          </h2>
          {Object.keys(summary.findings_by_type).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(summary.findings_by_type).map(([type, count]) => (
                <div key={type} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{type}</span>
                  <span className="text-sm font-medium bg-gray-100 px-2 py-0.5 rounded">
                    {count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No findings to display.</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm border p-5">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            to="/analysis"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition-colors"
          >
            Run Analysis
          </Link>
          <Link
            to="/reports"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-colors"
          >
            View Reports
          </Link>
        </div>
      </div>
    </div>
  )
}
