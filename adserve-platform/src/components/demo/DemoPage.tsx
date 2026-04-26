
// import { useState, useCallback } from 'react';
// import {
//   Globe, Brain, Target, Sparkles,
//   ChevronRight, RotateCcw, AlertTriangle,
//   MousePointerClick, ExternalLink, Clock, Cpu,
//   TrendingUp, Tag, Flame, FolderDown, CheckCircle2,
//   FileSpreadsheet, Chrome, Zap, UserPlus, X,
//   Mail, FolderOpen, Play, User,
// } from 'lucide-react';
// import { motion, AnimatePresence } from 'framer-motion';
// import { PageHeader, Spinner, Modal } from '@/components/ui';
// import { usePipeline } from '@/hooks/usePipeline';
// import { type ExportHistoryResponse } from '@/services/clientApi';
// import { adsApi } from '@/services/serverApi';
// import {DEMO_USERS, LIVE_PROFILES, CHART_COLORS } from '@/constants';
// import { cn, scoreColor } from '@/lib/utils';
// import type { InterestSignal, ServedAd, PipelineStage } from '@/types';
// import toast from 'react-hot-toast';

// // ─── Types ────────────────────────────────────────────────────────────────────
// interface Profile {
//   name: string;
//   email: string;
//   chrome_path: string;
//   color: string;
//   user_id: string;
// }

// // ─── Helpers ──────────────────────────────────────────────────────────────────
// function slugify(name: string): string {
//   return name.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
// }

// function initials(name: string): string {
//   return name.trim().split(/\s+/).map(w => w[0]?.toUpperCase() ?? '').join('').slice(0, 2);
// }

// const PALETTE = [
//   '#8b5cf6', '#34d399', '#fbbf24', '#f87171',
//   '#38bdf8', '#a78bfa', '#f97316', '#e879f9', '#84cc16', '#06b6d4',
// ];

// const SEED_PROFILES: Profile[] = (LIVE_PROFILES as unknown as Array<{
//   name: string; email: string; chrome_path: string; color: string;
// }>).map(p => ({ ...p, user_id: slugify(p.name) }));

// // ─── Pipeline Steps ───────────────────────────────────────────────────────────
// const PIPELINE_STEPS = [
//   { id: 'extracting', label: 'Browser History',  sublabel: 'Client side',    icon: Globe },
//   { id: 'extracted',  label: 'Interest Signals', sublabel: 'ML extraction',  icon: Brain },
//   { id: 'serving',    label: 'Ad Matching',       sublabel: 'Server ranking', icon: Target },
//   { id: 'complete',   label: 'Ads Delivered',     sublabel: 'Personalised',   icon: Sparkles },
// ] as const;

// // ─── Add Profile Modal ────────────────────────────────────────────────────────
// function AddProfileModal({ open, onClose, onAdd, nextColor }: {
//   open: boolean;
//   onClose: () => void;
//   onAdd: (p: Profile) => void;
//   nextColor: string;
// }) {
//   const [name, setName]   = useState('');
//   const [email, setEmail] = useState('');
//   const [path, setPath]   = useState('');
//   const [color, setColor] = useState(nextColor);
//   const userId = slugify(name);

//   const handleAdd = () => {
//     if (!name.trim()) { toast.error('Name is required'); return; }
//     if (!path.trim()) { toast.error('Chrome path is required'); return; }
//     onAdd({ name: name.trim(), email: email.trim(), chrome_path: path.trim(), color, user_id: userId });
//     setName(''); setEmail(''); setPath('');
//     onClose();
//     toast.success(`Profile "${name.trim()}" added`);
//   };

//   return (
//     <Modal open={open} onClose={onClose} title="Add Profile">
//       <div className="space-y-4">
//         <div>
//           <label className="field-label flex items-center gap-1.5">
//             <User size={11} /> Display Name
//           </label>
//           <input
//             className="field-input"
//             placeholder="e.g. Vikhyath"
//             value={name}
//             onChange={e => setName(e.target.value)}
//           />
//           {name.trim() && (
//             <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-word-3">
//               <span>Auto user ID:</span>
//               <code className="font-mono text-violet-400 bg-ink-3 px-1.5 py-0.5 rounded">{userId}</code>
//             </div>
//           )}
//         </div>

//         <div>
//           <label className="field-label flex items-center gap-1.5">
//             <Mail size={11} /> Email (optional)
//           </label>
//           <input
//             className="field-input"
//             placeholder="e.g. vikhyath@example.com"
//             value={email}
//             onChange={e => setEmail(e.target.value)}
//           />
//         </div>

//         <div>
//           <label className="field-label flex items-center gap-1.5">
//             <FolderOpen size={11} /> Chrome Profile Path
//           </label>
//           <input
//             className="field-input font-mono text-xs"
//             placeholder="C:\Users\...\AppData\Local\Google\Chrome\User Data\Profile 3"
//             value={path}
//             onChange={e => setPath(e.target.value)}
//           />
//           <p className="text-[11px] text-word-3 mt-1.5">
//             Find it at: <code className="font-mono text-word-2">chrome://version</code> → Profile Path
//           </p>
//         </div>

//         <div>
//           <label className="field-label">Avatar Colour</label>
//           <div className="flex items-center gap-2 flex-wrap">
//             {PALETTE.map(c => (
//               <button
//                 key={c}
//                 type="button"
//                 onClick={() => setColor(c)}
//                 className={cn(
//                   'w-7 h-7 rounded-lg transition-all duration-150',
//                   color === c ? 'ring-2 ring-white/50 scale-110' : 'opacity-60 hover:opacity-100',
//                 )}
//                 style={{ background: c }}
//               />
//             ))}
//           </div>
//         </div>

//         {name.trim() && (
//           <div className="flex items-center gap-3 p-3 bg-ink-3 rounded-xl border border-edge-1">
//             <div
//               className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0"
//               style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}
//             >
//               {initials(name)}
//             </div>
//             <div>
//               <div className="text-sm font-semibold text-word-1">{name.trim()}</div>
//               {email && <div className="text-xs text-word-3">{email}</div>}
//               <code className="text-[10px] font-mono text-violet-400">{userId}</code>
//             </div>
//           </div>
//         )}

//         <div className="flex justify-end gap-3 pt-1">
//           <button onClick={onClose} className="btn btn-secondary">Cancel</button>
//           <button onClick={handleAdd} className="btn btn-primary">Add Profile</button>
//         </div>
//       </div>
//     </Modal>
//   );
// }

// // ─── Profile Card ─────────────────────────────────────────────────────────────
// function ProfileCard({ profile, active, running, exportResult, onSelect, onRemove }: {
//   profile: Profile;
//   active: boolean;
//   running: boolean;
//   exportResult: ExportHistoryResponse | null;
//   onSelect: () => void;
//   onRemove: () => void;
// }) {
//   return (
//     <motion.div
//       layout
//       initial={{ opacity: 0, scale: 0.95 }}
//       animate={{ opacity: 1, scale: 1 }}
//       exit={{ opacity: 0, scale: 0.9 }}
//       className={cn(
//         'relative flex flex-col gap-3 p-4 rounded-xl border transition-all duration-200',
//         active
//           ? 'bg-ink-3 border-violet-500/50 shadow-glow-v'
//           : 'bg-ink-2 border-edge-1 hover:border-edge-2 hover:bg-ink-3',
//       )}
//     >
//       <button
//         onClick={e => { e.stopPropagation(); onRemove(); }}
//         className="absolute top-2 right-2 w-5 h-5 rounded-full bg-ink-4 border border-edge-1
//                    flex items-center justify-center text-word-3
//                    hover:text-coral-400 hover:border-coral-400/30
//                    transition-all opacity-0 group-hover:opacity-100"
//         title="Remove profile"
//       >
//         <X size={10} />
//       </button>

//       <div className="flex items-center gap-3">
//         <div
//           className="w-11 h-11 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0"
//           style={{ background: `${profile.color}18`, color: profile.color, border: `1px solid ${profile.color}35` }}
//         >
//           {initials(profile.name)}
//         </div>
//         <div className="min-w-0">
//           <div className="text-sm font-semibold text-word-1 truncate">{profile.name}</div>
//           {profile.email && (
//             <div className="text-[11px] text-word-3 truncate flex items-center gap-1">
//               <Mail size={9} />{profile.email}
//             </div>
//           )}
//           <code className="text-[10px] font-mono text-violet-400">{profile.user_id}</code>
//         </div>
//       </div>

//       <div className="flex items-start gap-1.5 bg-ink-3/80 rounded-lg px-2.5 py-2 border border-edge-1">
//         <Chrome size={10} className="text-sky-400 mt-0.5 flex-shrink-0" />
//         <span
//           className="text-[10px] font-mono text-word-3 leading-relaxed break-all line-clamp-2"
//           title={profile.chrome_path}
//         >
//           {profile.chrome_path}
//         </span>
//       </div>

//       {exportResult && active && (
//         <div className="flex items-center gap-1.5 text-[10px] text-jade-400">
//           <CheckCircle2 size={10} />
//           <span>{exportResult.rows_exported.toLocaleString()} rows exported</span>
//         </div>
//       )}

//       <button
//         onClick={onSelect}
//         disabled={running}
//         className={cn(
//           'w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold',
//           'transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed active:scale-95',
//           active && running
//             ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
//             : 'bg-violet-500 hover:bg-violet-600 text-white',
//         )}
//       >
//         {active && running
//           ? <><Spinner className="text-violet-300" /> Running…</>
//           : <><Play size={11} /> Run Analysis</>
//         }
//       </button>
//     </motion.div>
//   );
// }
// // ─── User Card ─────────────────────────────────────────────────────────────────
// function UserCard({ user, active, running, onSelect }: {
//   user: typeof DEMO_USERS[number]; active: boolean; running: boolean; onSelect: () => void;
// }) {
//   return (
//     <button
//       onClick={onSelect}
//       disabled={running}
//       className={cn(
//         'relative flex flex-col items-center gap-2.5 p-4 rounded-xl border',
//         'transition-all duration-200 cursor-pointer group',
//         'disabled:opacity-50 disabled:cursor-not-allowed',
//         active ? 'bg-ink-3 border-violet-500/40 shadow-glow-v' : 'bg-ink-2 border-edge-1 hover:border-edge-2 hover:bg-ink-3',
//       )}
//     >
//       <div
//         className="w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold"
//         style={{ background: `${user.color}18`, color: user.color, border: `1px solid ${user.color}30` }}
//       >
//         {user.initials}
//       </div>
//       <span className="text-xs font-medium text-word-2 group-hover:text-word-1 transition-colors">
//         {user.id.replace('_', ' #')}
//       </span>
//       {active && running && (
//         <span className="absolute top-2 right-2"><Spinner className="text-violet-400" /></span>
//       )}
//     </button>
//   );
// }

// // ─── Pipeline Visualiser ───────────────────────────────────────────────────────
// function PipelineVis({ stage }: { stage: PipelineStage }) {
//   const stageOrder: PipelineStage[] = ['extracting', 'extracted', 'serving', 'complete'];
//   const current = stageOrder.indexOf(stage);

//   return (
//     <div className="flex items-center p-5 bg-ink-2 border border-edge-1 rounded-xl overflow-x-auto">
//       {PIPELINE_STEPS.map((step, i) => {
//         const Icon = step.icon;
//         const stepIdx  = stageOrder.indexOf(step.id as PipelineStage);
//         const isActive = stage === step.id;
//         const isDone   = current > stepIdx || stage === 'complete';
//         const isError  = stage === 'error';

//         let nodeState: 'idle' | 'running' | 'done' | 'error' = 'idle';
//         if (isError && isActive) nodeState = 'error';
//         else if (isDone)         nodeState = 'done';
//         else if (isActive)       nodeState = 'running';

//         return (
//           <div key={step.id} className="flex items-center flex-1 min-w-0">
//             <div className="flex flex-col items-center gap-1.5 min-w-[80px]">
//               <div className={cn('pipe-icon', nodeState)}>
//                 {nodeState === 'running' ? <Spinner className="text-violet-400" /> : <Icon size={20} />}
//               </div>
//               <span className={cn(
//                 'text-xs font-medium text-center leading-tight',
//                 nodeState === 'done'    && 'text-jade-400',
//                 nodeState === 'running' && 'text-violet-300',
//                 nodeState === 'idle'    && 'text-word-3',
//                 nodeState === 'error'   && 'text-coral-400',
//               )}>
//                 {step.label}
//               </span>
//               <span className="text-[10px] text-word-3 text-center">{step.sublabel}</span>
//             </div>
//             {i < PIPELINE_STEPS.length - 1 && (
//               <div className={cn(
//                 'flex-1 h-px mx-2 min-w-[20px] transition-all duration-500',
//                 isDone   ? 'bg-gradient-to-r from-jade-400/50 to-jade-400/20' :
//                 isActive ? 'bg-gradient-to-r from-violet-500/60 to-transparent animate-flow' :
//                            'bg-edge-1',
//               )} />
//             )}
//           </div>
//         );
//       })}
//     </div>
//   );
// }

