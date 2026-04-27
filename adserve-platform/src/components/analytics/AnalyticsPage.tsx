import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp, MousePointerClick, Activity,
  Layers, Zap, Crown,
} from 'lucide-react';
import { analyticsApi } from '@/services/serverApi';
import { PageHeader, StatCard, Skeleton, EmptyState } from '@/components/ui';
import { CHART_COLORS } from '@/constants';
import { fmt } from '@/lib/utils';
import type { CategoryStat } from '@/types';

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-ink-3 border border-edge-2 rounded-xl p-3 shadow-float text-xs">
      {label && <div className="text-word-2 mb-2 font-medium">{label}</div>}
      {payload.map(p => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: p.color }} />
          <span className="text-word-2">{p.name}:</span>
          <span className="text-word-1 font-medium font-mono">{fmt.number(p.value)}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Section Title ─────────────────────────────────────────────────────────────
function SectionTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-4">
      <h3 className="font-semibold text-sm text-word-1">{title}</h3>
      {sub && <p className="text-xs text-word-3 mt-0.5">{sub}</p>}
    </div>
  );
}

// ─── Keyword Bar ──────────────────────────────────────────────────────────────
function KeywordBar({ name, count, max, color }: { name: string; count: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="w-24 text-xs text-word-2 truncate flex-shrink-0">{name}</div>
      <div className="flex-1 h-1.5 rounded-full bg-ink-4 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <div className="w-7 text-right font-mono text-[11px] text-word-3">{count}</div>
    </div>
  );
}

