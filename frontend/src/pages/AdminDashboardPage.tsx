import { Activity, Building2, Heart, Home, Inbox, LayoutDashboard, MessageSquare, Sparkles, Users } from 'lucide-react'
import { useSearchParams } from 'react-router'
import { ColumnChart, RankedBars, StatTile } from '../components/admin/Charts'
import { InquiriesList, PropertiesTable, UsersTable } from '../components/admin/AdminTables'
import { PageContainer, PageHeader } from '../components/layout/Page'
import { Card, CardHeader } from '../components/ui/Card'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/Feedback'
import { Tabs } from '../components/ui/Tabs'
import { useAsync } from '../hooks/useAsync'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { adminService } from '../services/adminService'
import type { Analytics } from '../types/api'
import { formatRupees } from '../utils/format'

type TabId = 'overview' | 'properties' | 'users' | 'inquiries'
const TAB_IDS: TabId[] = ['overview', 'properties', 'users', 'inquiries']

function percent(value: number | null) {
  return value === null ? '—' : `${(value * 100).toFixed(1)}%`
}

function Overview({ analytics }: { analytics: Analytics }) {
  const trend = analytics.recommendation_trend.map((point) => {
    const date = new Date(`${point.date}T00:00:00`)
    return {
      label: date.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }),
      shortLabel: date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
      value: point.count,
    }
  })
  const engine = analytics.engine_metrics
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatTile label="Total users" value={analytics.users.total} detail={`${analytics.users.new_last_7_days} new this week`} icon={<Users className="h-4 w-4" />} />
        <StatTile label="Total properties" value={analytics.properties.total} detail={`Avg rent ${formatRupees(analytics.properties.average_rent)}`} icon={<Building2 className="h-4 w-4" />} />
        <StatTile label="Active listings" value={analytics.properties.active} detail={`${analytics.properties.inactive} inactive · ${analytics.properties.flagged} flagged`} icon={<Home className="h-4 w-4" />} />
        <StatTile label="Recommendation requests" value={analytics.recommendations.total} detail={`${analytics.recommendations.last_7_days} in the last 7 days`} icon={<Sparkles className="h-4 w-4" />} />
        <StatTile label="Favorites" value={analytics.favorites.total} detail={`${analytics.inquiries.new} new inquiries`} icon={<Heart className="h-4 w-4" />} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Recommendation requests per day" description="Signed-in users, last 14 days" />
          <div className="p-5">
            <ColumnChart data={trend} label="Recommendation requests per day over the last 14 days" />
          </div>
        </Card>
        <Card>
          <CardHeader title="Recommendation engine" description="From recorded requests" />
          <dl className="divide-y divide-slate-100 px-5">
            {[
              ['Average latency', analytics.recommendations.average_latency_ms === null ? '—' : `${analytics.recommendations.average_latency_ms} ms`],
              ['Average candidates', analytics.recommendations.average_candidates ?? '—'],
              ['Budget relaxation rate', percent(analytics.recommendations.budget_relaxation_rate)],
              ['Requests since restart', engine.requests],
              ['Empty-result rate (since restart)', percent(engine.empty_result_rate)],
              ['Property views (7 days)', analytics.interactions.views_last_7_days],
            ].map(([label, value]) => (
              <div key={label as string} className="flex items-center justify-between py-3 text-sm">
                <dt className="text-slate-500">{label}</dt>
                <dd className="font-medium tabular-nums text-slate-900">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader title="Active listings by locality" />
          <div className="p-5">
            {analytics.listings_by_location.length ? (
              <RankedBars rows={analytics.listings_by_location.map((row) => ({ label: row.location, value: row.count }))} unit="listings" />
            ) : (
              <p className="text-sm text-slate-500">No active listings.</p>
            )}
          </div>
        </Card>
        <Card>
          <CardHeader title="Most saved" />
          <ol className="divide-y divide-slate-100 px-5">
            {analytics.most_favorited.length ? (
              analytics.most_favorited.map((row) => (
                <li key={row.id} className="flex items-center justify-between gap-3 py-3 text-sm">
                  <span className="min-w-0">
                    <span className="line-clamp-1 font-medium text-slate-800">{row.title}</span>
                    <span className="text-xs text-slate-500">{row.location}</span>
                  </span>
                  <span className="shrink-0 tabular-nums text-slate-700">{row.favorites_total}</span>
                </li>
              ))
            ) : (
              <li className="py-4 text-sm text-slate-500">No saves yet.</li>
            )}
          </ol>
        </Card>
        <Card>
          <CardHeader title="Most viewed" />
          <ol className="divide-y divide-slate-100 px-5">
            {analytics.most_viewed.length ? (
              analytics.most_viewed.map((row) => (
                <li key={row.id} className="flex items-center justify-between gap-3 py-3 text-sm">
                  <span className="min-w-0">
                    <span className="line-clamp-1 font-medium text-slate-800">{row.title}</span>
                    <span className="text-xs text-slate-500">{row.location}</span>
                  </span>
                  <span className="shrink-0 tabular-nums text-slate-700">{row.views_total}</span>
                </li>
              ))
            ) : (
              <li className="py-4 text-sm text-slate-500">No views yet.</li>
            )}
          </ol>
        </Card>
      </div>
    </div>
  )
}

export function AdminDashboardPage() {
  useDocumentTitle('Admin')
  const [params, setParams] = useSearchParams()
  const requested = params.get('tab') as TabId | null
  const tab: TabId = requested && TAB_IDS.includes(requested) ? requested : 'overview'
  const analytics = useAsync(() => adminService.analytics(), [])

  return (
    <PageContainer>
      <PageHeader title="Admin dashboard" description="Platform health, listings, users and inquiries." />
      <div className="mb-6">
        <Tabs
          label="Admin sections"
          active={tab}
          onChange={(id) => setParams(id === 'overview' ? {} : { tab: id })}
          tabs={[
            { id: 'overview', label: <><LayoutDashboard className="h-4 w-4" aria-hidden /> Overview</> },
            { id: 'properties', label: <><Building2 className="h-4 w-4" aria-hidden /> Listings</> },
            { id: 'users', label: <><Users className="h-4 w-4" aria-hidden /> Users</> },
            { id: 'inquiries', label: <><MessageSquare className="h-4 w-4" aria-hidden /> Inquiries</> },
          ]}
        />
      </div>
      <div role="tabpanel">
        {tab === 'overview' &&
          (analytics.loading ? (
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
                {Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-28 rounded-2xl" />)}
              </div>
              <Skeleton className="h-72 rounded-2xl" />
            </div>
          ) : analytics.error ? (
            <ErrorState error={analytics.error} onRetry={analytics.reload} />
          ) : analytics.data ? (
            <Overview analytics={analytics.data} />
          ) : (
            <EmptyState icon={<Activity className="h-6 w-6" />} title="No analytics yet" />
          ))}
        {tab === 'properties' && <Card className="p-5"><PropertiesTable onChanged={analytics.reload} /></Card>}
        {tab === 'users' && <Card className="p-5"><UsersTable /></Card>}
        {tab === 'inquiries' && (
          <Card className="p-5">
            <div className="mb-4 flex items-center gap-2 text-sm text-slate-500"><Inbox className="h-4 w-4" aria-hidden /> Contact requests from users</div>
            <InquiriesList />
          </Card>
        )}
      </div>
    </PageContainer>
  )
}