// // ─── Signal Card ──────────────────────────────────────────────────────────────
// function SignalCard({ num, label, data, color, isHighlight }: {
//   num: number;
//   label: string;
//   data: InterestSignal | null;
//   color: string;
//   isHighlight?: boolean;
// }) {
//   return (
//     <motion.div
//       initial={{ opacity: 0, y: 10 }}
//       animate={{ opacity: 1, y: 0 }}
//       transition={{ delay: num * 0.07 }}
//       className={cn(
//         'bg-ink-2 border rounded-xl p-4 flex flex-col gap-3 relative overflow-hidden',
//         isHighlight ? 'border-amber-400/40' : 'border-edge-1',
//       )}
//     >
//       {isHighlight && (
//         <div className="absolute top-0 right-0 px-2 py-0.5 bg-amber-400/15 border-b border-l border-amber-400/30 rounded-bl-lg">
//           <div className="flex items-center gap-1 text-[9px] font-bold text-amber-400 uppercase tracking-wider">
//             <Flame size={8} /> High
//           </div>
//         </div>
//       )}
//       <div className="flex items-center gap-2">
//         <div
//           className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider"
//           style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
//         >
//           SIG {num}
//         </div>
//         <span className="text-xs text-word-3">{label}</span>
//       </div>
//       {data ? (
//         <div className="space-y-1.5">
//           {data.category && (
//             <div className="flex items-center gap-1.5 flex-wrap">
//               <span className="badge-violet text-[10px]">{data.category}</span>
//               {data.subcategory && <span className="badge-sky text-[10px]">{data.subcategory}</span>}
//             </div>
//           )}
//           {data.product && (
//             <div className="text-sm font-semibold text-word-1 leading-snug">{data.product}</div>
//           )}
//           {data.brand && (
//             <div className="text-xs text-word-2">{data.brand}</div>
//           )}
//           {data.query && (
//             <div className="text-xs text-word-3 italic">"{data.query}"</div>
//           )}
//           {data.total_engagement_score != null && (
//             <div className="text-[10px] text-word-3 font-mono">
//               score: {Number(data.total_engagement_score).toFixed(1)}
//             </div>
//           )}
//         </div>
//       ) : (
//         <div className="text-xs text-word-3 italic">No signal available</div>
//       )}
//     </motion.div>
//   );
// }

// // ─── High Interest Banner ─────────────────────────────────────────────────────
// function HighInterestBanner({ category, multiplier }: { category: string; multiplier: number }) {
//   return (
//     <motion.div
//       initial={{ opacity: 0, scale: 0.97 }}
//       animate={{ opacity: 1, scale: 1 }}
//       className="mb-5 relative overflow-hidden rounded-xl border border-amber-400/30 p-4"
//       style={{ background: 'linear-gradient(to right, rgba(245,158,11,0.10), rgba(249,115,22,0.08), rgba(251,191,36,0.10))' }}
//     >
//       <div className="flex items-center gap-4">
//         <div className="w-10 h-10 rounded-xl bg-amber-400/15 border border-amber-400/30 flex items-center justify-center flex-shrink-0">
//           <Flame size={18} className="text-amber-400" />
//         </div>
//         <div className="flex-1 min-w-0">
//           <div className="flex items-center gap-2 mb-0.5">
//             <span className="text-sm font-bold text-amber-300">High-Interest Signal Detected</span>
//             <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-400/20 border border-amber-400/40 text-amber-300 uppercase tracking-wider">
//               Premium
//             </span>
//           </div>
//           <p className="text-xs leading-relaxed" style={{ color: 'rgba(253,230,138,0.6)' }}>
//             Both most recent browsing and dominant product interest point to{' '}
//             <span className="font-semibold text-amber-300">{category}</span>.
//             Strong purchase intent — ads carry a{' '}
//             <span className="font-semibold text-amber-300">{multiplier}× CPM premium</span>.
//           </p>
//         </div>
//         <div className="text-right flex-shrink-0">
//           <div className="text-2xl font-bold text-amber-300">{multiplier}×</div>
//           <div className="text-[10px] uppercase tracking-wider" style={{ color: 'rgba(251,191,36,0.6)' }}>CPM rate</div>
//         </div>
//       </div>
//     </motion.div>
//   );
// }

// // ─── Ad Result Card ───────────────────────────────────────────────────────────
// function AdResultCard({ ad, rank, userId, delay, isHighInterest, premiumCpm }: {
//   ad: ServedAd;
//   rank: number;
//   userId: string;
//   delay: number;
//   isHighInterest: boolean;
//   premiumCpm: number;
// }) {
//   const [clicked, setClicked] = useState(false);
//   const score    = ad.relevance_score ?? 0;
//   const scoreVal = Math.round(score * 100);

//   const handleClick = async () => {
//     setClicked(true);
//     await adsApi.recordClick(ad.ad_id, { impression_id: ad.impression_id ?? undefined, user_id: userId });
//     toast.success('Click recorded');
//   };

//   return (
//     <motion.div
//       initial={{ opacity: 0, y: 16 }}
//       animate={{ opacity: 1, y: 0 }}
//       transition={{ delay, ease: [0.16, 1, 0.3, 1] }}
//       className={cn('ad-card relative', isHighInterest && 'ring-1 ring-amber-400/30')}
//     >
//       {isHighInterest && (
//         <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center gap-1.5 py-1.5 backdrop-blur-sm"
//           style={{ background: 'linear-gradient(to right, rgba(245,158,11,0.8), rgba(251,191,36,0.9), rgba(249,115,22,0.8))' }}
//         >
//           <Flame size={11} className="text-amber-900" />
//           <span className="text-[10px] font-bold text-amber-900 uppercase tracking-wider">
//             High-Interest · {premiumCpm}× Premium CPM
//           </span>
//           <Zap size={10} className="text-amber-900" />
//         </div>
//       )}

//       <div className={cn('relative bg-ink-3 overflow-hidden aspect-[16/7]', isHighInterest && 'mt-7')}>
//         {ad.image_url ? (
//           <img
//             src={ad.image_url.startsWith('/') ? `/api/server${ad.image_url}` : ad.image_url}
//             alt={ad.title}
//             className="w-full h-full object-cover"
//           />
//         ) : (
//           <div className="w-full h-full flex items-center justify-center">
//             <div className="text-4xl opacity-10">◈</div>
//           </div>
//         )}
//         <div className="absolute top-3 left-3 w-7 h-7 rounded-lg bg-canvas/80 backdrop-blur-sm flex items-center justify-center text-xs font-bold text-word-1 border border-edge-2">
//           {rank}
//         </div>
//         <div
//           className="absolute top-3 right-3 px-2 py-0.5 rounded-lg bg-canvas/80 backdrop-blur-sm border border-edge-2 font-mono text-xs font-medium"
//           style={{ color: scoreColor(score) }}
//         >
//           {scoreVal}%
//         </div>
//       </div>

//       <div className="p-4 flex flex-col gap-3">
//         <div className="flex items-center gap-1.5 flex-wrap">
//           <span className="badge-sun text-[10px]">{ad.category}</span>
//           {ad.brand && <span className="badge-sky text-[10px]">{ad.brand}</span>}
//           {isHighInterest && (
//             <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-400/15 border border-amber-400/30 text-amber-300">
//               <Flame size={8} /> High-Interest
//             </span>
//           )}
//         </div>

//         <div>
//           <h3 className="text-sm font-semibold text-word-1 leading-snug mb-0.5">{ad.title}</h3>
//           <p className="text-xs text-word-2 line-clamp-2 leading-relaxed">{ad.description}</p>
//         </div>

//         {isHighInterest && (
//           <div className="flex items-center gap-2 p-2.5 rounded-lg border border-amber-400/20"
//             style={{ background: 'rgba(251,191,36,0.08)' }}
//           >
//             <Zap size={12} className="text-amber-400 flex-shrink-0" />
//             <div>
//               <div className="text-[10px] text-amber-400/70 uppercase tracking-wider">Premium Bid Rate</div>
//               <div className="text-xs font-mono font-bold text-amber-300">{premiumCpm}× standard CPM</div>
//             </div>
//           </div>
//         )}

//         <div className="bg-ink-3 rounded-lg p-3 space-y-2">
//           {([
//             ['Category', ad.matched_signals.category_score, CHART_COLORS[0]],
//             ['Keyword',  ad.matched_signals.keyword_score,  CHART_COLORS[1]],
//             ['Brand',    ad.matched_signals.brand_score,    CHART_COLORS[2]],
//           ] as [string, number, string][]).map(([lbl, val, col]) => (
//             <div key={lbl} className="flex items-center gap-2">
//               <span className="text-[10px] text-word-3 w-14 flex-shrink-0">{lbl}</span>
//               <div className="flex-1 score-track">
//                 <motion.div
//                   className="score-fill"
//                   initial={{ width: 0 }}
//                   animate={{ width: `${Math.round((val ?? 0) * 100)}%` }}
//                   transition={{ delay: delay + 0.2, duration: 0.7, ease: 'easeOut' }}
//                   style={{ background: col }}
//                 />
//               </div>
//               <span className="text-[10px] font-mono text-word-2 w-8 text-right">
//                 {Math.round((val ?? 0) * 100)}%
//               </span>
//             </div>
//           ))}
//         </div>

//         {ad.keywords?.length > 0 && (
//           <div className="flex flex-wrap gap-1">
//             {ad.keywords.slice(0, 4).map(kw => (
//               <span key={kw} className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-ink-4 border border-edge-1 text-word-3">
//                 <Tag size={8} />{kw}
//               </span>
//             ))}
//           </div>
//         )}

//         <div className="flex gap-2 pt-1">
//           <button
//             onClick={handleClick}
//             disabled={clicked}
//             className={cn(
//               'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200',
//               clicked
//                 ? 'bg-jade-400/10 text-jade-400 border border-jade-400/20'
//                 : isHighInterest
//                   ? 'text-white active:scale-95'
//                   : 'bg-violet-500 hover:bg-violet-600 text-white active:scale-95',
//             )}
//             style={!clicked && isHighInterest ? {
//               background: 'linear-gradient(to right, #f59e0b, #f97316)',
//             } : undefined}
//           >
//             {clicked
//               ? <><TrendingUp size={12} /> Clicked!</>
//               : <><MousePointerClick size={12} /> Visit Ad</>
//             }
//           </button>
//           {ad.destination_url && (
//           <a
//               href={ad.destination_url}
//               target="_blank"
//               rel="noopener noreferrer"
//               className="w-8 h-8 flex items-center justify-center rounded-lg bg-ink-3 border border-edge-2 text-word-2 hover:text-word-1 hover:bg-ink-4 transition-all"
//             >
//               <ExternalLink size={12} />
//             </a>
//           )}
//         </div>
//       </div>
//     </motion.div>
//   );
// }

// // ─── DemoPage ─────────────────────────────────────────────────────────────────
// export function DemoPage() {
//   const pipeline  = usePipeline();
//   const isRunning = pipeline.stage === 'extracting' || pipeline.stage === 'serving';

//   const [profiles, setProfiles]        = useState<Profile[]>(SEED_PROFILES);
//   const [showAddModal, setShowAddModal] = useState(false);
//   const [activeExport, setActiveExport] = useState<{ userId: string; result: ExportHistoryResponse } | null>(null);

//   const nextColor = PALETTE[profiles.length % PALETTE.length];

//   const handleProfileSelect = useCallback(async (profile: Profile) => {
//     setActiveExport(null);
//     // runLive: export → extract interests → serve ads, all in sequence
//     const exportResult = await pipeline.runLive(profile.user_id, profile.chrome_path);
//     if (exportResult) {
//       setActiveExport({ userId: profile.user_id, result: exportResult });
//       toast.success(`Exported ${exportResult.rows_exported} rows — ads served!`);
//     }
//   }, [pipeline]);

//   const handleAddProfile = useCallback((p: Profile) => {
//     setProfiles(prev => [...prev, p]);
//   }, []);

