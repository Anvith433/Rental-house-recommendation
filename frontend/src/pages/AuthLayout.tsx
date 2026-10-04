import { Check } from 'lucide-react'
import type { ReactNode } from 'react'
import { Logo } from '../components/layout/Logo'

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: ReactNode; children: ReactNode }) {
  return (
    <div className="grid min-h-[calc(100vh-4rem)] lg:grid-cols-2">
      <div className="flex items-center justify-center px-4 py-12 sm:px-6">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
          <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
      <div className="relative hidden overflow-hidden bg-brand-800 lg:block">
        <img src="/images/properties/living-1.svg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-25" />
        <div className="relative flex h-full flex-col justify-end p-12 text-white">
          <div className="rounded-2xl bg-white/10 p-6 backdrop-blur">
            <Logo className="[&_span]:text-white" />
            <ul className="mt-5 space-y-3 text-sm text-brand-50">
              {[
                'Recommendations ranked by your own priorities',
                'A plain-language reason behind every match',
                'Saved homes and preferences across devices',
              ].map((line) => (
                <li key={line} className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-brand-200" aria-hidden />
                  {line}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
