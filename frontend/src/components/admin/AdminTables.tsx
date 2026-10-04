import { Ban, CheckCircle2, Flag, Pencil, Plus, Search, ShieldCheck, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { useAsync } from '../../hooks/useAsync'
import { useAuth } from '../../hooks/useAuth'
import { useToast } from '../../hooks/useToast'
import { adminService } from '../../services/adminService'
import { propertyService } from '../../services/propertyService'
import type { AdminProperty, Inquiry, ListingStatus, Property, Role } from '../../types/api'
import { toAppError } from '../../utils/errors'
import { formatDate, formatDateTime, formatRupees } from '../../utils/format'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { EmptyState, ErrorState, Skeleton } from '../ui/Feedback'
import { Select } from '../ui/Field'
import { Pagination } from '../ui/Pagination'
import { PropertyFormModal } from './PropertyFormModal'

const STATUS_TONE: Record<ListingStatus, 'success' | 'neutral' | 'danger'> = { active: 'success', inactive: 'neutral', flagged: 'danger' }
const PAGE_SIZE = 12

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 6 }, (_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <label className="relative block w-full sm:max-w-xs">
      <span className="sr-only">{placeholder}</span>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-10 w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 text-sm shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/30"
      />
    </label>
  )
}

export function PropertiesTable({ onChanged }: { onChanged: () => void }) {
  const { notify } = useToast()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<ListingStatus | ''>('')
  const [editing, setEditing] = useState<Property | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [busy, setBusy] = useState<number | null>(null)
  const list = useAsync(
    () => adminService.properties({ page, page_size: PAGE_SIZE, search: search.trim() || undefined, status: status || undefined }),
    [page, search, status],
  )

  const openEditor = async (row?: AdminProperty) => {
    if (!row) {
      setEditing(null)
      setFormOpen(true)
      return
    }
    try {
      setEditing(await propertyService.get(row.id))
      setFormOpen(true)
    } catch (error) {
      notify(toAppError(error).message, 'error')
    }
  }

  const act = async (row: AdminProperty, action: () => Promise<unknown>, message: string) => {
    setBusy(row.id)
    try {
      await action()
      notify(message, 'success')
      list.reload()
      onChanged()
    } catch (error) {
      notify(toAppError(error).message, 'error')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 flex-col gap-3 sm:flex-row">
          <SearchBox value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search listings" />
          <Select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value as ListingStatus | ''); setPage(1) }} containerClassName="sm:w-44">
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="flagged">Flagged</option>
          </Select>
        </div>
        <Button icon={<Plus className="h-4 w-4" />} onClick={() => openEditor()}>
          New listing
        </Button>
      </div>

      {list.loading ? (
        <TableSkeleton />
      ) : list.error ? (
        <ErrorState error={list.error} onRetry={list.reload} />
      ) : !list.data?.results.length ? (
        <EmptyState title="No listings found" description="Try a different search or status filter." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full min-w-[56rem] text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Listing</th>
                  <th scope="col" className="px-4 py-3">Rent</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3 text-right">Views</th>
                  <th scope="col" className="px-4 py-3 text-right">Saves</th>
                  <th scope="col" className="px-4 py-3 text-right">Inquiries</th>
                  <th scope="col" className="px-4 py-3">Updated</th>
                  <th scope="col" className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {list.data.results.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50/60">
                    <td className="max-w-xs px-4 py-3">
                      <Link to={`/properties/${row.id}`} className="line-clamp-1 font-medium text-slate-900 hover:text-brand-700">{row.title}</Link>
                      <p className="text-xs text-slate-500">{row.location} · {row.bedrooms} bed · {row.area_sqft} sq ft</p>
                    </td>
                    <td className="px-4 py-3 tabular-nums">{formatRupees(row.rent)}</td>
                    <td className="px-4 py-3"><Badge tone={STATUS_TONE[row.status]}>{row.status}</Badge></td>
                    <td className="px-4 py-3 text-right tabular-nums">{row.views_count}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{row.favorites_count}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{row.inquiries_count}</td>
                    <td className="px-4 py-3 text-slate-500">{formatDate(row.updated_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="sm" aria-label={`Edit ${row.title}`} title="Edit" onClick={() => openEditor(row)} icon={<Pencil className="h-4 w-4" />} />
                        {row.status === 'active' ? (
                          <>
                            <Button variant="ghost" size="sm" title="Deactivate" aria-label={`Deactivate ${row.title}`} disabled={busy === row.id}
                              onClick={() => act(row, () => propertyService.update(row.id, { status: 'inactive' }), 'Listing deactivated.')} icon={<Ban className="h-4 w-4" />} />
                            <Button variant="ghost" size="sm" title="Flag for review" aria-label={`Flag ${row.title}`} disabled={busy === row.id}
                              onClick={() => act(row, () => propertyService.update(row.id, { status: 'flagged' }), 'Listing flagged for review.')} icon={<Flag className="h-4 w-4" />} />
                          </>
                        ) : (
                          <Button variant="ghost" size="sm" title="Activate" aria-label={`Activate ${row.title}`} disabled={busy === row.id}
                            onClick={() => act(row, () => propertyService.update(row.id, { status: 'active' }), 'Listing activated.')} icon={<CheckCircle2 className="h-4 w-4" />} />
                        )}
                        <Button variant="ghost" size="sm" title="Delete" aria-label={`Delete ${row.title}`} disabled={busy === row.id} className="text-rose-600 hover:bg-rose-50"
                          onClick={() => window.confirm(`Delete "${row.title}" permanently? Consider deactivating instead.`) && act(row, () => propertyService.remove(row.id), 'Listing deleted.')}
                          icon={<Trash2 className="h-4 w-4" />} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={list.data.count} onChange={setPage} />
        </>
      )}

      {formOpen && (
        <PropertyFormModal
          open={formOpen}
          property={editing}
          onClose={() => setFormOpen(false)}
          onSaved={() => {
            setFormOpen(false)
            list.reload()
            onChanged()
          }}
        />
      )}
    </div>
  )
}

export function UsersTable() {
  const { user: me } = useAuth()
  const { notify } = useToast()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<Role | ''>('')
  const list = useAsync(() => adminService.users({ page, search: search.trim() || undefined, role }), [page, search, role])

  const update = async (id: number, payload: { role?: Role; is_active?: boolean }, message: string) => {
    try {
      const updated = await adminService.updateUser(id, payload)
      list.setData((current) => (current ? { ...current, results: current.results.map((u) => (u.id === id ? updated : u)) } : current))
      notify(message, 'success')
    } catch (error) {
      notify(toAppError(error).message, 'error')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <SearchBox value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search users by name or email" />
        <Select aria-label="Filter by role" value={role} onChange={(e) => { setRole(e.target.value as Role | ''); setPage(1) }} containerClassName="sm:w-40">
          <option value="">All roles</option>
          <option value="USER">Users</option>
          <option value="ADMIN">Admins</option>
        </Select>
      </div>
      {list.loading ? (
        <TableSkeleton />
      ) : list.error ? (
        <ErrorState error={list.error} onRetry={list.reload} />
      ) : !list.data?.results.length ? (
        <EmptyState title="No users found" />
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full min-w-[48rem] text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-4 py-3">User</th>
                  <th scope="col" className="px-4 py-3">Role</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3 text-right">Saves</th>
                  <th scope="col" className="px-4 py-3 text-right">Searches</th>
                  <th scope="col" className="px-4 py-3">Joined</th>
                  <th scope="col" className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {list.data.results.map((row) => {
                  const isMe = row.id === me?.id
                  return (
                    <tr key={row.id}>
                      <td className="px-4 py-3">
                        <p className="font-medium text-slate-900">{row.full_name || '—'} {isMe && <span className="text-xs text-slate-400">(you)</span>}</p>
                        <p className="text-xs text-slate-500">{row.email}</p>
                      </td>
                      <td className="px-4 py-3"><Badge tone={row.role === 'ADMIN' ? 'brand' : 'neutral'}>{row.role === 'ADMIN' ? 'Admin' : 'User'}</Badge></td>
                      <td className="px-4 py-3"><Badge tone={row.is_active ? 'success' : 'danger'}>{row.is_active ? 'Active' : 'Deactivated'}</Badge></td>
                      <td className="px-4 py-3 text-right tabular-nums">{row.favorites_count}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{row.recommendations_count}</td>
                      <td className="px-4 py-3 text-slate-500">{formatDate(row.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <Button variant="secondary" size="sm" disabled={isMe} icon={<ShieldCheck className="h-4 w-4" />}
                            onClick={() => update(row.id, { role: row.role === 'ADMIN' ? 'USER' : 'ADMIN' }, row.role === 'ADMIN' ? 'Admin role removed.' : 'User promoted to admin.')}>
                            {row.role === 'ADMIN' ? 'Make user' : 'Make admin'}
                          </Button>
                          <Button variant={row.is_active ? 'ghost' : 'secondary'} size="sm" disabled={isMe} className={row.is_active ? 'text-rose-600 hover:bg-rose-50' : ''}
                            onClick={() => update(row.id, { is_active: !row.is_active }, row.is_active ? 'User deactivated.' : 'User reactivated.')}>
                            {row.is_active ? 'Deactivate' : 'Reactivate'}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={list.data.count} onChange={setPage} />
        </>
      )}
    </div>
  )
}

export function InquiriesList() {
  const { notify } = useToast()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const list = useAsync(() => adminService.inquiries(page, status), [page, status])

  const setInquiryStatus = async (inquiry: Inquiry, next: Inquiry['status']) => {
    try {
      const updated = await adminService.updateInquiry(inquiry.id, next)
      list.setData((current) => (current ? { ...current, results: current.results.map((i) => (i.id === inquiry.id ? updated : i)) } : current))
      notify('Inquiry updated.', 'success')
    } catch (error) {
      notify(toAppError(error).message, 'error')
    }
  }

  return (
    <div className="space-y-4">
      <Select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }} containerClassName="sm:w-44">
        <option value="">All inquiries</option>
        <option value="new">New</option>
        <option value="responded">Responded</option>
        <option value="closed">Closed</option>
      </Select>
      {list.loading ? (
        <TableSkeleton />
      ) : list.error ? (
        <ErrorState error={list.error} onRetry={list.reload} />
      ) : !list.data?.results.length ? (
        <EmptyState title="No inquiries" description="Requests for information from users will appear here." />
      ) : (
        <>
          <ul className="space-y-3">
            {list.data.results.map((inquiry) => (
              <li key={inquiry.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <Link to={`/properties/${inquiry.property}`} className="font-medium text-slate-900 hover:text-brand-700">{inquiry.property_title}</Link>
                    <p className="text-xs text-slate-500">
                      {inquiry.user_name || inquiry.user_email} · {inquiry.user_email}{inquiry.phone && ` · ${inquiry.phone}`} · {formatDateTime(inquiry.created_at)}
                    </p>
                  </div>
                  <Select aria-label="Inquiry status" value={inquiry.status} onChange={(e) => setInquiryStatus(inquiry, e.target.value as Inquiry['status'])} className="!h-8 text-xs">
                    <option value="new">New</option>
                    <option value="responded">Responded</option>
                    <option value="closed">Closed</option>
                  </Select>
                </div>
                <p className="mt-2 whitespace-pre-line text-sm text-slate-700">{inquiry.message}</p>
              </li>
            ))}
          </ul>
          <Pagination page={page} pageSize={PAGE_SIZE} total={list.data.count} onChange={setPage} />
        </>
      )}
    </div>
  )
}