//   const handleRemoveProfile = useCallback((userId: string) => {
//     setProfiles(prev => prev.filter(p => p.user_id !== userId));
//     if (pipeline.userId === userId) pipeline.reset();
//   }, [pipeline]);

//   const sig1Cat     = (pipeline.interests?.top_1_most_recent as Record<string, unknown> | null)?.category as string | undefined;
//   const sig2Cat     = (pipeline.interests?.top_2_most_dominant_product as Record<string, unknown> | null)?.category as string | undefined;
//   const bothSameCat = !!(sig1Cat && sig2Cat && sig1Cat.toLowerCase() === sig2Cat.toLowerCase());

//   return (
//     <div className="p-8 max-w-[1200px] mx-auto">
//       <PageHeader
//         title="Live Ad Pipeline"
//         subtitle="Select a profile — exports browser history then runs full personalisation"
//       >
//         {pipeline.stage !== 'idle' && (
//           <button
//             onClick={() => { pipeline.reset(); setActiveExport(null); }}
//             className="btn btn-ghost flex items-center gap-2"
//           >
//             <RotateCcw size={14} /> Reset
//           </button>
//         )}
//       </PageHeader>

//       {/* ── Profile Grid ── */}
//       <section className="mb-8">
//         <div className="flex items-center justify-between mb-3">
//           <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
//             Demo Profiles
//           </div>
//           <button
//             onClick={() => setShowAddModal(true)}
//             className="btn btn-secondary btn-sm flex items-center gap-1.5"
//           >
//             <UserPlus size={13} /> Add Profile
//           </button>
//         </div>
//         <AnimatePresence mode="popLayout">
//           <div className="grid grid-cols-3 gap-4">
//             {profiles.map(profile => (
//               <div key={profile.user_id} className="group">
//                 <ProfileCard
//                   profile={profile}
//                   active={pipeline.userId === profile.user_id}
//                   running={isRunning && pipeline.userId === profile.user_id}
//                   exportResult={activeExport?.userId === profile.user_id ? activeExport.result : null}
//                   onSelect={() => handleProfileSelect(profile)}
//                   onRemove={() => handleRemoveProfile(profile.user_id)}
//                 />
//               </div>
//             ))}
//           </div>
//         </AnimatePresence>
//       </section>

//       {/* ── Add Profile Modal ── */}
//       <AddProfileModal
//         open={showAddModal}
//         onClose={() => setShowAddModal(false)}
//         onAdd={handleAddProfile}
//         nextColor={nextColor}
//       />
//       {/* ── User selector ── */}
//       <section className="mb-7">
//         <div className="text-xs font-semibold text-word-3 uppercase tracking-widest mb-3">
//           Select User Profile
//         </div>
//         <div className="grid grid-cols-6 gap-3">
//           {DEMO_USERS.map(user => (
//             <UserCard
//               key={user.id}
//               user={user}
//               active={pipeline.userId === user.id}
//               running={isRunning}
//               onSelect={() => pipeline.run(user.id)}
//             />
//           ))}
//         </div>
//       </section>

//       {/* ── Pipeline Visualiser ── */}
//       <AnimatePresence>
//         {pipeline.stage !== 'idle' && (
//           <motion.section
//             initial={{ opacity: 0, y: 10 }}
//             animate={{ opacity: 1, y: 0 }}
//             className="mb-7"
//           >
//             <div className="text-xs font-semibold text-word-3 uppercase tracking-widest mb-3">
//               Pipeline
//             </div>
//             <PipelineVis stage={pipeline.stage} />
//             {(pipeline.timings.extract || pipeline.timings.serve) && (
//               <div className="flex items-center gap-4 mt-3 px-1">
//                 {pipeline.timings.extract && (
//                   <div className="flex items-center gap-1.5 text-xs text-word-3">
//                     <Clock size={11} />
//                     <span>Extract</span>
//                     <span className="font-mono text-violet-300">{pipeline.timings.extract}ms</span>
//                   </div>
//                 )}
//                 {pipeline.timings.serve && (
//                   <div className="flex items-center gap-1.5 text-xs text-word-3">
//                     <Cpu size={11} />
//                     <span>Serve</span>
//                     <span className="font-mono text-jade-300">{pipeline.timings.serve}ms</span>
//                   </div>
//                 )}
//                 {pipeline.timings.extract && pipeline.timings.serve && (
//                   <div className="flex items-center gap-1.5 text-xs text-word-3">
//                     <ChevronRight size={11} />
//                     <span>Total</span>
//                     <span className="font-mono text-sun-400">
//                       {pipeline.timings.extract + pipeline.timings.serve}ms
//                     </span>
//                   </div>
//                 )}
//               </div>
//             )}
//           </motion.section>
//         )}
//       </AnimatePresence>

//       {/* ── Error ── */}
//       <AnimatePresence>
//         {pipeline.stage === 'error' && pipeline.error && (
//           <motion.div
//             initial={{ opacity: 0, y: 8 }}
//             animate={{ opacity: 1, y: 0 }}
//             className="mb-7 p-4 border border-coral-400/20 rounded-xl flex items-start gap-3 bg-coral-400/5"
//           >
//             <AlertTriangle size={16} className="text-coral-400 mt-0.5 flex-shrink-0" />
//             <div>
//               <div className="text-sm font-semibold text-coral-400 mb-0.5">Pipeline Error</div>
//               <div className="text-xs text-coral-400/70">{pipeline.error}</div>
//               <div className="text-xs text-word-3 mt-1">
//                 Ensure Client API is on :8000 and Server API on :8001
//               </div>
//             </div>
//           </motion.div>
//         )}
//       </AnimatePresence>

//       {/* ── Export Result Summary ── */}
//       <AnimatePresence>
//         {activeExport && pipeline.userId && (
//           <motion.div
//             initial={{ opacity: 0, height: 0 }}
//             animate={{ opacity: 1, height: 'auto' }}
//             exit={{ opacity: 0, height: 0 }}
//             className="mb-7 overflow-hidden"
//           >
//             <div className="bg-jade-400/5 border border-jade-400/20 rounded-xl p-4">
//               <div className="flex items-center gap-2 mb-3">
//                 <CheckCircle2 size={14} className="text-jade-400" />
//                 <span className="text-sm font-semibold text-jade-400">Browser History Exported</span>
//                 {activeExport.result.overwritten && (
//                   <span className="text-[10px] px-2 py-0.5 rounded-full bg-sun-400/10 border border-sun-400/20 text-sun-400">
//                     Overwritten
//                   </span>
//                 )}
//               </div>
//               <div className="grid grid-cols-4 gap-3">
//                 {[
//                   { label: 'User',   value: activeExport.result.user_id,                                icon: <User size={11} /> },
//                   { label: 'Rows',   value: activeExport.result.rows_exported.toLocaleString(),         icon: <FileSpreadsheet size={11} /> },
//                   { label: 'File',   value: activeExport.result.csv_path.split(/[\\/]/).pop() ?? '',    icon: <FolderDown size={11} /> },
//                   { label: 'Status', value: activeExport.result.overwritten ? 'Overwritten' : 'New file', icon: <CheckCircle2 size={11} /> },
//                 ].map(item => (
//                   <div key={item.label} className="bg-ink-3 border border-edge-1 rounded-lg p-2.5">
//                     <div className="flex items-center gap-1 text-[10px] text-word-3 mb-1">
//                       {item.icon}{item.label}
//                     </div>
//                     <div className="text-xs font-semibold text-word-1 truncate" title={String(item.value)}>
//                       {item.value}
//                     </div>
//                   </div>
//                 ))}
//               </div>
//               <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-word-3">
//                 <FolderDown size={10} />
//                 <span className="font-mono truncate">{activeExport.result.csv_path}</span>
//               </div>
//             </div>
//           </motion.div>
//         )}
//       </AnimatePresence>

//       {/* ── Interest Signals ── */}
//       <AnimatePresence>
//         {pipeline.interests && (
//           <motion.section
//             initial={{ opacity: 0 }}
//             animate={{ opacity: 1 }}
//             className="mb-7"
//           >
//             <div className="flex items-center justify-between mb-3">
//               <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
//                 Interest Profile — {pipeline.userId}
//               </div>
//               <div className="flex items-center gap-3 text-xs text-word-3">
//                 {typeof pipeline.interests.client_metadata?.products_found === 'number' && (
//                   <span>{pipeline.interests.client_metadata.products_found} products analysed</span>
//                 )}
//                 {pipeline.timings.extract && (
//                   <span className="font-mono text-violet-400">⚡ {pipeline.timings.extract}ms</span>
//                 )}
//               </div>
//             </div>
//             <div className="grid grid-cols-4 gap-3">
//               {[
//                 { num: 1, label: 'Most Recent',      data: pipeline.interests.top_1_most_recent,                   color: CHART_COLORS[0], highlight: bothSameCat },
//                 { num: 2, label: 'Top Product',       data: pipeline.interests.top_2_most_dominant_product,         color: CHART_COLORS[1], highlight: bothSameCat },
//                 { num: 3, label: 'Category + Sub',    data: pipeline.interests.top_3_dominant_category_subcategory, color: CHART_COLORS[2], highlight: false },
//                 { num: 4, label: 'Dominant Category', data: pipeline.interests.top_4_dominant_category,             color: CHART_COLORS[3], highlight: false },
//               ].map(sig => (
//                 <SignalCard key={sig.num} {...sig} isHighlight={sig.highlight} />
//               ))}
//             </div>
//           </motion.section>
//         )}
//       </AnimatePresence>

//       {/* ── High Interest Banner ── */}
//       <AnimatePresence>
//         {pipeline.isHighInterest && pipeline.highInterestCategory && pipeline.stage !== 'extracting' && (
//           <HighInterestBanner
//             category={pipeline.highInterestCategory}
//             multiplier={pipeline.premiumCpmMultiplier}
//           />
//         )}
//       </AnimatePresence>

//       {/* ── Serving loading ── */}
//       <AnimatePresence>
//         {pipeline.stage === 'serving' && (
//           <motion.div
//             initial={{ opacity: 0 }}
//             animate={{ opacity: 1 }}
//             exit={{ opacity: 0 }}
//             className="flex items-center justify-center gap-3 py-10 text-sm text-word-3"
//           >
//             <Spinner className="text-violet-400" />
//             Matching ads to top-1 interest category…
//           </motion.div>
//         )}
//       </AnimatePresence>

//       {/* ── Served Ads ── */}
//       <AnimatePresence>
//         {pipeline.result && pipeline.stage === 'complete' && (
//           <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
//             <div className="flex items-center justify-between mb-3">
//               <div className="flex items-center gap-2">
//                 <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
//                   {pipeline.result.ads.length} Ads — Best Matches
//                 </div>
//                 {pipeline.result.ads.length === 0 && (
//                   <span className="text-[10px] text-coral-400 border border-coral-400/20 rounded-full px-2 py-0.5">
//                     No matching ads found
//                   </span>
//                 )}
//               </div>
//               <div className="flex items-center gap-4 text-xs text-word-3">
//                 <span>{pipeline.result.total_candidates_evaluated} evaluated</span>
//                 {pipeline.timings.serve && (
//                   <span className="font-mono text-jade-400">⚡ {pipeline.timings.serve}ms</span>
//                 )}
//               </div>
//             </div>

//             {pipeline.result.signals_used && (
//               <div className="flex flex-wrap gap-1.5 mb-4">
//                 <span className="text-[10px] text-word-3 mr-1 self-center">Matched on:</span>
//                 {pipeline.result.signals_used.categories.map(c => (
//                   <span key={c} className="badge-sun text-[10px]">{c}</span>
//                 ))}
//                 {pipeline.result.signals_used.brands.map(b => (
//                   <span key={b} className="badge-sky text-[10px]">{b}</span>
//                 ))}
//                 {pipeline.result.signals_used.interest_tokens.slice(0, 4).map(t => (
//                   <span key={t} className="badge-muted text-[10px]">{t}</span>
//                 ))}
//               </div>
//             )}

//             <div className={cn(
//               'grid gap-4',
//               pipeline.result.ads.length === 1 ? 'grid-cols-1 max-w-md' :
//               pipeline.result.ads.length === 2 ? 'grid-cols-2' : 'grid-cols-3',
//             )}>
//               {pipeline.result.ads.map((ad, i) => (
//                 <AdResultCard
//                   key={ad.ad_id}
//                   ad={ad}
//                   rank={i + 1}
//                   userId={pipeline.userId!}
//                   delay={i * 0.1}
//                   isHighInterest={pipeline.isHighInterest}
//                   premiumCpm={pipeline.premiumCpmMultiplier}
//                 />
//               ))}
//             </div>
//           </motion.section>
//         )}
//       </AnimatePresence>
//     </div>
//   );
// }

