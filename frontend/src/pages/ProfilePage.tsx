import { History, KeyRound, LogOut, Settings2, Trash2, UserRound } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { PageContainer, PageHeader } from '../components/layout/Page'
import { PreferenceForm } from '../components/recommendation/PreferenceForm'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmptyState, ErrorState, Skeleton, Spinner } from '../components/ui/Feedback'
import { Input } from '../components/ui/Field'
import { Pagination } from '../components/ui/Pagination'
import { Tabs } from '../components/ui/Tabs'
import { useAsync } from '../hooks/useAsync'
import { useAuth } from '../hooks/useAuth'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { useToast } from '../hooks/useToast'
import { propertyService } from '../services/propertyService'
import { userService } from '../services/userService'
import type { Preferences } from '../types/api'
import { toAppError } from '../utils/errors'
import { formatDate, formatDateTime, formatRupees } from '../utils/format'

type TabId = 'profile' | 'preferences' | 'history' | 'security'
const TAB_IDS: TabId[] = ['profile', 'preferences', 'history', 'security']

function ProfileTab() {
  const { user, setUser } = useAuth()
  const { notify } = useToast()
  const [form, setForm] = useState({ first_name: user?.first_name ?? '', last_name: user?.last_name ?? '', phone: user?.phone ?? '' })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      setUser(await userService.updateProfile(form))
      notify('Profile updated.', 'success')
    } catch (error) {
      const appError = toAppError(error)
      setErrors(appError.fieldErrors)
      notify(appError.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="max-w-xl space-y-5" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="First name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} error={errors.first_name} maxLength={150} />
        <Input label="Last name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} error={errors.last_name} maxLength={150} />
      </div>
      <Input label="Email" value={user?.email ?? ''} disabled hint="Contact support to change your email address." />
      <Input label="Phone" type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} error={errors.phone} placeholder="+91 98xxx xxxxx" />
      <p className="text-sm text-slate-500">
        Member since {formatDate(user?.created_at)} {user?.is_admin && <Badge tone="brand" className="ml-2">Administrator</Badge>}
      </p>
      <Button type="submit" loading={saving}>
        Save changes
      </Button>
    </form>
  )
}

