import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Search, Filter, RefreshCw,
  Eye, PencilLine, Trash2, ToggleLeft, ToggleRight,
  Layers, TrendingUp, MousePointerClick, Activity,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { adsApi } from '@/services/serverApi';
import {
  PageHeader, StatCard, StatusBadge, Modal, ConfirmDialog,
  Skeleton, EmptyState, Spinner,
} from '@/components/ui';
import { AdForm } from './AdForm';
import { AD_CATEGORIES } from '@/constants';
import { cn, fmt } from '@/lib/utils';
import type { Ad, AdSummary, AdFormValues } from '@/types';
import toast from 'react-hot-toast';

const PAGE_SIZE = 12;

// ─── Ad Detail Drawer ─────────────────────────────────────────────────────────
function AdDetailModal({ ad, onClose }: { ad: Ad; onClose: () => void }) {
  return (
    <Modal open title={ad.title} onClose={onClose} wide>
      <div className="space-y-5">
        {ad.image_url && (
          <img src={ad.image_url.startsWith('/') ? `/api/server${ad.image_url}` : ad.image_url}
            alt={ad.title} className="w-full h-40 object-cover rounded-lg" />
        )}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <InfoRow label="Category"   value={ad.category} />
          <InfoRow label="Brand"      value={ad.brand ?? '—'} />
          <InfoRow label="Budget"     value={fmt.currency(ad.budget)} />
          <InfoRow label="Bid CPM"    value={fmt.currency(ad.bid_cpm)} />
          <InfoRow label="Impressions" value={fmt.number(ad.impression_count)} />
          <InfoRow label="Clicks"     value={fmt.number(ad.click_count)} />
          <InfoRow label="CTR"        value={fmt.percent(ad.ctr)} />
          <InfoRow label="Created"    value={fmt.date(ad.created_at)} />
        </div>
        <div>
          <p className="text-xs font-semibold text-word-3 uppercase tracking-wider mb-1.5">Description</p>
          <p className="text-sm text-word-2 leading-relaxed">{ad.description}</p>
        </div>
        {ad.keywords.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-word-3 uppercase tracking-wider mb-1.5">Keywords</p>
            <div className="flex flex-wrap gap-1.5">
              {ad.keywords.map(k => (
                <span key={k} className="badge-violet text-[11px]">{k}</span>
              ))}
            </div>
          </div>
        )}
        {ad.destination_url && (
          <div>
            <p className="text-xs font-semibold text-word-3 uppercase tracking-wider mb-1">Destination</p>
            <a href={ad.destination_url} target="_blank" rel="noopener noreferrer"
              className="text-xs text-violet-300 hover:text-violet-200 underline underline-offset-2 break-all">
              {ad.destination_url}
            </a>
          </div>
        )}
      </div>
    </Modal>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-word-3 mb-0.5">{label}</p>
      <p className="text-sm font-medium text-word-1">{value}</p>
    </div>
  );
}

// ─── Ad Table Row ─────────────────────────────────────────────────────────────
function AdRow({
  ad, onView, onEdit, onToggle, onDelete, toggleLoading,
}: {
  ad: AdSummary;
  onView: () => void;
  onEdit: () => void;
  onToggle: () => void;
  onDelete: () => void;
  toggleLoading: boolean;
}) {
  return (
    <motion.tr
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="group"
    >
      <td>
        <div className="font-mono text-[11px] text-word-3">#{ad.id}</div>
      </td>
      <td>
        <div className="font-medium text-word-1 truncate max-w-[240px]" title={ad.title}>{ad.title}</div>
        {ad.brand && <div className="text-xs text-word-3 mt-0.5">{ad.brand}</div>}
      </td>
      <td>
        <span className="badge-sun text-[10px]">{ad.category}</span>
      </td>
      <td>
        <StatusBadge active={ad.is_active} />
      </td>
      <td>
        <span className="font-mono text-xs">{fmt.number(ad.impression_count)}</span>
      </td>
      <td>
        <span className="font-mono text-xs">{fmt.number(ad.click_count)}</span>
      </td>
      <td>
        <span className={cn(
          'font-mono text-xs font-medium',
          (ad.ctr ?? 0) >= 0.05 ? 'text-jade-400' : (ad.ctr ?? 0) >= 0.02 ? 'text-sun-400' : 'text-word-2',
        )}>
          {fmt.percent(ad.ctr)}
        </span>
      </td>
      <td>
        <div className="text-xs text-word-3">{fmt.date(ad.created_at)}</div>
      </td>
      <td>
        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={onView} title="View" className="btn-icon btn-ghost p-1.5 rounded-lg">
            <Eye size={13} />
          </button>
          <button onClick={onEdit} title="Edit" className="btn-icon btn-ghost p-1.5 rounded-lg">
            <PencilLine size={13} />
          </button>
          <button onClick={onToggle} disabled={toggleLoading} title={ad.is_active ? 'Pause' : 'Activate'}
            className={cn('btn-icon btn-ghost p-1.5 rounded-lg', ad.is_active ? 'text-sun-400' : 'text-jade-400')}>
            {toggleLoading ? <Spinner /> : ad.is_active ? <ToggleRight size={13} /> : <ToggleLeft size={13} />}
          </button>
          <button onClick={onDelete} title="Delete" className="btn-icon btn-ghost p-1.5 rounded-lg text-coral-400">
            <Trash2 size={13} />
          </button>
        </div>
      </td>
    </motion.tr>
  );
}

