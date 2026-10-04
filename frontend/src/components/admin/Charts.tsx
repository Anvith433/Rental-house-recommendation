import { useState, type ReactNode } from 'react'

export function StatTile({ label, value, detail, icon }: { label: string; value: ReactNode; detail?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{label}</p>
        {icon && <span className="text-slate-400">{icon}</span>}
      </div>
      <p className="mt-2 text-3xl font-semibold tabular-nums tracking-tight text-slate-900">{value}</p>
      {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
    </div>
  )
}

function niceMax(value: number): number {
  if (value <= 4) return 4
  const magnitude = 10 ** Math.floor(Math.log10(value))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s * 4 >= value) ?? magnitude * 10
  return step * 4
}

/**
 * Single-series column chart (one hue, so no legend – the card title names it).
 * Columns are capped at 24px with a rounded data-end and a square baseline;
 * hovering or focusing a column shows its exact value. A visually hidden table
 * carries the same data for screen readers.
 */
export function ColumnChart({ data, label }: { data: { label: string; shortLabel: string; value: number }[]; label: string }) {
  const [active, setActive] = useState<number | null>(null)
  const max = niceMax(Math.max(0, ...data.map((d) => d.value)))
  const ticks = [0, max / 4, max / 2, (3 * max) / 4, max]
  const height = 180

  return (
    <figure>
      <div className="relative flex gap-2" style={{ height: height + 24 }}>
        <div className="flex w-8 flex-col-reverse justify-between pb-6 text-right text-[11px] tabular-nums text-slate-400" aria-hidden>
          {ticks.map((tick) => (
            <span key={tick} className="-translate-y-1/2 leading-none first:translate-y-0">
              {Number.isInteger(tick) ? tick.toLocaleString('en-IN') : tick.toFixed(1)}
            </span>
          ))}
        </div>
        <div className="relative flex-1">
          <div className="absolute inset-x-0 top-0" style={{ height }} aria-hidden>
            {ticks.map((tick) => (
              <div key={tick} className="absolute inset-x-0 border-t border-slate-100" style={{ bottom: `${(tick / max) * 100}%` }} />
            ))}
          </div>
          <div className="absolute inset-x-0 top-0 flex items-end gap-[2px]" style={{ height }} role="img" aria-label={label}>
            {data.map((point, index) => (
              <div
                key={point.label}
                className="group relative flex h-full flex-1 cursor-default items-end justify-center outline-none"
                tabIndex={0}
                onMouseEnter={() => setActive(index)}
                onMouseLeave={() => setActive(null)}
                onFocus={() => setActive(index)}
                onBlur={() => setActive(null)}
                aria-label={`${point.label}: ${point.value}`}
              >
                <div
                  className={`w-full max-w-6 rounded-t-[4px] transition-colors ${active === index ? 'bg-brand-700' : 'bg-brand-600'}`}
                  style={{ height: `${(point.value / max) * 100}%`, minHeight: point.value > 0 ? 2 : 0 }}
                />
                {active === index && (
                  <div className="pointer-events-none absolute bottom-full z-10 mb-2 whitespace-nowrap rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-md">
                    <p className="text-slate-500">{point.label}</p>
                    <p className="font-semibold tabular-nums text-slate-900">{point.value.toLocaleString('en-IN')} requests</p>
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="absolute inset-x-0 border-t border-slate-300" style={{ top: height }} aria-hidden />
          <div className="absolute inset-x-0 flex gap-[2px] text-[11px] text-slate-400" style={{ top: height + 6 }} aria-hidden>
            {data.map((point, index) => (
              <span key={point.label} className="flex-1 text-center">
                {index % 2 === data.length % 2 ? '' : point.shortLabel}
              </span>
            ))}
          </div>
        </div>
      </div>
      <table className="sr-only">
        <caption>{label}</caption>
        <thead>
          <tr>
            <th>Date</th>
            <th>Requests</th>
          </tr>
        </thead>
        <tbody>
          {data.map((point) => (
            <tr key={point.label}>
              <td>{point.label}</td>
              <td>{point.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}

/** Horizontal ranked bars with the value at each bar's tip (text in ink colours, not the bar colour). */
export function RankedBars({ rows, unit }: { rows: { label: string; value: number }[]; unit: string }) {
  const max = Math.max(1, ...rows.map((row) => row.value))
  return (
    <ul className="space-y-3">
      {rows.map((row) => (
        <li key={row.label} className="grid grid-cols-[minmax(0,8rem)_1fr] items-center gap-3 text-sm">
          <span className="truncate text-slate-600" title={row.label}>
            {row.label}
          </span>
          <div className="flex items-center gap-2">
            <div className="h-3 rounded-r-[4px] bg-brand-600" style={{ width: `${(row.value / max) * 85}%`, minWidth: 2 }} />
            <span className="shrink-0 tabular-nums text-slate-700">
              {row.value} <span className="sr-only">{unit}</span>
            </span>
          </div>
        </li>
      ))}
    </ul>
  )
}
