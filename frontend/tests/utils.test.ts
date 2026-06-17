import { describe, it, expect } from 'vitest'

// ── Severity helpers ──────────────────────────────────────
export function severityColor(severity: string): string {
  switch (severity) {
    case 'critical': return 'text-red-600'
    case 'warning':  return 'text-yellow-500'
    case 'info':     return 'text-blue-500'
    default:         return 'text-gray-400'
  }
}

export function severityLabel(severity: string): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1)
}

// ── Date helpers ──────────────────────────────────────────
export function formatDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

export function formatDateTime(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB')
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)   return 'just now'
  if (mins < 60)  return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)   return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

// ── Byte formatting ───────────────────────────────────────
export function formatGB(gb: number): string {
  if (gb >= 1024) return `${(gb / 1024).toFixed(1)} TB`
  return `${gb.toFixed(0)} GB`
}

// ── Role helpers ──────────────────────────────────────────
export function canEdit(role: string): boolean {
  return role === 'admin' || role === 'operator'
}

export function canAdmin(role: string): boolean {
  return role === 'admin'
}

// ══════════════════════════════════════════════════════════
// TESTS
// ══════════════════════════════════════════════════════════

describe('severityColor', () => {
  it('returns red for critical', () => {
    expect(severityColor('critical')).toBe('text-red-600')
  })
  it('returns yellow for warning', () => {
    expect(severityColor('warning')).toBe('text-yellow-500')
  })
  it('returns blue for info', () => {
    expect(severityColor('info')).toBe('text-blue-500')
  })
  it('returns gray for unknown', () => {
    expect(severityColor('unknown')).toBe('text-gray-400')
  })
})

describe('severityLabel', () => {
  it('capitalises first letter', () => {
    expect(severityLabel('critical')).toBe('Critical')
    expect(severityLabel('warning')).toBe('Warning')
  })
})

describe('formatDate', () => {
  it('returns dash for empty string', () => {
    expect(formatDate('')).toBe('—')
  })
  it('formats a valid ISO date', () => {
    const result = formatDate('2026-06-17T10:00:00Z')
    expect(result).toMatch(/2026/)
  })
})

describe('timeAgo', () => {
  it('returns just now for recent timestamps', () => {
    const now = new Date().toISOString()
    expect(timeAgo(now)).toBe('just now')
  })
})

describe('formatGB', () => {
  it('formats GB under 1TB', () => {
    expect(formatGB(500)).toBe('500 GB')
  })
  it('converts to TB over 1024', () => {
    expect(formatGB(2048)).toBe('2.0 TB')
  })
})

describe('canEdit', () => {
  it('admin can edit', ()   => expect(canEdit('admin')).toBe(true))
  it('operator can edit', () => expect(canEdit('operator')).toBe(true))
  it('viewer cannot edit', () => expect(canEdit('viewer')).toBe(false))
})

describe('canAdmin', () => {
  it('admin can admin',    () => expect(canAdmin('admin')).toBe(true))
  it('operator cannot',    () => expect(canAdmin('operator')).toBe(false))
  it('viewer cannot',      () => expect(canAdmin('viewer')).toBe(false))
})
