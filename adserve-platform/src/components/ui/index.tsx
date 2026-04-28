import { type ReactNode, forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { Loader2, X } from 'lucide-react';

// ─── Spinner ──────────────────────────────────────────────────────────────────
export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('animate-spin text-word-3', className)} size={16} />;
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton', className)} />;
}

// ─── PageHeader ───────────────────────────────────────────────────────────────
export function PageHeader({
  title, subtitle, children,
}: { title: string; subtitle?: string; children?: ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-7">
      <div>
        <h1 className="font-display text-2xl font-semibold text-word-1 leading-tight">{title}</h1>
        {subtitle && <p className="text-sm text-word-3 mt-1">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}

// ─── StatCard ─────────────────────────────────────────────────────────────────
export function StatCard({
  label, value, sub, accent, icon,
}: { label: string; value: string | number; sub?: string; accent?: string; icon?: ReactNode }) {
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-semibold text-word-3 uppercase tracking-wider mb-3">{label}</div>
          <div className={cn('text-3xl font-display font-semibold leading-none', accent ?? 'text-word-1')}>
            {value}
          </div>
          {sub && <div className="text-xs text-word-3 mt-2">{sub}</div>}
        </div>
        {icon && (
          <div className="w-9 h-9 rounded-lg bg-ink-4 flex items-center justify-center text-word-3">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── StatusBadge ──────────────────────────────────────────────────────────────
export function StatusBadge({ active }: { active: boolean }) {
  return active
    ? <span className="badge-green"><span className="w-1.5 h-1.5 rounded-full bg-jade-400 inline-block" /> Active</span>
    : <span className="badge-muted"><span className="w-1.5 h-1.5 rounded-full bg-word-3 inline-block" /> Paused</span>;
}

// ─── Toggle ───────────────────────────────────────────────────────────────────
export function Toggle({ checked, onChange, label }: {
  checked: boolean; onChange: (v: boolean) => void; label?: string;
}) {
  return (
    <label className="flex items-center gap-2.5 cursor-pointer group">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative rounded-full transition-all duration-200 flex-shrink-0 outline-none',
          'focus-visible:ring-2 focus-visible:ring-violet-500/40',
          checked ? 'bg-violet-500 border border-violet-400/50' : 'bg-ink-4 border border-edge-2',
        )}
        style={{ width: 40, height: 22 }}
      >
        <span
          className="absolute top-[3px] w-4 h-4 rounded-full bg-white shadow-sm transition-all duration-200"
          style={{ left: checked ? 22 : 3 }}
        />
      </button>
      {label && <span className="text-sm text-word-2 group-hover:text-word-1 transition-colors">{label}</span>}
    </label>
  );
}

// ─── Input ────────────────────────────────────────────────────────────────────
export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { error?: string }
>(({ className, error, ...props }, ref) => (
  <div>
    <input
      ref={ref}
      className={cn('field-input', error && 'border-coral-500/50 focus:border-coral-500/50', className)}
      {...props}
    />
    {error && <p className="field-error">{error}</p>}
  </div>
));
Input.displayName = 'Input';

// ─── Textarea ─────────────────────────────────────────────────────────────────
export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { error?: string }
>(({ className, error, ...props }, ref) => (
  <div>
    <textarea
      ref={ref}
      className={cn('field-input resize-none', error && 'border-coral-500/50', className)}
      {...props}
    />
    {error && <p className="field-error">{error}</p>}
  </div>
));
Textarea.displayName = 'Textarea';

// ─── Select ───────────────────────────────────────────────────────────────────
export const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => (
  <select ref={ref} className={cn('field-input', className)} {...props}>
    {children}
  </select>
));
Select.displayName = 'Select';

// ─── Modal ────────────────────────────────────────────────────────────────────
export function Modal({ open, onClose, title, children, wide }: {
  open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className={cn('modal-panel', wide && 'max-w-2xl')}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-edge-1">
          <h2 className="font-display font-semibold text-lg text-word-1">{title}</h2>
          <button onClick={onClose} className="btn-icon btn-ghost">
            <X size={16} />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

// ─── EmptyState ───────────────────────────────────────────────────────────────
export function EmptyState({ icon, title, description, action }: {
  icon: ReactNode; title: string; description?: string; action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-14 h-14 rounded-2xl bg-ink-3 flex items-center justify-center text-word-3 mb-4">
        {icon}
      </div>
      <h3 className="font-display font-medium text-base text-word-1 mb-1">{title}</h3>
      {description && <p className="text-sm text-word-3 max-w-xs">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

// ─── ConfirmDialog ────────────────────────────────────────────────────────────
export function ConfirmDialog({ open, onClose, onConfirm, title, message, loading }: {
  open: boolean; onClose: () => void; onConfirm: () => void;
  title: string; message: string; loading?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="bg-ink-2/90 backdrop-blur-2xl border border-edge-2 shadow-card rounded-2xl w-full max-w-sm p-6 animate-scale-in"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="font-display font-semibold text-base text-word-1 mb-2">{title}</h3>
        <p className="text-sm text-word-2 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button onClick={onConfirm} disabled={loading} className="btn btn-danger">
            {loading ? <Spinner className="text-coral-400" /> : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}
