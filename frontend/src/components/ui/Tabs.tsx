import type { ReactNode } from 'react'

interface TabsProps<T extends string> {
  tabs: { id: T; label: ReactNode }[]
  active: T
  onChange: (id: T) => void
  label: string
}

export function Tabs<T extends string>({ tabs, active, onChange, label }: TabsProps<T>) {
  return (
    <div role="tablist" aria-label={label} className="-mx-1 flex gap-1 overflow-x-auto border-b border-slate-200 px-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          onClick={() => onChange(tab.id)}
          className={`-mb-px flex shrink-0 items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors ${
            active === tab.id
              ? 'border-brand-700 text-brand-800'
              : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