// import { useState } from 'react';
// import {
//   Globe, Brain, Target, Sparkles,
//   ChevronRight, RotateCcw, AlertTriangle,
//   MousePointerClick, ExternalLink, Clock, Cpu,
//   TrendingUp, Tag, Flame, FolderDown, CheckCircle2,
//   FileSpreadsheet, User, Chrome, Zap,
// } from 'lucide-react';
// import { motion, AnimatePresence } from 'framer-motion';
// import { PageHeader, Spinner } from '@/components/ui';
// import { usePipeline } from '@/hooks/usePipeline';
// import { clientApi, type ExportHistoryResponse } from '@/services/clientApi';
// import { adsApi } from '@/services/serverApi';
// import { DEMO_USERS, CHART_COLORS } from '@/constants';
// import { cn, fmt, scoreColor } from '@/lib/utils';
// import type { InterestSignal, ServedAd, PipelineStage } from '@/types';
// import toast from 'react-hot-toast';

// // ─── Pipeline Step Config ──────────────────────────────────────────────────────
// const PIPELINE_STEPS = [
//   { id: 'extracting', label: 'Browser History',  sublabel: 'Client side',    icon: Globe },
//   { id: 'extracted',  label: 'Interest Signals', sublabel: 'ML extraction',  icon: Brain },
//   { id: 'serving',    label: 'Ad Matching',       sublabel: 'Server ranking', icon: Target },
//   { id: 'complete',   label: 'Ads Delivered',     sublabel: 'Personalised',   icon: Sparkles },
// ] as const;

// // ─── Live Analysis Panel ────────────────────────────────────────────────────────
// function LiveAnalysisPanel() {
//   const [userId, setUserId]     = useState('');
//   const [profilePath, setPath]  = useState('');
//   const [loading, setLoading]   = useState(false);
//   const [result, setResult]     = useState<ExportHistoryResponse | null>(null);
//   const [error, setError]       = useState<string | null>(null);

//   const handleExport = async () => {
//     if (!userId.trim() || !profilePath.trim()) {
//       toast.error('Both User ID and Chrome Profile Path are required');
//       return;
//     }
//     setLoading(true);
//     setError(null);
//     setResult(null);
//     try {
//       const res = await clientApi.exportHistory(userId.trim(), profilePath.trim());
//       setResult(res);
//       toast.success(`Exported ${res.rows_exported} rows for ${res.user_id}`);
//     } catch (err: unknown) {
//       const msg = err instanceof Error ? err.message : 'Export failed';
//       setError(msg);
//       toast.error(msg);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="mb-8 bg-ink-2 border border-edge-1 rounded-xl overflow-hidden">
//       {/* Header */}
//       <div className="flex items-center gap-3 px-5 py-4 border-b border-edge-1 bg-ink-3/40">
//         <div className="w-8 h-8 rounded-lg bg-sky-400/10 border border-sky-400/20 flex items-center justify-center">
//           <Chrome size={15} className="text-sky-400" />
//         </div>
//         <div>
//           <div className="text-sm font-semibold text-word-1">Live Browser History Export</div>
//           <div className="text-xs text-word-3">Export Chrome history to CSV then run full analysis</div>
//         </div>
//         <div className="ml-auto flex items-center gap-1.5 text-[10px] font-medium px-2 py-1 rounded-full bg-jade-400/10 border border-jade-400/20 text-jade-400">
//           <span className="w-1.5 h-1.5 rounded-full bg-jade-400 inline-block animate-pulse" />
//           Live
//         </div>
//       </div>

//       <div className="p-5 grid grid-cols-[1fr_1fr_auto] gap-4 items-end">
//         {/* User ID */}
//         <div>
//           <label className="field-label flex items-center gap-1.5">
//             <User size={11} /> User ID
//           </label>
//           <input
//             className="field-input"
//             placeholder="e.g. user7"
//             value={userId}
//             onChange={e => setUserId(e.target.value)}
//             disabled={loading}
//           />
//         </div>

//         {/* Chrome Profile Path */}
//         <div>
//           <label className="field-label flex items-center gap-1.5">
//             <Chrome size={11} /> Chrome Profile Path
//           </label>
//           <input
//             className="field-input font-mono text-xs"
//             placeholder="C:\Users\...\AppData\Local\Google\Chrome\User Data\Profile 3"
//             value={profilePath}
//             onChange={e => setPath(e.target.value)}
//             disabled={loading}
//           />
//         </div>

//         {/* Export button */}
//         <button
//           onClick={handleExport}
//           disabled={loading || !userId.trim() || !profilePath.trim()}
//           className="btn btn-primary gap-2 whitespace-nowrap"
//         >
//           {loading ? <Spinner className="text-white" /> : <FolderDown size={14} />}
//           {loading ? 'Exporting…' : 'Export & Analyse'}
//         </button>
//       </div>

//       {/* Result */}
//       <AnimatePresence>
//         {result && (
//           <motion.div
//             initial={{ opacity: 0, height: 0 }}
//             animate={{ opacity: 1, height: 'auto' }}
//             exit={{ opacity: 0, height: 0 }}
//             className="border-t border-edge-1 overflow-hidden"
//           >
//             <div className="px-5 py-4 bg-jade-400/5">
//               <div className="flex items-center gap-3 mb-4">
//                 <CheckCircle2 size={16} className="text-jade-400 flex-shrink-0" />
//                 <span className="text-sm font-semibold text-jade-400">Export Successful</span>
//                 {result.overwritten && (
//                   <span className="text-[10px] px-2 py-0.5 rounded-full bg-sun-400/10 border border-sun-400/20 text-sun-400">
//                     Overwritten
//                   </span>
//                 )}
//               </div>
//               <div className="grid grid-cols-4 gap-4">
//                 {[
//                   { label: 'User ID',        value: result.user_id,                        icon: <User size={12} /> },
//                   { label: 'Rows Exported',  value: result.rows_exported.toLocaleString(), icon: <FileSpreadsheet size={12} /> },
//                   { label: 'Output File',    value: result.csv_path.split(/[\\/]/).pop() ?? result.csv_path, icon: <FolderDown size={12} /> },
//                   { label: 'Status',         value: result.overwritten ? 'Overwritten' : 'New file', icon: <CheckCircle2 size={12} /> },
//                 ].map(item => (
//                   <div key={item.label} className="bg-ink-3 border border-edge-1 rounded-lg p-3">
//                     <div className="flex items-center gap-1.5 text-[10px] text-word-3 mb-1.5">
//                       {item.icon}{item.label}
//                     </div>
//                     <div className="text-sm font-semibold text-word-1 truncate" title={String(item.value)}>
//                       {item.value}
//                     </div>
//                   </div>
//                 ))}
//               </div>
//               <div className="mt-3 flex items-center gap-2 text-xs text-word-3">
//                 <FolderDown size={11} />
//                 <span className="font-mono text-word-2 truncate">{result.csv_path}</span>
//               </div>
//             </div>
//           </motion.div>
//         )}

//         {error && (
//           <motion.div
//             initial={{ opacity: 0, height: 0 }}
//             animate={{ opacity: 1, height: 'auto' }}
//             className="border-t border-coral-400/20 overflow-hidden"
//           >
//             <div className="px-5 py-4 bg-coral-400/5 flex items-start gap-3">
//               <AlertTriangle size={14} className="text-coral-400 mt-0.5 flex-shrink-0" />
//               <div>
//                 <div className="text-sm font-semibold text-coral-400 mb-0.5">Export Failed</div>
//                 <div className="text-xs text-coral-400/70">{error}</div>
//               </div>
//             </div>
//           </motion.div>
//         )}
//       </AnimatePresence>
//     </div>
//   );
// }

// // ─── High Interest Banner ──────────────────────────────────────────────────────
// function HighInterestBanner({ category, multiplier }: { category: string; multiplier: number }) {
//   return (
//     <motion.div
//       initial={{ opacity: 0, scale: 0.97 }}
//       animate={{ opacity: 1, scale: 1 }}
//       className="mb-5 relative overflow-hidden rounded-xl border border-amber-400/30 bg-gradient-to-r from-amber-500/10 via-orange-500/8 to-amber-400/10 p-4"
//     >
//       {/* Animated glow sweep */}
//       <div className="absolute inset-0 bg-gradient-to-r from-transparent via-amber-400/5 to-transparent animate-[shimmer_3s_linear_infinite] pointer-events-none" />

//       <div className="flex items-center gap-4">
//         <div className="w-10 h-10 rounded-xl bg-amber-400/15 border border-amber-400/30 flex items-center justify-center flex-shrink-0">
//           <Flame size={18} className="text-amber-400" />
//         </div>
//         <div className="flex-1 min-w-0">
//           <div className="flex items-center gap-2 mb-0.5">
//             <span className="text-sm font-bold text-amber-300">High-Interest Signal Detected</span>
//             <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-400/20 border border-amber-400/40 text-amber-300 uppercase tracking-wider">
//               Premium
//             </span>
//           </div>
//           <p className="text-xs text-amber-200/60 leading-relaxed">
//             Both the most recent browsing and dominant product interest point to{' '}
//             <span className="font-semibold text-amber-300">{category}</span>.
//             This user shows exceptionally strong purchase intent — ads in this category carry a{' '}
//             <span className="font-semibold text-amber-300">{multiplier}× CPM premium</span>.
//           </p>
//         </div>
//         <div className="text-right flex-shrink-0">
//           <div className="text-2xl font-bold text-amber-300">{multiplier}×</div>
//           <div className="text-[10px] text-amber-400/60 uppercase tracking-wider">CPM rate</div>
//         </div>
//       </div>
//     </motion.div>
//   );
// }

// // ─── User Card ─────────────────────────────────────────────────────────────────
// function UserCard({ user, active, running, onSelect }: {
//   user: typeof DEMO_USERS[number]; active: boolean; running: boolean; onSelect: () => void;
// }) {
//   return (
//     <button
//       onClick={onSelect}
//       disabled={running}
//       className={cn(
//         'relative flex flex-col items-center gap-2.5 p-4 rounded-xl border',
//         'transition-all duration-200 cursor-pointer group',
//         'disabled:opacity-50 disabled:cursor-not-allowed',
//         active ? 'bg-ink-3 border-violet-500/40 shadow-glow-v' : 'bg-ink-2 border-edge-1 hover:border-edge-2 hover:bg-ink-3',
//       )}
//     >
//       <div
//         className="w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold"
//         style={{ background: `${user.color}18`, color: user.color, border: `1px solid ${user.color}30` }}
//       >
//         {user.initials}
//       </div>
//       <span className="text-xs font-medium text-word-2 group-hover:text-word-1 transition-colors">
//         {user.id.replace('_', ' #')}
//       </span>
//       {active && running && (
//         <span className="absolute top-2 right-2"><Spinner className="text-violet-400" /></span>
//       )}
//     </button>
//   );
// }

// // ─── Pipeline Visualiser ───────────────────────────────────────────────────────
// function PipelineVis({ stage }: { stage: PipelineStage }) {
//   const stageOrder: PipelineStage[] = ['extracting', 'extracted', 'serving', 'complete'];
//   const current = stageOrder.indexOf(stage);

//   return (
//     <div className="flex items-center p-5 bg-ink-2 border border-edge-1 rounded-xl overflow-x-auto">
//       {PIPELINE_STEPS.map((step, i) => {
//         const Icon = step.icon;
//         const stepIdx = stageOrder.indexOf(step.id as PipelineStage);
//         const isActive = stage === step.id;
//         const isDone   = current > stepIdx || stage === 'complete';
//         const isError  = stage === 'error';

//         let nodeState: 'idle' | 'running' | 'done' | 'error' = 'idle';
//         if (isError && isActive) nodeState = 'error';
//         else if (isDone)  nodeState = 'done';
//         else if (isActive) nodeState = 'running';

