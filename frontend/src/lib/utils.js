import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatDate(value, opts = {}) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    ...opts,
  });
}

export function formatPercent(n, digits = 0) {
  if (n == null || Number.isNaN(Number(n))) return '—';
  return `${(Number(n) * (Number(n) <= 1 ? 100 : 1)).toFixed(digits)}%`;
}

export function scoreColor(score) {
  const s = Number(score) || 0;
  if (s >= 80) return 'text-emerald-500';
  if (s >= 60) return 'text-teal-500';
  if (s >= 40) return 'text-amber-500';
  return 'text-rose-500';
}

export function initials(name = '') {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('') || '?';
}

export function downloadCsv(filename, rows) {
  const csv = rows
    .map((r) =>
      r
        .map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`)
        .join(',')
    )
    .join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