// ─── AnalyticsPage ────────────────────────────────────────────────────────────
export function AnalyticsPage() {
  const overviewQ = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: () => analyticsApi.overview(8),
  });
  const timeQ = useQuery({
    queryKey: ['analytics-time'],
    queryFn: () => analyticsApi.timeSeries(),
  });
  const kwQ = useQuery({
    queryKey: ['analytics-kw'],
    queryFn: () => analyticsApi.keywords(12),
  });

  const ov  = overviewQ.data;
  const ts  = timeQ.data?.series ?? [];
  const kws = Object.entries(kwQ.data?.keywords ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const maxKw = kws[0]?.[1] ?? 1;

  // Category data
  const catBars = (ov?.top_categories ?? []).map((c: CategoryStat) => ({
    name: c.category.length > 13 ? c.category.slice(0, 13) + '…' : c.category,
    Impressions: c.total_impressions,
    Clicks: c.total_clicks,
    Ads: c.ad_count,
  }));
  const pieData = (ov?.top_categories ?? []).map((c: CategoryStat) => ({
    name: c.category, value: c.ad_count,
  }));

  const isLoading = overviewQ.isLoading;

  return (
    <div className="p-8">
      <PageHeader
        title="Analytics"
        subtitle="Platform-wide performance — impressions, CTR, category breakdown"
      />

      {/* ── KPI Strip ── */}
      {isLoading ? (
        <div className="grid grid-cols-5 gap-4 mb-8">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : ov ? (
        <div className="grid grid-cols-5 gap-4 mb-8 animate-fade-up">
          <StatCard label="Total Ads"    value={ov.total_ads}                    sub={`${ov.inactive_ads} inactive`} icon={<Layers size={16} />} />
          <StatCard label="Active"       value={ov.active_ads}                   sub="Serving now"   accent="text-jade-400" icon={<Zap size={16} />} />
          <StatCard label="Impressions"  value={fmt.number(ov.total_impressions)} sub="All time"     icon={<TrendingUp size={16} />} />
          <StatCard label="Clicks"       value={fmt.number(ov.total_clicks)}      sub="All time"     icon={<MousePointerClick size={16} />} />
          <StatCard label="Platform CTR" value={fmt.percent(ov.overall_ctr)}      sub="Overall rate" accent="text-violet-400" icon={<Activity size={16} />} />
        </div>
      ) : null}

      {/* ── Full-width trend ── */}
      <div className="card mb-5 animate-fade-up" style={{ animationDelay: '60ms' }}>
        <SectionTitle title="Daily Impressions Trend" />
        {timeQ.isLoading ? <Skeleton className="h-44" /> : ts.length > 0 ? (
          <ResponsiveContainer width="100%" height={176}>
            <LineChart data={ts}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#4e4e6a' }} tickFormatter={d => d.slice(5)} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#4e4e6a' }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Line type="monotone" dataKey="impressions" stroke={CHART_COLORS[0]} strokeWidth={2.5} dot={false} activeDot={{ r: 5, fill: CHART_COLORS[0] }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState icon={<TrendingUp size={20} />} title="No impression data yet" description="Run the demo to generate impressions" />
        )}
      </div>

      {/* ── Row 2: Category bar + Pie ── */}
      <div className="grid grid-cols-[3fr_2fr] gap-5 mb-5">
        <div className="card animate-fade-up" style={{ animationDelay: '100ms' }}>
          <SectionTitle title="Impressions & Clicks by Category" />
          {isLoading ? <Skeleton className="h-52" /> : catBars.length > 0 ? (
            <ResponsiveContainer width="100%" height={208}>
              <BarChart data={catBars}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#4e4e6a' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#4e4e6a' }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="Impressions" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} maxBarSize={18} />
                <Bar dataKey="Clicks" fill={CHART_COLORS[1]} radius={[4, 4, 0, 0]} maxBarSize={18} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState icon={<Activity size={20} />} title="No category data" description="Create ads across categories to see breakdown" />
          )}
        </div>

        <div className="card animate-fade-up" style={{ animationDelay: '130ms' }}>
          <SectionTitle title="Ad Mix by Category" />
          {isLoading ? <Skeleton className="h-52" /> : pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={150}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" cx="50%" cy="50%" innerRadius={40} outerRadius={68} paddingAngle={2}>
                    {pieData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1.5 mt-3">
                {pieData.slice(0, 5).map((d, i) => (
                  <div key={d.name} className="flex items-center gap-2 text-xs">
                    <span className="w-2 h-2 rounded-sm flex-shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                    <span className="text-word-2 flex-1 truncate">{d.name}</span>
                    <span className="font-mono text-word-3">{d.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <EmptyState icon={<Layers size={20} />} title="No data" />
          )}
        </div>
      </div>

      {/* ── Row 3: Keywords + Top CTR ── */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <div className="card animate-fade-up" style={{ animationDelay: '160ms' }}>
          <SectionTitle title="Keyword Frequency" sub="Most-used targeting keywords" />
          {kwQ.isLoading ? (
            <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-4" />)}</div>
          ) : kws.length > 0 ? (
            <div className="space-y-2.5">
              {kws.map(([name, count], i) => (
                <KeywordBar key={name} name={name} count={count} max={maxKw} color={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </div>
          ) : (
            <EmptyState icon={<Activity size={20} />} title="No keywords yet" />
          )}
        </div>

        <div className="card animate-fade-up" style={{ animationDelay: '190ms' }}>
          <SectionTitle title="Top Ads by CTR" sub="Min. 5 impressions required" />
          {isLoading ? (
            <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : (ov?.top_ads_by_ctr ?? []).length > 0 ? (
            <div className="space-y-2">
              {(ov?.top_ads_by_ctr ?? []).slice(0, 6).map((ad, i) => (
                <div key={ad.ad_id} className="flex items-center gap-3 p-2.5 rounded-lg bg-ink-3/40 hover:bg-ink-3 transition-colors">
                  <div
                    className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                    style={{ background: `${CHART_COLORS[i % CHART_COLORS.length]}15`, color: CHART_COLORS[i % CHART_COLORS.length] }}
                  >
                    {i === 0 ? <Crown size={11} /> : i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-word-1 truncate">{ad.title}</div>
                    <div className="text-[10px] text-word-3 mt-0.5">{ad.category}</div>
                  </div>
                  <div className="text-xs font-mono font-semibold text-jade-400">
                    {fmt.percent(ad.ctr)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={<Crown size={20} />} title="No CTR data" description="Need at least 5 impressions per ad" />
          )}
        </div>
      </div>

      {/* ── Row 4: Top by Impressions ── */}
      {ov && (ov.top_ads_by_impressions?.length ?? 0) > 0 && (
        <div className="card animate-fade-up" style={{ animationDelay: '220ms' }}>
          <SectionTitle title="Top Ads by Impressions" />
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-8">#</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Impressions</th>
                  <th>Clicks</th>
                  <th>CTR</th>
                  <th>Budget</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {ov.top_ads_by_impressions.map((ad, i) => (
                  <tr key={ad.ad_id}>
                    <td>
                      <div className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold"
                        style={{ background: `${CHART_COLORS[i % CHART_COLORS.length]}15`, color: CHART_COLORS[i % CHART_COLORS.length] }}>
                        {i + 1}
                      </div>
                    </td>
                    <td><div className="font-medium truncate max-w-[220px]" title={ad.title}>{ad.title}</div></td>
                    <td><span className="badge-sun text-[10px]">{ad.category}</span></td>
                    <td><span className="font-mono text-xs">{fmt.number(ad.impression_count)}</span></td>
                    <td><span className="font-mono text-xs">{fmt.number(ad.click_count)}</span></td>
                    <td><span className="font-mono text-xs text-jade-400 font-semibold">{fmt.percent(ad.ctr)}</span></td>
                    <td><span className="font-mono text-xs">{fmt.currency(ad.budget)}</span></td>
                    <td>
                      {ad.is_active
                        ? <span className="badge-green text-[10px]">Active</span>
                        : <span className="badge-muted text-[10px]">Paused</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