//         return (
//           <div key={step.id} className="flex items-center flex-1 min-w-0">
//             <div className="flex flex-col items-center gap-1.5 min-w-[80px]">
//               <div className={cn('pipe-icon', nodeState)}>
//                 {nodeState === 'running' ? <Spinner className="text-violet-400" /> : <Icon size={20} />}
//               </div>
//               <span className={cn(
//                 'text-xs font-medium text-center leading-tight',
//                 nodeState === 'done'    && 'text-jade-400',
//                 nodeState === 'running' && 'text-violet-300',
//                 nodeState === 'idle'    && 'text-word-3',
//                 nodeState === 'error'   && 'text-coral-400',
//               )}>{step.label}</span>
//               <span className="text-[10px] text-word-3 text-center">{step.sublabel}</span>
//             </div>
//             {i < PIPELINE_STEPS.length - 1 && (
//               <div className={cn(
//                 'flex-1 h-px mx-2 min-w-[20px] transition-all duration-500',
//                 isDone    ? 'bg-gradient-to-r from-jade-400/50 to-jade-400/20' :
//                 isActive  ? 'bg-gradient-to-r from-violet-500/60 to-transparent animate-flow' :
//                             'bg-edge-1'
//               )} />
//             )}
//           </div>
//         );
//       })}
//     </div>
//   );
// }

// // ─── Signal Card ──────────────────────────────────────────────────────────────
// function SignalCard({ num, label, data, color, isHighlight }: {
//   num: number; label: string; data: InterestSignal | null; color: string; isHighlight?: boolean;
// }) {
//   return (
//     <motion.div
//       initial={{ opacity: 0, y: 10 }}
//       animate={{ opacity: 1, y: 0 }}
//       transition={{ delay: num * 0.07 }}
//       className={cn(
//         'bg-ink-2 border rounded-xl p-4 flex flex-col gap-3 relative overflow-hidden',
//         isHighlight ? 'border-amber-400/40' : 'border-edge-1',
//       )}
//     >
//       {isHighlight && (
//         <div className="absolute top-0 right-0 px-2 py-0.5 bg-amber-400/15 border-b border-l border-amber-400/30 rounded-bl-lg">
//           <div className="flex items-center gap-1 text-[9px] font-bold text-amber-400 uppercase tracking-wider">
//             <Flame size={8} /> High
//           </div>
//         </div>
//       )}
//       <div className="flex items-center gap-2">
//         <div
//           className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider"
//           style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
//         >
//           SIG {num}
//         </div>
//         <span className="text-xs text-word-3">{label}</span>
//       </div>
//       {data ? (
//         <div className="space-y-1.5">
//           {data.category && (
//             <div className="flex items-center gap-1.5 flex-wrap">
//               <span className="badge-violet text-[10px]">{data.category}</span>
//               {data.subcategory && <span className="badge-sky text-[10px]">{data.subcategory}</span>}
//             </div>
//           )}
//           {data.product && <div className="text-sm font-semibold text-word-1 leading-snug">{data.product}</div>}
//           {data.brand   && <div className="text-xs text-word-2">{data.brand}</div>}
//           {data.query   && <div className="text-xs text-word-3 italic">"{data.query}"</div>}
//           {data.total_engagement_score != null && (
//             <div className="text-[10px] text-word-3 font-mono">score: {Number(data.total_engagement_score).toFixed(1)}</div>
//           )}
//         </div>
//       ) : (
//         <div className="text-xs text-word-3 italic">No signal available</div>
//       )}
//     </motion.div>
//   );
// }

// // ─── Ad Result Card ───────────────────────────────────────────────────────────
// function AdResultCard({ ad, rank, userId, delay, isHighInterest, premiumCpm }: {
//   ad: ServedAd; rank: number; userId: string; delay: number;
//   isHighInterest: boolean; premiumCpm: number;
// }) {
//   const [clicked, setClicked] = useState(false);
//   const score    = ad.relevance_score ?? 0;
//   const scoreVal = Math.round(score * 100);

//   const handleClick = async () => {
//     setClicked(true);
//     await adsApi.recordClick(ad.ad_id, { impression_id: ad.impression_id ?? undefined, user_id: userId });
//     toast.success('Click recorded');
//   };

//   return (
//     <motion.div
//       initial={{ opacity: 0, y: 16 }}
//       animate={{ opacity: 1, y: 0 }}
//       transition={{ delay, ease: [0.16, 1, 0.3, 1] }}
//       className={cn(
//         'ad-card relative',
//         isHighInterest && 'ring-1 ring-amber-400/30',
//       )}
//     >
//       {/* High-interest ribbon */}
//       {isHighInterest && (
//         <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center gap-1.5 py-1.5 bg-gradient-to-r from-amber-500/80 via-amber-400/90 to-orange-500/80 backdrop-blur-sm">
//           <Flame size={11} className="text-amber-900" />
//           <span className="text-[10px] font-bold text-amber-900 uppercase tracking-wider">High-Interest · {premiumCpm}× Premium CPM</span>
//           <Zap size={10} className="text-amber-900" />
//         </div>
//       )}

//       {/* Image */}
//       <div className={cn('relative bg-ink-3 overflow-hidden', isHighInterest ? 'aspect-[16/7] mt-7' : 'aspect-[16/7]')}>
//         {ad.image_url ? (
//           <img
//             src={ad.image_url.startsWith('/') ? `/api/server${ad.image_url}` : ad.image_url}
//             alt={ad.title}
//             className="w-full h-full object-cover"
//           />
//         ) : (
//           <div className="w-full h-full flex items-center justify-center">
//             <div className="text-4xl opacity-10">◈</div>
//           </div>
//         )}
//         {/* Rank badge */}
//         <div className="absolute top-3 left-3 w-7 h-7 rounded-lg bg-canvas/80 backdrop-blur-sm flex items-center justify-center text-xs font-bold text-word-1 border border-edge-2">
//           {rank}
//         </div>
//         {/* Score badge */}
//         <div
//           className="absolute top-3 right-3 px-2 py-0.5 rounded-lg bg-canvas/80 backdrop-blur-sm border border-edge-2 font-mono text-xs font-medium"
//           style={{ color: scoreColor(score) }}
//         >
//           {scoreVal}%
//         </div>
//       </div>

//       {/* Body */}
//       <div className="p-4 flex flex-col gap-3">
//         {/* Category / Brand */}
//         <div className="flex items-center gap-1.5 flex-wrap">
//           <span className="badge-sun text-[10px]">{ad.category}</span>
//           {ad.brand && <span className="badge-sky text-[10px]">{ad.brand}</span>}
//           {isHighInterest && (
//             <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-400/15 border border-amber-400/30 text-amber-300">
//               <Flame size={8} /> High-Interest
//             </span>
//           )}
//         </div>

//         <div>
//           <h3 className="text-sm font-semibold text-word-1 leading-snug mb-0.5">{ad.title}</h3>
//           <p className="text-xs text-word-2 line-clamp-2 leading-relaxed">{ad.description}</p>
//         </div>

//         {/* CPM indicator for high-interest */}
//         {isHighInterest && (
//           <div className="flex items-center gap-2 p-2.5 rounded-lg bg-amber-400/8 border border-amber-400/20">
//             <Zap size={12} className="text-amber-400 flex-shrink-0" />
//             <div className="flex-1">
//               <div className="text-[10px] text-amber-400/70 uppercase tracking-wider">Premium Bid Rate</div>
//               <div className="text-xs font-mono font-bold text-amber-300">
//                 {premiumCpm}× standard CPM — high-intent audience
//               </div>
//             </div>
//           </div>
//         )}

//         {/* Signal breakdown */}
//         <div className="bg-ink-3 rounded-lg p-3 space-y-2">
//           {([
//             ['Category', ad.matched_signals.category_score, CHART_COLORS[0]],
//             ['Keyword',  ad.matched_signals.keyword_score,  CHART_COLORS[1]],
//             ['Brand',    ad.matched_signals.brand_score,    CHART_COLORS[2]],
//           ] as [string, number, string][]).map(([lbl, val, col]) => (
//             <div key={lbl} className="flex items-center gap-2">
//               <span className="text-[10px] text-word-3 w-14 flex-shrink-0">{lbl}</span>
//               <div className="flex-1 score-track">
//                 <motion.div
//                   className="score-fill"
//                   initial={{ width: 0 }}
//                   animate={{ width: `${Math.round((val ?? 0) * 100)}%` }}
//                   transition={{ delay: delay + 0.2, duration: 0.7, ease: 'easeOut' }}
//                   style={{ background: col }}
//                 />
//               </div>
//               <span className="text-[10px] font-mono text-word-2 w-8 text-right">{Math.round((val ?? 0) * 100)}%</span>
//             </div>
//           ))}
//         </div>

//         {/* Keywords */}
//         {ad.keywords?.length > 0 && (
//           <div className="flex flex-wrap gap-1">
//             {ad.keywords.slice(0, 4).map(kw => (
//               <span key={kw} className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-ink-4 border border-edge-1 text-word-3">
//                 <Tag size={8} />{kw}
//               </span>
//             ))}
//           </div>
//         )}

//         {/* Actions */}
//         <div className="flex gap-2 pt-1">
//           <button
//             onClick={handleClick}
//             disabled={clicked}
//             className={cn(
//               'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200',
//               clicked
//                 ? 'bg-jade-400/10 text-jade-400 border border-jade-400/20'
//                 : isHighInterest
//                   ? 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white active:scale-95'
//                   : 'bg-violet-500 hover:bg-violet-600 text-white active:scale-95',
//             )}
//           >
//             {clicked
//               ? <><TrendingUp size={12} /> Clicked!</>
//               : <><MousePointerClick size={12} /> Visit Ad</>}
//           </button>
//           {ad.destination_url && (
//             <a
//               href={ad.destination_url}
//               target="_blank"
//               rel="noopener noreferrer"
//               className="w-8 h-8 flex items-center justify-center rounded-lg bg-ink-3 border border-edge-2 text-word-2 hover:text-word-1 hover:bg-ink-4 transition-all"
//             >
//               <ExternalLink size={12} />
//             </a>
//           )}
//         </div>
//       </div>
//     </motion.div>
//   );
// }

// // ─── DemoPage ─────────────────────────────────────────────────────────────────
// export function DemoPage() {
//   const pipeline  = usePipeline();
//   const isRunning = pipeline.stage === 'extracting' || pipeline.stage === 'serving';

//   // Determine if sig1 and sig2 highlight (for signal cards)
//   const sig1Cat = (pipeline.interests?.top_1_most_recent as Record<string, unknown> | null)?.category as string | undefined;
//   const sig2Cat = (pipeline.interests?.top_2_most_dominant_product as Record<string, unknown> | null)?.category as string | undefined;
//   const bothSameCat = !!(sig1Cat && sig2Cat && sig1Cat.toLowerCase() === sig2Cat.toLowerCase());

//   return (
//     <div className="p-8 max-w-[1200px] mx-auto">
//       <PageHeader
//         title="Live Ad Pipeline"
//         subtitle="Export browser history, extract interests, and serve personalised ads in real time"
//       >
//         {pipeline.stage !== 'idle' && (
//           <button onClick={pipeline.reset} className="btn-ghost btn flex items-center gap-2">
//             <RotateCcw size={14} /> Reset
//           </button>
//         )}
//       </PageHeader>

//       {/* ── Live Analysis Panel ── */}
//       <LiveAnalysisPanel />

//       {/* ── User selector ── */}
//       <section className="mb-7">
//         <div className="text-xs font-semibold text-word-3 uppercase tracking-widest mb-3">
//           Select User Profile
//         </div>
//         <div className="grid grid-cols-6 gap-3">
//           {DEMO_USERS.map(user => (
//             <UserCard
//               key={user.id}
//               user={user}
//               active={pipeline.userId === user.id}
//               running={isRunning}
//               onSelect={() => pipeline.run(user.id)}
//             />
//           ))}
//         </div>
//       </section>

//       {/* ── Pipeline visualiser ── */}
//       <AnimatePresence>
//         {pipeline.stage !== 'idle' && (
//           <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-7">
//             <div className="text-xs font-semibold text-word-3 uppercase tracking-widest mb-3">Pipeline</div>
//             <PipelineVis stage={pipeline.stage} />

//             {(pipeline.timings.extract || pipeline.timings.serve) && (
//               <div className="flex items-center gap-4 mt-3 px-1">
//                 {pipeline.timings.extract && (
//                   <div className="flex items-center gap-1.5 text-xs text-word-3">
//                     <Clock size={11} /><span>Extract</span>
//                     <span className="font-mono text-violet-300">{pipeline.timings.extract}ms</span>
//                   </div>
//                 )}
//                 {pipeline.timings.serve && (
//                   <div className="flex items-center gap-1.5 text-xs text-word-3">
//                     <Cpu size={11} /><span>Serve</span>
//                     <span className="font-mono text-jade-300">{pipeline.timings.serve}ms</span>
//                   </div>
//                 )}
//                 {pipeline.timings.extract && pipeline.timings.serve && (
//                   <div className="flex items-center gap-1.5 text-xs text-word-3">
//                     <ChevronRight size={11} /><span>Total</span>
//                     <span className="font-mono text-sun-400">{pipeline.timings.extract + pipeline.timings.serve}ms</span>
//                   </div>
//                 )}
//               </div>
//             )}
//           </motion.section>
//         )}
//       </AnimatePresence>

