import type { ReactNode } from 'react'

export function PageContainer({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10 ${className}`}>{children}</div>
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string
  description?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">{title}</h1>
        {description && <p className="mt-1.5 max-w-2xl text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  )
}

/** Standard page: container plus header. */
export function Page({
  title,
  description,
  action,
  children,
}: {
  title: string
  description?: ReactNode
  action?: ReactNode
  children: ReactNode
}) {
  return (
    <PageContainer>
      <PageHeader title={title} description={description} action={action} />
      {children}
    </PageContainer>
  )
}
