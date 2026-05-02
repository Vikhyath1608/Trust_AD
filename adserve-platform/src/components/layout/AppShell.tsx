import { type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Zap, Layers, BarChart3, FlaskConical,
  CircleDot,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useServerHealth } from '@/hooks/useServerHealth';

interface NavItem { to: string; label: string; icon: ReactNode; badge?: string; }

const NAV_ITEMS: NavItem[] = [
  { to: '/demo',      label: 'Live Demo',       icon: <FlaskConical size={16} /> },
  { to: '/ads',       label: 'Ad Manager',      icon: <Layers size={16} /> },
  { to: '/analytics', label: 'Analytics',       icon: <BarChart3 size={16} /> },
];

function ServerPill({ status }: { status: 'online' | 'offline' | 'pending' }) {
  return (
    <div className={cn(
      'flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border',
      status === 'online'  && 'bg-jade-400/10 text-jade-400 border-jade-400/20',
      status === 'offline' && 'bg-coral-400/10 text-coral-400 border-coral-400/20',
      status === 'pending' && 'bg-ink-4 text-word-3 border-edge-1',
    )}>
      <CircleDot size={9} className={cn(
        status === 'online'  && 'animate-pulse text-jade-400',
        status === 'offline' && 'text-coral-400',
        status === 'pending' && 'text-word-3',
      )} />
      {status === 'online' ? 'API Online' : status === 'offline' ? 'API Offline' : 'Connecting'}
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const { status } = useServerHealth();

  return (
    <div className="flex h-full min-h-screen">
      {/* ── Sidebar ── */}
      <aside className="w-[220px] min-w-[220px] flex flex-col bg-ink-1/80 backdrop-blur-xl border-r border-edge-1 fixed h-full z-40">
        {/* Brand */}
        <div className="px-5 py-5 border-b border-edge-1">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center shadow-glow-v">
              <Zap size={15} className="text-white" />
            </div>
            <div>
              <div className="font-semibold text-[15px] text-word-1 leading-none">AdServe</div>
              <div className="text-[10px] text-word-3 mt-0.5 tracking-widest uppercase">Platform</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          <div className="text-[10px] font-semibold text-word-3 uppercase tracking-widest px-3 mb-2">Navigation</div>
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'nav-link',
                pathname.startsWith(item.to) && 'active',
              )}
            >
              {item.icon}
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-edge-1">
          <ServerPill status={status} />
          <div className="mt-3 text-[10px] text-word-3 px-1">
            Client :8000 · Server :8001
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 ml-[220px] min-h-screen overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