// ─── AdsPage ──────────────────────────────────────────────────────────────────
export function AdsPage() {
  const qc = useQueryClient();

  // Filters
  const [page, setPage]         = useState(1);
  const [search, setSearch]     = useState('');
  const [catFilter, setCat]     = useState('');
  const [statusFilter, setSt]   = useState<'all' | 'active' | 'inactive'>('all');

  // Modal state
  const [showCreate, setShowCreate]   = useState(false);
  const [editAd, setEditAd]           = useState<Ad | null>(null);
  const [viewAd, setViewAd]           = useState<Ad | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; title: string } | null>(null);
  const [togglingId, setTogglingId]   = useState<number | null>(null);

  // ── Queries ──
  const adsQ = useQuery({
    queryKey: ['ads', page, catFilter, statusFilter],
    queryFn: () => adsApi.list({
      page, page_size: PAGE_SIZE,
      ...(catFilter ? { category: catFilter } : {}),
      ...(statusFilter === 'active' ? { active_only: true } : {}),
    }),
  });

  const overviewQ = useQuery({
    queryKey: ['overview-mini'],
    queryFn: () => import('@/services/serverApi').then(m => m.analyticsApi.overview(1)),
  });

  // ── Mutations ──
  const createMut = useMutation({
    mutationFn: (v: AdFormValues) => adsApi.create({
      ...v,
      image_url:       v.image_url || null,
      destination_url: v.destination_url || null,
      brand:           v.brand || null,
    }),
    onSuccess: () => {
      toast.success('Ad created successfully');
      qc.invalidateQueries({ queryKey: ['ads'] });
      qc.invalidateQueries({ queryKey: ['overview-mini'] });
      setShowCreate(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, v }: { id: number; v: AdFormValues }) => adsApi.update(id, {
      ...v,
      image_url:       v.image_url || null,
      destination_url: v.destination_url || null,
      brand:           v.brand || null,
    }),
    onSuccess: () => {
      toast.success('Ad updated');
      qc.invalidateQueries({ queryKey: ['ads'] });
      setEditAd(null);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const toggleMut = useMutation({
    mutationFn: (id: number) => adsApi.toggle(id),
    onSuccess: (updated) => {
      toast.success(`Ad ${updated.is_active ? 'activated' : 'paused'}`);
      qc.invalidateQueries({ queryKey: ['ads'] });
      setTogglingId(null);
    },
    onError: (e: Error) => { toast.error(e.message); setTogglingId(null); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => adsApi.remove(id),
    onSuccess: () => {
      toast.success('Ad deleted');
      qc.invalidateQueries({ queryKey: ['ads'] });
      qc.invalidateQueries({ queryKey: ['overview-mini'] });
      setDeleteTarget(null);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const handleViewAd = useCallback(async (id: number) => {
    const ad = await adsApi.get(id);
    setViewAd(ad);
  }, []);

  const handleEditAd = useCallback(async (id: number) => {
    const ad = await adsApi.get(id);
    setEditAd(ad);
  }, []);

  const handleToggle = (id: number) => { setTogglingId(id); toggleMut.mutate(id); };

  // Client-side search filter
  const filteredAds = (adsQ.data?.items ?? []).filter(a => {
    if (statusFilter === 'inactive' && a.is_active) return false;
    if (!search) return true;
    return [a.title, a.brand ?? '', a.category].join(' ').toLowerCase().includes(search.toLowerCase());
  });

  const totalPages = adsQ.data?.total_pages ?? 1;
  const ov = overviewQ.data;

  return (
    <div className="p-8">
      <PageHeader
        title="Ad Manager"
        subtitle="Create, monitor and control your entire ad inventory"
      >
        <button
          onClick={() => qc.invalidateQueries({ queryKey: ['ads'] })}
          className="btn-ghost btn p-2"
          title="Refresh"
        >
          <RefreshCw size={14} className={adsQ.isFetching ? 'animate-spin' : ''} />
        </button>
        <button onClick={() => setShowCreate(true)} className="btn-primary btn">
          <Plus size={15} /> New Ad
        </button>
      </PageHeader>

      {/* ── Mini stats ── */}
      {ov ? (
        <div className="grid grid-cols-4 gap-4 mb-8 animate-fade-up">
          <StatCard label="Total Ads"   value={ov.total_ads}                  sub={`${ov.active_ads} active`} icon={<Layers size={16} />} />
          <StatCard label="Impressions" value={fmt.number(ov.total_impressions)} icon={<TrendingUp size={16} />} />
          <StatCard label="Clicks"      value={fmt.number(ov.total_clicks)}    icon={<MousePointerClick size={16} />} />
          <StatCard label="Platform CTR" value={fmt.percent(ov.overall_ctr)}  accent="text-violet-400" icon={<Activity size={16} />} />
        </div>
      ) : (
        <div className="grid grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      )}

      {/* ── Filters ── */}
      <div className="flex items-center gap-3 mb-5">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-word-3 pointer-events-none" />
          <input
            className="field-input pl-9"
            placeholder="Search by title, brand, category…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* Category */}
        <div className="relative">
          <Filter size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-word-3 pointer-events-none" />
          <select
            className="field-input pl-8 w-44 appearance-none"
            value={catFilter}
            onChange={e => { setCat(e.target.value); setPage(1); }}
          >
            <option value="">All Categories</option>
            {AD_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {/* Status tabs */}
        <div className="tab-bar">
          {(['all', 'active', 'inactive'] as const).map(s => (
            <div
              key={s}
              className={cn('tab-item', statusFilter === s && 'active')}
              onClick={() => { setSt(s); setPage(1); }}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </div>
          ))}
        </div>

        <div className="ml-auto text-xs text-word-3">
          {adsQ.data?.total ?? 0} ads total
        </div>
      </div>

      {/* ── Table ── */}
      <div className="bg-ink-2 border border-edge-1 rounded-xl overflow-hidden">
        {adsQ.isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Spinner className="text-violet-400" />
          </div>
        ) : filteredAds.length === 0 ? (
          <EmptyState
            icon={<Layers size={24} />}
            title="No ads found"
            description="Try adjusting your filters or create your first ad"
            action={
              <button onClick={() => setShowCreate(true)} className="btn-primary btn">
                <Plus size={14} /> Create Ad
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-12">ID</th>
                  <th>Ad Creative</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Impressions</th>
                  <th>Clicks</th>
                  <th>CTR</th>
                  <th>Created</th>
                  <th className="w-32">Actions</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {filteredAds.map(ad => (
                    <AdRow
                      key={ad.id}
                      ad={ad}
                      onView={() => handleViewAd(ad.id)}
                      onEdit={() => handleEditAd(ad.id)}
                      onToggle={() => handleToggle(ad.id)}
                      onDelete={() => setDeleteTarget({ id: ad.id, title: ad.title })}
                      toggleLoading={togglingId === ad.id}
                    />
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Pagination ── */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-5">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="btn-secondary btn btn-sm"
          >← Prev</button>
          <span className="text-xs text-word-2 px-3">
            {page} / {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
            className="btn-secondary btn btn-sm"
          >Next →</button>
        </div>
      )}

      {/* ── Modals ── */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create New Ad" wide>
        <AdForm
          onSubmit={(v) => createMut.mutateAsync(v)}
          onCancel={() => setShowCreate(false)}
          isLoading={createMut.isPending}
        />
      </Modal>

      {editAd && (
        <Modal open onClose={() => setEditAd(null)} title={`Edit — ${editAd.title.slice(0, 50)}`} wide>
          <AdForm
            defaultValues={editAd}
            onSubmit={(v) => updateMut.mutateAsync({ id: editAd.id, v })}
            onCancel={() => setEditAd(null)}
            isLoading={updateMut.isPending}
          />
        </Modal>
      )}

      {viewAd && <AdDetailModal ad={viewAd} onClose={() => setViewAd(null)} />}

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}
        title="Delete Ad"
        message={`Are you sure you want to permanently delete "${deleteTarget?.title.slice(0, 60)}"? This cannot be undone.`}
        loading={deleteMut.isPending}
      />
    </div>
  );
}
