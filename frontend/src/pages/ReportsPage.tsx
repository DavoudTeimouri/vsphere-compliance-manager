import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Download, Loader2, CheckCircle } from 'lucide-react'
import api from '../utils/api'

interface Report {
  id: number
  vcenter_id: number
  analysis_type: string
  status: string
  started_at: string
  completed_at: string | null
  summary: any
}

interface Finding {
  id: number
  finding_type: string
  severity: string
  cluster_name: string | null
  vm_name: string
  datastore_name: string | null
  details: any
  recommendation: string
  is_actionable: boolean
  action_taken: boolean
}

function formatDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

const severityStyle = (severity: string) => {
  switch (severity) {
    case 'critical': return 'text-red-600 bg-red-50'
    case 'warning': return 'text-yellow-600 bg-yellow-50'
    case 'info': return 'text-blue-600 bg-blue-50'
    default: return 'text-gray-600 bg-gray-50'
  }
}

// ── List View ──────────────────────────────────────────────

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
        <div className="grid gap-4">
          {reports.map((report) => (
            <div key={report.id} className="bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-gray-900">Report #{report.id}</h3>
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded capitalize">
                      {report.analysis_type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Completed {report.completed_at ? formatDate(report.completed_at) : '—'}
                  </p>
                  {report.summary && (
                    <div className="flex gap-4 mt-3">
                      {report.summary.drs && (
                        <span className="text-xs text-gray-500">
                          DRS: {report.summary.drs.clusters} clusters
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    to={`/reports/${report.id}`}
                    className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition-colors"
                  >
                    View Details
                  </Link>
                  <a
                    href={`${import.meta.env.VITE_API_BASE_URL || '/api'}/reports/${report.id}/export?format=json`}
                    className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
                    title="Export JSON"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Detail View ────────────────────────────────────────────

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<string>('all')

  const { data: report, isLoading: loadingReport } = useQuery({
    queryKey: ['report', id],
    queryFn: async () => {
      const { data } = await api.get(`/reports/${id}`)
      return data
    },
  })

  const { data: findings, isLoading: loadingFindings } = useQuery({
    queryKey: ['findings', id],
    queryFn: async () => {
      const { data } = await api.get(`/analysis/${id}/findings?per_page=100`)
      return data
    },
  })

  const applyDrs = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/analysis/${id}/apply-drs`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['findings', id] })
    },
  })

  const approveStorage = useMutation({
    mutationFn: async (findingId: number) => {
      const { data } = await api.post(`/analysis/${id}/approve-storage/${findingId}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['findings', id] })
    },
  })

  const isLoading = loadingReport || loadingFindings
  const allFindings: Finding[] = findings?.data || []
  const filteredFindings = filter === 'all'
    ? allFindings
    : allFindings.filter(f => f.severity === filter)

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
        <Link to="/reports" className="text-primary-600 hover:text-primary-700 text-sm">
          ← Back to Reports
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-2">Report #{id}</h1>
        <p className="text-gray-500 mt-1">
          {report?.analysis_type && <span className="capitalize">{report.analysis_type} analysis</span>}
          {' · '}
          {report?.completed_at ? formatDate(report.completed_at) : report?.status}
        </p>
      </div>

      {/* Summary Stats */}
      {report?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {report.summary.drs && (
            <>
              <div className="bg-white rounded-xl shadow-sm border p-4">
                <p className="text-sm text-gray-500">Clusters Analyzed</p>
                <p className="text-2xl font-bold mt-1">{report.summary.drs.clusters}</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border p-4">
                <p className="text-sm text-gray-500">DRS Rules to Create</p>
                <p className="text-2xl font-bold mt-1 text-yellow-600">{report.summary.drs.rules_to_create}</p>
              </div>
            </>
          )}
          {report.summary.storage && (
            <>
              <div className="bg-white rounded-xl shadow-sm border p-4">
                <p className="text-sm text-gray-500">Storage Violations</p>
                <p className="text-2xl font-bold mt-1 text-red-600">{report.summary.storage.total_violations || 0}</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border p-4">
                <p className="text-sm text-gray-500">Scattered VMs</p>
                <p className="text-2xl font-bold mt-1 text-yellow-600">{report.summary.storage.total_scattered_vms || 0}</p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => applyDrs.mutate()}
          disabled={applyDrs.isPending}
          className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          {applyDrs.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          Apply DRS Rules
        </button>
        <a
          href={`${import.meta.env.VITE_API_BASE_URL || '/api'}/reports/${id}/export?format=json`}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-colors flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export JSON
        </a>
        <a
          href={`${import.meta.env.VITE_API_BASE_URL || '/api'}/reports/${id}/export?format=csv`}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-colors flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </a>
      </div>

      {/* Findings Filter */}
      <div className="flex gap-2">
        {['all', 'critical', 'warning', 'info'].map(sev => (
          <button
            key={sev}
            onClick={() => setFilter(sev)}
            className={`px-3 py-1.5 rounded-lg text-sm capitalize transition-colors ${
              filter === sev
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {sev}
            {sev !== 'all' && (
              <span className="ml-1 opacity-75">
                ({allFindings.filter(f => f.severity === sev).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Findings Table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {filteredFindings.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-400" />
            <p>No findings for this filter.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Severity</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">VM / Cluster</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredFindings.map((finding) => (
                <tr key={finding.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium capitalize ${severityStyle(finding.severity)}`}>
                      {finding.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 capitalize">
                    {finding.finding_type.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <p className="font-medium text-gray-900">{finding.vm_name}</p>
                    {finding.cluster_name && (
                      <p className="text-xs text-gray-400">{finding.cluster_name}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs">
                    {finding.recommendation}
                  </td>
                  <td className="px-4 py-3">
                    {finding.action_taken ? (
                      <span className="flex items-center gap-1 text-green-600 text-sm">
                        <CheckCircle className="w-3 h-3" /> Done
                      </span>
                    ) : finding.is_actionable && finding.finding_type === 'storage_shared' ? (
                      <button
                        onClick={() => approveStorage.mutate(finding.id)}
                        disabled={approveStorage.isPending}
                        className="text-xs px-2 py-1 bg-primary-50 text-primary-700 rounded hover:bg-primary-100 transition-colors"
                      >
                        Approve
                      </button>
                    ) : (
                      <span className="text-xs text-gray-400">Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