//       {/* ── Error ── */}
//       <AnimatePresence>
//         {pipeline.stage === 'error' && pipeline.error && (
//           <motion.div
//             initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
//             className="mb-7 p-4 border border-coral-400/20 rounded-xl flex items-start gap-3 bg-coral-400/5"
//           >
//             <AlertTriangle size={16} className="text-coral-400 mt-0.5 flex-shrink-0" />
//             <div>
//               <div className="text-sm font-semibold text-coral-400 mb-0.5">Pipeline Error</div>
//               <div className="text-xs text-coral-400/70">{pipeline.error}</div>
//               <div className="text-xs text-word-3 mt-1">Ensure Client API is running on :8000 and Server API on :8001</div>
//             </div>
//           </motion.div>
//         )}
//       </AnimatePresence>

//       {/* ── Interest Signals ── */}
//       <AnimatePresence>
//         {pipeline.interests && (
//           <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-7">
//             <div className="flex items-center justify-between mb-3">
//               <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
//                 Interest Profile — {pipeline.userId}
//               </div>
//               <div className="flex items-center gap-3 text-xs text-word-3">
//                 {typeof pipeline.interests.client_metadata?.products_found === 'number' && (
//                   <span>{pipeline.interests.client_metadata.products_found} products analysed</span>
//                 )}
//                 {pipeline.timings.extract && (
//                   <span className="font-mono text-violet-400">⚡ {pipeline.timings.extract}ms</span>
//                 )}
//               </div>
//             </div>
//             <div className="grid grid-cols-4 gap-3">
//               {[
//                 { num: 1, label: 'Most Recent',      data: pipeline.interests.top_1_most_recent,                   color: CHART_COLORS[0], highlight: bothSameCat },
//                 { num: 2, label: 'Top Product',       data: pipeline.interests.top_2_most_dominant_product,         color: CHART_COLORS[1], highlight: bothSameCat },
//                 { num: 3, label: 'Category + Sub',    data: pipeline.interests.top_3_dominant_category_subcategory, color: CHART_COLORS[2], highlight: false },
//                 { num: 4, label: 'Dominant Category', data: pipeline.interests.top_4_dominant_category,             color: CHART_COLORS[3], highlight: false },
//               ].map(sig => (
//                 <SignalCard key={sig.num} {...sig} isHighlight={sig.highlight} />
//               ))}
//             </div>
//           </motion.section>
//         )}
//       </AnimatePresence>

//       {/* ── High Interest Banner ── */}
//       <AnimatePresence>
//         {pipeline.isHighInterest && pipeline.highInterestCategory && pipeline.stage !== 'extracting' && (
//           <HighInterestBanner
//             category={pipeline.highInterestCategory}
//             multiplier={pipeline.premiumCpmMultiplier}
//           />
//         )}
//       </AnimatePresence>

//       {/* ── Serving loading ── */}
//       <AnimatePresence>
//         {pipeline.stage === 'serving' && (
//           <motion.div
//             initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
//             className="flex items-center justify-center gap-3 py-10 text-sm text-word-3"
//           >
//             <Spinner className="text-violet-400" />
//             Matching ads to top-1 interest category…
//           </motion.div>
//         )}
//       </AnimatePresence>

//       {/* ── Served Ads ── */}
//       <AnimatePresence>
//         {pipeline.result && pipeline.stage === 'complete' && (
//           <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
//             <div className="flex items-center justify-between mb-3">
//               <div className="flex items-center gap-2">
//                 <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
//                   {pipeline.result.ads.length} Ads — Best Matches
//                 </div>
//                 {pipeline.result.ads.length === 0 && (
//                   <span className="text-[10px] text-coral-400 border border-coral-400/20 rounded-full px-2 py-0.5 bg-coral-400/8">
//                     No matching ads found
//                   </span>
//                 )}
//               </div>
//               <div className="flex items-center gap-4 text-xs text-word-3">
//                 <span>{pipeline.result.total_candidates_evaluated} evaluated</span>
//                 {pipeline.timings.serve && (
//                   <span className="font-mono text-jade-400">⚡ {pipeline.timings.serve}ms</span>
//                 )}
//               </div>
//             </div>

//             {/* Signals used */}
//             {pipeline.result.signals_used && (
//               <div className="flex flex-wrap gap-1.5 mb-4">
//                 <span className="text-[10px] text-word-3 mr-1 self-center">Matched on:</span>
//                 {pipeline.result.signals_used.categories.map(c => (
//                   <span key={c} className="badge-sun text-[10px]">{c}</span>
//                 ))}
//                 {pipeline.result.signals_used.brands.map(b => (
//                   <span key={b} className="badge-sky text-[10px]">{b}</span>
//                 ))}
//                 {pipeline.result.signals_used.interest_tokens.slice(0, 4).map(t => (
//                   <span key={t} className="badge-muted text-[10px]">{t}</span>
//                 ))}
//               </div>
//             )}

//             <div className={cn(
//               'grid gap-4',
//               pipeline.result.ads.length === 1 ? 'grid-cols-1 max-w-md' :
//               pipeline.result.ads.length === 2 ? 'grid-cols-2' : 'grid-cols-3'
//             )}>
//               {pipeline.result.ads.map((ad, i) => (
//                 <AdResultCard
//                   key={ad.ad_id}
//                   ad={ad}
//                   rank={i + 1}
//                   userId={pipeline.userId!}
//                   delay={i * 0.1}
//                   isHighInterest={pipeline.isHighInterest}
//                   premiumCpm={pipeline.premiumCpmMultiplier}
//                 />
//               ))}
//             </div>
//           </motion.section>
//         )}
//       </AnimatePresence>
//     </div>
//   );
// }





import { useState, useCallback, useEffect } from 'react';
import {
  Globe, Brain, Target, Sparkles,
  ChevronRight, RotateCcw, AlertTriangle,
  MousePointerClick, ExternalLink, Clock, Cpu,
  TrendingUp, Tag, Flame, FolderDown, CheckCircle2,
  FileSpreadsheet, Chrome, Zap, UserPlus, X,
  Mail, FolderOpen, Play, User,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageHeader, Spinner, Modal } from '@/components/ui';
import { usePipeline } from '@/hooks/usePipeline';
import { type ExportHistoryResponse } from '@/services/clientApi';
import { adsApi } from '@/services/serverApi';
import {DEMO_USERS, LIVE_PROFILES, CHART_COLORS } from '@/constants';
import { cn, scoreColor } from '@/lib/utils';
import type { InterestSignal, ServedAd, PipelineStage } from '@/types';
import toast from 'react-hot-toast';

// ─── Types ────────────────────────────────────────────────────────────────────
interface Profile {
  name: string;
  email: string;
  chrome_path: string;
  color: string;
  user_id: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function slugify(name: string): string {
  return name.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
}

function initials(name: string): string {
  return name.trim().split(/\s+/).map(w => w[0]?.toUpperCase() ?? '').join('').slice(0, 2);
}

const PALETTE = [
  '#8b5cf6', '#34d399', '#fbbf24', '#f87171',
  '#38bdf8', '#a78bfa', '#f97316', '#e879f9', '#84cc16', '#06b6d4',
];

const SEED_PROFILES: Profile[] = (LIVE_PROFILES as unknown as Array<{
  name: string; email: string; chrome_path: string; color: string;
}>).map(p => ({ ...p, user_id: slugify(p.name) }));

// ─── Pipeline Steps ───────────────────────────────────────────────────────────
const PIPELINE_STEPS = [
  { id: 'extracting', label: 'Browser History',  sublabel: 'Client side',    icon: Globe },
  { id: 'extracted',  label: 'Interest Signals', sublabel: 'ML extraction',  icon: Brain },
  { id: 'serving',    label: 'Ad Matching',       sublabel: 'Server ranking', icon: Target },
  { id: 'complete',   label: 'Ads Delivered',     sublabel: 'Personalised',   icon: Sparkles },
] as const;

// ─── Add Profile Modal ────────────────────────────────────────────────────────
function AddProfileModal({ open, onClose, onAdd, nextColor }: {
  open: boolean;
  onClose: () => void;
  onAdd: (p: Profile) => void;
  nextColor: string;
}) {
  const [name, setName]   = useState('');
  const [email, setEmail] = useState('');
  const [path, setPath]   = useState('');
  const [color, setColor] = useState(nextColor);
  const userId = slugify(name);

  const handleAdd = () => {
    if (!name.trim()) { toast.error('Name is required'); return; }
    if (!path.trim()) { toast.error('Chrome path is required'); return; }
    onAdd({ name: name.trim(), email: email.trim(), chrome_path: path.trim(), color, user_id: userId });
    setName(''); setEmail(''); setPath('');
    onClose();
    toast.success(`Profile "${name.trim()}" added`);
  };

  return (
    <Modal open={open} onClose={onClose} title="Add Profile">
      <div className="space-y-4">
        <div>
          <label className="field-label flex items-center gap-1.5">
            <User size={11} /> Display Name
          </label>
          <input
            className="field-input"
            placeholder="e.g. Vikhyath"
            value={name}
            onChange={e => setName(e.target.value)}
          />
          {name.trim() && (
            <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-word-3">
              <span>Auto user ID:</span>
              <code className="font-mono text-violet-400 bg-ink-3 px-1.5 py-0.5 rounded">{userId}</code>
            </div>
          )}
        </div>

        <div>
          <label className="field-label flex items-center gap-1.5">
            <Mail size={11} /> Email (optional)
          </label>
          <input
            className="field-input"
            placeholder="e.g. vikhyath@example.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
          />
        </div>

        <div>
          <label className="field-label flex items-center gap-1.5">
            <FolderOpen size={11} /> Chrome Profile Path
          </label>
          <input
            className="field-input font-mono text-xs"
            placeholder="C:\Users\...\AppData\Local\Google\Chrome\User Data\Profile 3"
            value={path}
            onChange={e => setPath(e.target.value)}
          />
          <p className="text-[11px] text-word-3 mt-1.5">
            Find it at: <code className="font-mono text-word-2">chrome://version</code> → Profile Path
          </p>
        </div>

        <div>
          <label className="field-label">Avatar Colour</label>
          <div className="flex items-center gap-2 flex-wrap">
            {PALETTE.map(c => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                className={cn(
                  'w-7 h-7 rounded-lg transition-all duration-150',
                  color === c ? 'ring-2 ring-white/50 scale-110' : 'opacity-60 hover:opacity-100',
                )}
                style={{ background: c }}
              />
            ))}
          </div>
        </div>

        {name.trim() && (
          <div className="flex items-center gap-3 p-3 bg-ink-3 rounded-xl border border-edge-1">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0"
              style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}
            >
              {initials(name)}
            </div>
            <div>
              <div className="text-sm font-semibold text-word-1">{name.trim()}</div>
              {email && <div className="text-xs text-word-3">{email}</div>}
              <code className="text-[10px] font-mono text-violet-400">{userId}</code>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-1">
          <button onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button onClick={handleAdd} className="btn btn-primary">Add Profile</button>
        </div>
      </div>
    </Modal>
  );
}

// ─── Profile Card ─────────────────────────────────────────────────────────────
function ProfileCard({ profile, active, running, exportResult, onSelect, onRemove }: {
  profile: Profile;
  active: boolean;
  running: boolean;
  exportResult: ExportHistoryResponse | null;
  onSelect: () => void;
  onRemove: () => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn(
        'relative flex flex-col gap-3 p-4 rounded-xl border transition-all duration-200',
        active
          ? 'bg-ink-3 border-violet-500/50 shadow-glow-v'
          : 'bg-ink-2 border-edge-1 hover:border-edge-2 hover:bg-ink-3',
      )}
    >
      <button
        onClick={e => { e.stopPropagation(); onRemove(); }}
        className="absolute top-2 right-2 w-5 h-5 rounded-full bg-ink-4 border border-edge-1
                   flex items-center justify-center text-word-3
                   hover:text-coral-400 hover:border-coral-400/30
                   transition-all opacity-0 group-hover:opacity-100"
        title="Remove profile"
      >
        <X size={10} />
      </button>

      <div className="flex items-center gap-3">
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0"
          style={{ background: `${profile.color}18`, color: profile.color, border: `1px solid ${profile.color}35` }}
        >
          {initials(profile.name)}
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold text-word-1 truncate">{profile.name}</div>
          {profile.email && (
            <div className="text-[11px] text-word-3 truncate flex items-center gap-1">
              <Mail size={9} />{profile.email}
            </div>
          )}
          <code className="text-[10px] font-mono text-violet-400">{profile.user_id}</code>
        </div>
      </div>

      <div className="flex items-start gap-1.5 bg-ink-3/80 rounded-lg px-2.5 py-2 border border-edge-1">
        <Chrome size={10} className="text-sky-400 mt-0.5 flex-shrink-0" />
        <span
          className="text-[10px] font-mono text-word-3 leading-relaxed break-all line-clamp-2"
          title={profile.chrome_path}
        >
          {profile.chrome_path}
        </span>
      </div>

      {exportResult && active && (
        <div className="flex items-center gap-1.5 text-[10px] text-jade-400">
          <CheckCircle2 size={10} />
          <span>{exportResult.rows_exported.toLocaleString()} rows exported</span>
        </div>
      )}

      <button
        onClick={onSelect}
        disabled={running}
        className={cn(
          'w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold',
          'transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed active:scale-95',
          active && running
            ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
            : 'bg-violet-500 hover:bg-violet-600 text-white',
        )}
      >
        {active && running
          ? <><Spinner className="text-violet-300" /> Running…</>
          : <><Play size={11} /> Run Analysis</>
        }
      </button>
    </motion.div>
  );
}
// ─── User Card ─────────────────────────────────────────────────────────────────
function UserCard({ user, active, running, onSelect }: {
  user: typeof DEMO_USERS[number]; active: boolean; running: boolean; onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      disabled={running}
      className={cn(
        'relative flex flex-col items-center gap-2.5 p-4 rounded-xl border',
        'transition-all duration-200 cursor-pointer group',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        active ? 'bg-ink-3 border-violet-500/40 shadow-glow-v' : 'bg-ink-2 border-edge-1 hover:border-edge-2 hover:bg-ink-3',
      )}
    >
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold"
        style={{ background: `${user.color}18`, color: user.color, border: `1px solid ${user.color}30` }}
      >
        {user.initials}
      </div>
      <span className="text-xs font-medium text-word-2 group-hover:text-word-1 transition-colors">
        {user.id.replace('_', ' #')}
      </span>
      {active && running && (
        <span className="absolute top-2 right-2"><Spinner className="text-violet-400" /></span>
      )}
    </button>
  );
}