function PreferencesTab() {
  const { notify } = useToast()
  const saved = useAsync(() => userService.getPreferences(), [])
  const locations = useAsync(() => propertyService.locations(), [])
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const save = async (preferences: Preferences) => {
    setSaving(true)
    setErrors({})
    try {
      await userService.savePreferences(preferences)
      notify('Preferences saved. Match scores across RentWise now use them.', 'success')
      saved.reload()
    } catch (error) {
      const appError = toAppError(error)
      setErrors(appError.fieldErrors)
      notify(appError.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  if (saved.loading && !saved.data) return <Spinner label="Loading preferences" />
  if (saved.error) return <ErrorState error={saved.error} onRetry={saved.reload} />
  return (
    <div className="max-w-2xl">
      {saved.data?.updated_at && <p className="mb-5 text-sm text-slate-500">Last updated {formatDateTime(saved.data.updated_at)}</p>}
      <PreferenceForm
        initial={saved.data?.updated_at ? saved.data : undefined}
        onSubmit={save}
        submitLabel="Save preferences"
        loading={saving}
        serverErrors={errors}
        locations={locations.data?.map((row) => row.location)}
      />
    </div>
  )
}

function HistoryTab() {
  const { notify } = useToast()
  const [page, setPage] = useState(1)
  const { data, error, loading, reload } = useAsync(() => userService.getHistory(page, 10), [page])
  const [clearing, setClearing] = useState(false)

  const clear = async () => {
    if (!window.confirm('Clear your entire recommendation history?')) return
    setClearing(true)
    try {
      await userService.clearHistory()
      notify('History cleared.', 'success')
      setPage(1)
      reload()
    } catch (caught) {
      notify(toAppError(caught).message, 'error')
    } finally {
      setClearing(false)
    }
  }

  if (loading)
    return (
      <div className="space-y-3">
        {[0, 1, 2, 3].map((key) => (
          <Skeleton key={key} className="h-20 w-full" />
        ))}
      </div>
    )
  if (error) return <ErrorState error={error} onRetry={reload} />
  if (!data?.results.length)
    return <EmptyState icon={<History className="h-6 w-6" aria-hidden />} title="No recommendation history" description="Your recommendation searches will be listed here." />

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="ghost" size="sm" onClick={clear} loading={clearing} icon={<Trash2 className="h-4 w-4" />} className="text-rose-600 hover:bg-rose-50">
          Clear history
        </Button>
      </div>
      <ul className="space-y-3">
        {data.results.map((entry) => {
          const prefs = entry.request_preferences
          return (
            <li key={entry.id} className="rounded-xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-900">
                    {prefs.location || 'Any location'}
                    {prefs.max_rent ? ` · up to ${formatRupees(prefs.max_rent)}` : ''}
                    {prefs.bedrooms ? ` · ${prefs.bedroom_mode === 'minimum' ? '≥' : ''}${prefs.bedrooms} bed` : ''}
                  </p>
                  <p className="text-xs text-slate-500">
                    {formatDateTime(entry.created_at)} · {entry.total_matches} matching homes · {entry.latency_ms.toFixed(0)} ms
                  </p>
                </div>
                <div className="flex gap-2">
                  {entry.budget_relaxed && <Badge tone="warning">Budget relaxed</Badge>}
                  {entry.top_score !== null && <Badge tone="brand">Best {Math.round(entry.top_score)}%</Badge>}
                </div>
              </div>
              {entry.results.length > 0 && (
                <ol className="mt-3 flex flex-wrap gap-2">
                  {entry.results.slice(0, 5).map((result, index) => (
                    <li key={result.id}>
                      <Link to={`/properties/${result.id}`} className="inline-flex items-center gap-1 rounded-lg bg-slate-50 px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-100">
                        <span className="font-semibold text-slate-400">#{index + 1}</span> {result.title}
                      </Link>
                    </li>
                  ))}
                </ol>
              )}
            </li>
          )
        })}
      </ul>
      <Pagination page={page} pageSize={10} total={data.count} onChange={setPage} />
    </div>
  )
}

function SecurityTab() {
  const { setUser } = useAuth()
  const { notify } = useToast()
  const [form, setForm] = useState({ current: '', next: '', confirm: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const found: Record<string, string> = {}
    if (!form.current) found.current_password = 'Enter your current password.'
    if (form.next.length < 8) found.new_password = 'Use at least 8 characters.'
    if (form.next !== form.confirm) found.confirm = "Passwords don't match."
    setErrors(found)
    if (Object.keys(found).length) return
    setSaving(true)
    try {
      setUser(await userService.changePassword(form.current, form.next))
      setForm({ current: '', next: '', confirm: '' })
      notify('Password changed. Other sessions have been signed out.', 'success')
    } catch (error) {
      const appError = toAppError(error)
      setErrors(appError.fieldErrors)
      if (!Object.keys(appError.fieldErrors).length) notify(appError.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="max-w-md space-y-5" noValidate>
      <Input label="Current password" type="password" autoComplete="current-password" value={form.current} onChange={(e) => setForm({ ...form, current: e.target.value })} error={errors.current_password} />
      <Input label="New password" type="password" autoComplete="new-password" value={form.next} onChange={(e) => setForm({ ...form, next: e.target.value })} error={errors.new_password} />
      <Input label="Confirm new password" type="password" autoComplete="new-password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} error={errors.confirm} />
      <Button type="submit" loading={saving}>
        Change password
      </Button>
    </form>
  )
}

export function ProfilePage() {
  useDocumentTitle('Profile')
  const { logout } = useAuth()
  const { notify } = useToast()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const requested = params.get('tab') as TabId | null
  const tab: TabId = requested && TAB_IDS.includes(requested) ? requested : 'profile'

  const handleLogout = async () => {
    await logout()
    notify('You have been signed out.', 'success')
    navigate('/')
  }

  return (
    <PageContainer>
      <PageHeader
        title="Your account"
        description="Manage your profile, recommendation preferences and history."
        action={
          <Button variant="secondary" onClick={handleLogout} icon={<LogOut className="h-4 w-4" />}>
            Sign out
          </Button>
        }
      />
      <Card>
        <div className="px-5 pt-2">
          <Tabs
            label="Account sections"
            active={tab}
            onChange={(id) => setParams(id === 'profile' ? {} : { tab: id })}
            tabs={[
              { id: 'profile', label: <><UserRound className="h-4 w-4" aria-hidden /> Profile</> },
              { id: 'preferences', label: <><Settings2 className="h-4 w-4" aria-hidden /> Preferences</> },
              { id: 'history', label: <><History className="h-4 w-4" aria-hidden /> History</> },
              { id: 'security', label: <><KeyRound className="h-4 w-4" aria-hidden /> Security</> },
            ]}
          />
        </div>
        <div className="p-5 sm:p-6" role="tabpanel">
          {tab === 'profile' && <ProfileTab />}
          {tab === 'preferences' && <PreferencesTab />}
          {tab === 'history' && <HistoryTab />}
          {tab === 'security' && <SecurityTab />}
        </div>
      </Card>
    </PageContainer>
  )
}