// ─── Pipeline Visualiser ───────────────────────────────────────────────────────
function PipelineVis({ stage }: { stage: PipelineStage }) {
  const stageOrder: PipelineStage[] = ['extracting', 'extracted', 'serving', 'complete'];
  const current = stageOrder.indexOf(stage);

  return (
    <div className="flex items-center p-5 bg-ink-2 border border-edge-1 rounded-xl overflow-x-auto">
      {PIPELINE_STEPS.map((step, i) => {
        const Icon = step.icon;
        const stepIdx  = stageOrder.indexOf(step.id as PipelineStage);
        const isActive = stage === step.id;
        const isDone   = current > stepIdx || stage === 'complete';
        const isError  = stage === 'error';

        let nodeState: 'idle' | 'running' | 'done' | 'error' = 'idle';
        if (isError && isActive) nodeState = 'error';
        else if (isDone)         nodeState = 'done';
        else if (isActive)       nodeState = 'running';

        return (
          <div key={step.id} className="flex items-center flex-1 min-w-0">
            <div className="flex flex-col items-center gap-1.5 min-w-[80px]">
              <div className={cn('pipe-icon', nodeState)}>
                {nodeState === 'running' ? <Spinner className="text-violet-400" /> : <Icon size={20} />}
              </div>
              <span className={cn(
                'text-xs font-medium text-center leading-tight',
                nodeState === 'done'    && 'text-jade-400',
                nodeState === 'running' && 'text-violet-300',
                nodeState === 'idle'    && 'text-word-3',
                nodeState === 'error'   && 'text-coral-400',
              )}>
                {step.label}
              </span>
              <span className="text-[10px] text-word-3 text-center">{step.sublabel}</span>
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <div className={cn(
                'flex-1 h-px mx-2 min-w-[20px] transition-all duration-500',
                isDone   ? 'bg-gradient-to-r from-jade-400/50 to-jade-400/20' :
                isActive ? 'bg-gradient-to-r from-violet-500/60 to-transparent animate-flow' :
                           'bg-edge-1',
              )} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Signal Card ──────────────────────────────────────────────────────────────
function SignalCard({ num, label, data, color, isHighlight }: {
  num: number;
  label: string;
  data: InterestSignal | null;
  color: string;
  isHighlight?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: num * 0.07 }}
      className={cn(
        'bg-ink-2 border rounded-xl p-4 flex flex-col gap-3 relative overflow-hidden',
        isHighlight ? 'border-amber-400/40' : 'border-edge-1',
      )}
    >
      {isHighlight && (
        <div className="absolute top-0 right-0 px-2 py-0.5 bg-amber-400/15 border-b border-l border-amber-400/30 rounded-bl-lg">
          <div className="flex items-center gap-1 text-[9px] font-bold text-amber-400 uppercase tracking-wider">
            <Flame size={8} /> High
          </div>
        </div>
      )}
      <div className="flex items-center gap-2">
        <div
          className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider"
          style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
        >
          SIG {num}
        </div>
        <span className="text-xs text-word-3">{label}</span>
      </div>
      {data ? (
        <div className="space-y-1.5">
          {data.category && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="badge-violet text-[10px]">{data.category}</span>
              {data.subcategory && <span className="badge-sky text-[10px]">{data.subcategory}</span>}
            </div>
          )}
          {data.product && (
            <div className="text-sm font-semibold text-word-1 leading-snug">{data.product}</div>
          )}
          {data.brand && (
            <div className="text-xs text-word-2">{data.brand}</div>
          )}
          {data.query && (
            <div className="text-xs text-word-3 italic">"{data.query}"</div>
          )}
          {data.total_engagement_score != null && (
            <div className="text-[10px] text-word-3 font-mono">
              score: {Number(data.total_engagement_score).toFixed(1)}
            </div>
          )}
        </div>
      ) : (
        <div className="text-xs text-word-3 italic">No signal available</div>
      )}
    </motion.div>
  );
}

// ─── High Interest Banner ─────────────────────────────────────────────────────
function HighInterestBanner({ category, multiplier }: { category: string; multiplier: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="mb-5 relative overflow-hidden rounded-xl border border-amber-400/30 p-4"
      style={{ background: 'linear-gradient(to right, rgba(245,158,11,0.10), rgba(249,115,22,0.08), rgba(251,191,36,0.10))' }}
    >
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-amber-400/15 border border-amber-400/30 flex items-center justify-center flex-shrink-0">
          <Flame size={18} className="text-amber-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-sm font-bold text-amber-300">High-Interest Signal Detected</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-400/20 border border-amber-400/40 text-amber-300 uppercase tracking-wider">
              Premium
            </span>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: 'rgba(253,230,138,0.6)' }}>
            Both most recent browsing and dominant product interest point to{' '}
            <span className="font-semibold text-amber-300">{category}</span>.
            Strong purchase intent — ads carry a{' '}
            <span className="font-semibold text-amber-300">{multiplier}× CPM premium</span>.
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-2xl font-bold text-amber-300">{multiplier}×</div>
          <div className="text-[10px] uppercase tracking-wider" style={{ color: 'rgba(251,191,36,0.6)' }}>CPM rate</div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Ad Result Card ───────────────────────────────────────────────────────────
function AdResultCard({ ad, rank, userId, delay, isHighInterest, premiumCpm }: {
  ad: ServedAd;
  rank: number;
  userId: string;
  delay: number;
  isHighInterest: boolean;
  premiumCpm: number;
}) {
  const [clicked, setClicked] = useState(false);
  const score    = ad.relevance_score ?? 0;
  const scoreVal = Math.round(score * 100);

  const handleClick = async () => {
    setClicked(true);
    await adsApi.recordClick(ad.ad_id, { impression_id: ad.impression_id ?? undefined, user_id: userId });
    toast.success('Click recorded');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, ease: [0.16, 1, 0.3, 1] }}
      className={cn('ad-card relative', isHighInterest && 'ring-1 ring-amber-400/30')}
    >
      {isHighInterest && (
        <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center gap-1.5 py-1.5 backdrop-blur-sm"
          style={{ background: 'linear-gradient(to right, rgba(245,158,11,0.8), rgba(251,191,36,0.9), rgba(249,115,22,0.8))' }}
        >
          <Flame size={11} className="text-amber-900" />
          <span className="text-[10px] font-bold text-amber-900 uppercase tracking-wider">
            High-Interest · {premiumCpm}× Premium CPM
          </span>
          <Zap size={10} className="text-amber-900" />
        </div>
      )}

      <div className={cn('relative bg-ink-3 overflow-hidden aspect-[16/7]', isHighInterest && 'mt-7')}>
        {ad.image_url ? (
          <img
            src={ad.image_url.startsWith('/') ? `/api/server${ad.image_url}` : ad.image_url}
            alt={ad.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-4xl opacity-10">◈</div>
          </div>
        )}
        <div className="absolute top-3 left-3 w-7 h-7 rounded-lg bg-canvas/80 backdrop-blur-sm flex items-center justify-center text-xs font-bold text-word-1 border border-edge-2">
          {rank}
        </div>
        <div
          className="absolute top-3 right-3 px-2 py-0.5 rounded-lg bg-canvas/80 backdrop-blur-sm border border-edge-2 font-mono text-xs font-medium"
          style={{ color: scoreColor(score) }}
        >
          {scoreVal}%
        </div>
      </div>

      <div className="p-4 flex flex-col gap-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="badge-sun text-[10px]">{ad.category}</span>
          {ad.brand && <span className="badge-sky text-[10px]">{ad.brand}</span>}
          {isHighInterest && (
            <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-400/15 border border-amber-400/30 text-amber-300">
              <Flame size={8} /> High-Interest
            </span>
          )}
        </div>

        <div>
          <h3 className="text-sm font-semibold text-word-1 leading-snug mb-0.5">{ad.title}</h3>
          <p className="text-xs text-word-2 line-clamp-2 leading-relaxed">{ad.description}</p>
        </div>

        {isHighInterest && (
          <div className="flex items-center gap-2 p-2.5 rounded-lg border border-amber-400/20"
            style={{ background: 'rgba(251,191,36,0.08)' }}
          >
            <Zap size={12} className="text-amber-400 flex-shrink-0" />
            <div>
              <div className="text-[10px] text-amber-400/70 uppercase tracking-wider">Premium Bid Rate</div>
              <div className="text-xs font-mono font-bold text-amber-300">{premiumCpm}× standard CPM</div>
            </div>
          </div>
        )}

        <div className="bg-ink-3 rounded-lg p-3 space-y-2">
          {([
            ['Category', ad.matched_signals.category_score, CHART_COLORS[0]],
            ['Keyword',  ad.matched_signals.keyword_score,  CHART_COLORS[1]],
            ['Brand',    ad.matched_signals.brand_score,    CHART_COLORS[2]],
          ] as [string, number, string][]).map(([lbl, val, col]) => (
            <div key={lbl} className="flex items-center gap-2">
              <span className="text-[10px] text-word-3 w-14 flex-shrink-0">{lbl}</span>
              <div className="flex-1 score-track">
                <motion.div
                  className="score-fill"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.round((val ?? 0) * 100)}%` }}
                  transition={{ delay: delay + 0.2, duration: 0.7, ease: 'easeOut' }}
                  style={{ background: col }}
                />
              </div>
              <span className="text-[10px] font-mono text-word-2 w-8 text-right">
                {Math.round((val ?? 0) * 100)}%
              </span>
            </div>
          ))}
        </div>

        {ad.keywords?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {ad.keywords.slice(0, 4).map(kw => (
              <span key={kw} className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-ink-4 border border-edge-1 text-word-3">
                <Tag size={8} />{kw}
              </span>
            ))}
          </div>
        )}

        <div className="flex gap-2 pt-1">
          <button
            onClick={handleClick}
            disabled={clicked}
            className={cn(
              'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200',
              clicked
                ? 'bg-jade-400/10 text-jade-400 border border-jade-400/20'
                : isHighInterest
                  ? 'text-white active:scale-95'
                  : 'bg-violet-500 hover:bg-violet-600 text-white active:scale-95',
            )}
            style={!clicked && isHighInterest ? {
              background: 'linear-gradient(to right, #f59e0b, #f97316)',
            } : undefined}
          >
            {clicked
              ? <><TrendingUp size={12} /> Clicked!</>
              : <><MousePointerClick size={12} /> Visit Ad</>
            }
          </button>
          {ad.destination_url && (
          <a
              href={ad.destination_url}
              target="_blank"
              rel="noopener noreferrer"
              className="w-8 h-8 flex items-center justify-center rounded-lg bg-ink-3 border border-edge-2 text-word-2 hover:text-word-1 hover:bg-ink-4 transition-all"
            >
              <ExternalLink size={12} />
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ─── DemoPage ─────────────────────────────────────────────────────────────────
export function DemoPage() {
  const pipeline  = usePipeline();
  const isRunning = pipeline.stage === 'extracting' || pipeline.stage === 'serving';

  // ── Profiles — persisted to localStorage so they survive refresh / navigation ──
  const [profiles, setProfiles] = useState<Profile[]>(() => {
    try {
      const saved = localStorage.getItem('adserve_live_profiles');
      if (saved) {
        const parsed = JSON.parse(saved) as Profile[];
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch { /* ignore parse errors */ }
    return SEED_PROFILES;
  });

  // Keep localStorage in sync whenever profiles change
  useEffect(() => {
    try {
      localStorage.setItem('adserve_live_profiles', JSON.stringify(profiles));
    } catch { /* storage full or unavailable */ }
  }, [profiles]);

  const [showAddModal, setShowAddModal] = useState(false);
  const [activeExport, setActiveExport] = useState<{ userId: string; result: ExportHistoryResponse } | null>(null);

  const nextColor = PALETTE[profiles.length % PALETTE.length];

  const handleProfileSelect = useCallback(async (profile: Profile) => {
    setActiveExport(null);
    // runLive: export → extract interests → serve ads, all in sequence
    const exportResult = await pipeline.runLive(profile.user_id, profile.chrome_path);
    if (exportResult) {
      setActiveExport({ userId: profile.user_id, result: exportResult });
      toast.success(`Exported ${exportResult.rows_exported} rows — ads served!`);
    }
  }, [pipeline]);

  const handleAddProfile = useCallback((p: Profile) => {
    setProfiles(prev => [...prev, p]);
  }, []);

  const handleRemoveProfile = useCallback((userId: string) => {
    setProfiles(prev => prev.filter(p => p.user_id !== userId));
    if (pipeline.userId === userId) pipeline.reset();
  }, [pipeline]);

  const sig1Cat     = (pipeline.interests?.top_1_most_recent as Record<string, unknown> | null)?.category as string | undefined;
  const sig2Cat     = (pipeline.interests?.top_2_most_dominant_product as Record<string, unknown> | null)?.category as string | undefined;
  const bothSameCat = !!(sig1Cat && sig2Cat && sig1Cat.toLowerCase() === sig2Cat.toLowerCase());

  return (
    <div className="p-8 max-w-[1200px] mx-auto">
      <PageHeader
        title="Live Ad Pipeline"
        subtitle="Select a profile — exports browser history then runs full personalisation"
      >
        {pipeline.stage !== 'idle' && (
          <button
            onClick={() => { pipeline.reset(); setActiveExport(null); }}
            className="btn btn-ghost flex items-center gap-2"
          >
            <RotateCcw size={14} /> Reset
          </button>
        )}
      </PageHeader>

      {/* ── Profile Grid ── */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
            Demo Profiles
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-secondary btn-sm flex items-center gap-1.5"
          >
            <UserPlus size={13} /> Add Profile
          </button>
        </div>
        <AnimatePresence mode="popLayout">
          <div className="grid grid-cols-3 gap-4">
            {profiles.map(profile => (
              <div key={profile.user_id} className="group">
                <ProfileCard
                  profile={profile}
                  active={pipeline.userId === profile.user_id}
                  running={isRunning && pipeline.userId === profile.user_id}
                  exportResult={activeExport?.userId === profile.user_id ? activeExport.result : null}
                  onSelect={() => handleProfileSelect(profile)}
                  onRemove={() => handleRemoveProfile(profile.user_id)}
                />
              </div>
            ))}
          </div>
        </AnimatePresence>
      </section>

      {/* ── Add Profile Modal ── */}
      <AddProfileModal
        open={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddProfile}
        nextColor={nextColor}
      />
      {/* ── User selector ── */}
      <section className="mb-7">
        <div className="text-xs font-semibold text-word-3 uppercase tracking-widest mb-3">
          Select User Profile
        </div>
        <div className="grid grid-cols-6 gap-3">
          {DEMO_USERS.map(user => (
            <UserCard
              key={user.id}
              user={user}
              active={pipeline.userId === user.id}
              running={isRunning}
              onSelect={() => pipeline.run(user.id)}
            />
          ))}
        </div>
      </section>

      {/* ── Pipeline Visualiser ── */}
      <AnimatePresence>
        {pipeline.stage !== 'idle' && (
          <motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-7"
          >
            <div className="text-xs font-semibold text-word-3 uppercase tracking-widest mb-3">
              Pipeline
            </div>
            <PipelineVis stage={pipeline.stage} />
            {(pipeline.timings.extract || pipeline.timings.serve) && (
              <div className="flex items-center gap-4 mt-3 px-1">
                {pipeline.timings.extract && (
                  <div className="flex items-center gap-1.5 text-xs text-word-3">
                    <Clock size={11} />
                    <span>Extract</span>
                    <span className="font-mono text-violet-300">{pipeline.timings.extract}ms</span>
                  </div>
                )}
                {pipeline.timings.serve && (
                  <div className="flex items-center gap-1.5 text-xs text-word-3">
                    <Cpu size={11} />
                    <span>Serve</span>
                    <span className="font-mono text-jade-300">{pipeline.timings.serve}ms</span>
                  </div>
                )}
                {pipeline.timings.extract && pipeline.timings.serve && (
                  <div className="flex items-center gap-1.5 text-xs text-word-3">
                    <ChevronRight size={11} />
                    <span>Total</span>
                    <span className="font-mono text-sun-400">
                      {pipeline.timings.extract + pipeline.timings.serve}ms
                    </span>
                  </div>
                )}
              </div>
            )}
          </motion.section>
        )}
      </AnimatePresence>

      {/* ── Error ── */}
      <AnimatePresence>
        {pipeline.stage === 'error' && pipeline.error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-7 p-4 border border-coral-400/20 rounded-xl flex items-start gap-3 bg-coral-400/5"
          >
            <AlertTriangle size={16} className="text-coral-400 mt-0.5 flex-shrink-0" />
            <div>
              <div className="text-sm font-semibold text-coral-400 mb-0.5">Pipeline Error</div>
              <div className="text-xs text-coral-400/70">{pipeline.error}</div>
              <div className="text-xs text-word-3 mt-1">
                Ensure Client API is on :8000 and Server API on :8001
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Export Result Summary ── */}
      <AnimatePresence>
        {activeExport && pipeline.userId && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-7 overflow-hidden"
          >
            <div className="bg-jade-400/5 border border-jade-400/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 size={14} className="text-jade-400" />
                <span className="text-sm font-semibold text-jade-400">Browser History Exported</span>
                {activeExport.result.overwritten && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-sun-400/10 border border-sun-400/20 text-sun-400">
                    Overwritten
                  </span>
                )}
              </div>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'User',   value: activeExport.result.user_id,                                icon: <User size={11} /> },
                  { label: 'Rows',   value: activeExport.result.rows_exported.toLocaleString(),         icon: <FileSpreadsheet size={11} /> },
                  { label: 'File',   value: activeExport.result.csv_path.split(/[\\/]/).pop() ?? '',    icon: <FolderDown size={11} /> },
                  { label: 'Status', value: activeExport.result.overwritten ? 'Overwritten' : 'New file', icon: <CheckCircle2 size={11} /> },
                ].map(item => (
                  <div key={item.label} className="bg-ink-3 border border-edge-1 rounded-lg p-2.5">
                    <div className="flex items-center gap-1 text-[10px] text-word-3 mb-1">
                      {item.icon}{item.label}
                    </div>
                    <div className="text-xs font-semibold text-word-1 truncate" title={String(item.value)}>
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-word-3">
                <FolderDown size={10} />
                <span className="font-mono truncate">{activeExport.result.csv_path}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Interest Signals ── */}
      <AnimatePresence>
        {pipeline.interests && (
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-7"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
                Interest Profile — {pipeline.userId}
              </div>
              <div className="flex items-center gap-3 text-xs text-word-3">
                {typeof pipeline.interests.client_metadata?.products_found === 'number' && (
                  <span>{pipeline.interests.client_metadata.products_found} products analysed</span>
                )}
                {pipeline.timings.extract && (
                  <span className="font-mono text-violet-400">⚡ {pipeline.timings.extract}ms</span>
                )}
              </div>
            </div>
            <div className="grid grid-cols-4 gap-3">
              {[
                { num: 1, label: 'Most Recent',      data: pipeline.interests.top_1_most_recent,                   color: CHART_COLORS[0], highlight: bothSameCat },
                { num: 2, label: 'Top Product',       data: pipeline.interests.top_2_most_dominant_product,         color: CHART_COLORS[1], highlight: bothSameCat },
                { num: 3, label: 'Category + Sub',    data: pipeline.interests.top_3_dominant_category_subcategory, color: CHART_COLORS[2], highlight: false },
                { num: 4, label: 'Dominant Category', data: pipeline.interests.top_4_dominant_category,             color: CHART_COLORS[3], highlight: false },
              ].map(sig => (
                <SignalCard key={sig.num} {...sig} isHighlight={sig.highlight} />
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {/* ── High Interest Banner ── */}
      <AnimatePresence>
        {pipeline.isHighInterest && pipeline.highInterestCategory && pipeline.stage !== 'extracting' && (
          <HighInterestBanner
            category={pipeline.highInterestCategory}
            multiplier={pipeline.premiumCpmMultiplier}
          />
        )}
      </AnimatePresence>

      {/* ── Serving loading ── */}
      <AnimatePresence>
        {pipeline.stage === 'serving' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center justify-center gap-3 py-10 text-sm text-word-3"
          >
            <Spinner className="text-violet-400" />
            Matching ads to top-1 interest category…
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Served Ads ── */}
      <AnimatePresence>
        {pipeline.result && pipeline.stage === 'complete' && (
          <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="text-xs font-semibold text-word-3 uppercase tracking-widest">
                  {pipeline.result.ads.length} Ads — Best Matches
                </div>
                {pipeline.result.ads.length === 0 && (
                  <span className="text-[10px] text-coral-400 border border-coral-400/20 rounded-full px-2 py-0.5">
                    No matching ads found
                  </span>
                )}
              </div>
              <div className="flex items-center gap-4 text-xs text-word-3">
                <span>{pipeline.result.total_candidates_evaluated} evaluated</span>
                {pipeline.timings.serve && (
                  <span className="font-mono text-jade-400">⚡ {pipeline.timings.serve}ms</span>
                )}
              </div>
            </div>

            {pipeline.result.signals_used && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                <span className="text-[10px] text-word-3 mr-1 self-center">Matched on:</span>
                {pipeline.result.signals_used.categories.map(c => (
                  <span key={c} className="badge-sun text-[10px]">{c}</span>
                ))}
                {pipeline.result.signals_used.brands.map(b => (
                  <span key={b} className="badge-sky text-[10px]">{b}</span>
                ))}
                {pipeline.result.signals_used.interest_tokens.slice(0, 4).map(t => (
                  <span key={t} className="badge-muted text-[10px]">{t}</span>
                ))}
              </div>
            )}

            <div className={cn(
              'grid gap-4',
              pipeline.result.ads.length === 1 ? 'grid-cols-1 max-w-md' :
              pipeline.result.ads.length === 2 ? 'grid-cols-2' : 'grid-cols-3',
            )}>
              {pipeline.result.ads.map((ad, i) => (
                <AdResultCard
                  key={ad.ad_id}
                  ad={ad}
                  rank={i + 1}
                  userId={pipeline.userId!}
                  delay={i * 0.1}
                  isHighInterest={pipeline.isHighInterest}
                  premiumCpm={pipeline.premiumCpmMultiplier}
                />
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  );
}