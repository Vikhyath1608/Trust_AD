
import React, { useState, useRef } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Sparkles, CheckCircle2, AlertTriangle, Upload, Link, ImageIcon, Loader2 } from 'lucide-react';
import { Input, Textarea, Toggle, Spinner } from '@/components/ui';
import { adGenerateApi } from '@/services/serverApi';
import { cn } from '@/lib/utils';
import type { Ad, AdFormValues } from '@/types';

const SERVER_BASE = '/api/server';

const schema = z.object({
  title:           z.string().min(3, 'Title must be at least 3 characters').max(200),
  description:     z.string().min(10, 'Description must be at least 10 characters'),
  image_url:       z.string().url('Must be a valid URL').or(z.literal('')).optional(),
  destination_url: z.string().url('Must be a valid URL').or(z.literal('')).optional(),
  category:        z.string().min(1, 'Category is required'),
  brand:           z.string().optional(),
  keywords:        z.array(z.string()),
  budget:          z.coerce.number().min(0, 'Budget must be >= 0'),
  bid_cpm:         z.coerce.number().min(0, 'CPM must be >= 0'),
  is_active:       z.boolean(),
});

interface Props {
  defaultValues?: Ad;
  onSubmit: (values: AdFormValues) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
}

type ImageTab = 'url' | 'upload';

export function AdForm({ defaultValues, onSubmit, onCancel, isLoading }: Props) {
  const [generating, setGenerating] = useState(false);
  const [genStatus, setGenStatus]   = useState<'idle' | 'ok' | 'error'>('idle');
  const [genMessage, setGenMessage] = useState('');
  const [genLlmUsed, setGenLlmUsed] = useState(false);

  // Image upload state
  const [imageTab, setImageTab]         = useState<ImageTab>('url');
  const [uploading, setUploading]       = useState(false);
  const [uploadedUrl, setUploadedUrl]   = useState<string | null>(null);
  const [uploadError, setUploadError]   = useState<string | null>(null);
  const [previewSrc, setPreviewSrc]     = useState<string | null>(
    defaultValues?.image_url ?? null
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    register, handleSubmit, control, watch, setValue,
    formState: { errors },
  } = useForm<AdFormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues
      ? {
          title:           defaultValues.title,
          description:     defaultValues.description,
          image_url:       defaultValues.image_url ?? '',
          destination_url: defaultValues.destination_url ?? '',
          category:        defaultValues.category,
          brand:           defaultValues.brand ?? '',
          keywords:        defaultValues.keywords ?? [],
          budget:          defaultValues.budget,
          bid_cpm:         defaultValues.bid_cpm,
          is_active:       defaultValues.is_active,
        }
      : {
          title: '', description: '', image_url: '', destination_url: '',
          category: '', brand: '', keywords: [], budget: 1000, bid_cpm: 2, is_active: true,
        },
  });

  const keywords       = watch('keywords');
  const titleVal       = watch('title');
  const descriptionVal = watch('description');
  const brandVal       = watch('brand');
  const destinationVal = watch('destination_url');
  const imageUrlVal    = watch('image_url');

  // ── Keyword helpers ──────────────────────────────────────────────────────
  const addKeyword = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const input = e.currentTarget;
    const kw = input.value.trim().toLowerCase();
    if (kw && !keywords.includes(kw) && keywords.length < 20) {
      setValue('keywords', [...keywords, kw]);
      input.value = '';
    }
  };
  const removeKeyword = (kw: string) => setValue('keywords', keywords.filter(k => k !== kw));

  // ── AI Generate ──────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!titleVal?.trim() || !descriptionVal?.trim()) {
      setGenStatus('error');
      setGenMessage('Fill in Title and Description first.');
      return;
    }
    setGenerating(true); setGenStatus('idle'); setGenMessage('');
    try {
      const result = await adGenerateApi.generate({
        title:           titleVal.trim(),
        description:     descriptionVal.trim(),
        brand:           brandVal?.trim() || undefined,
        destination_url: destinationVal?.trim() || undefined,
      });
      setValue('category', result.category);
      const merged = Array.from(new Set([...result.keywords, ...keywords])).slice(0, 20);
      setValue('keywords', merged);
      setGenLlmUsed(result.llm_used);
      setGenStatus('ok');
      setGenMessage(`Generated via ${result.llm_used ? 'LLM' : 'heuristic'} · confidence ${Math.round(result.confidence * 100)}%`);
    } catch (err) {
      setGenStatus('error');
      setGenMessage(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  // ── Image upload ──────────────────────────────────────────────────────────
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Local preview immediately
    const reader = new FileReader();
    reader.onload = ev => setPreviewSrc(ev.target?.result as string);
    reader.readAsDataURL(file);

    setUploading(true);
    setUploadError(null);
    setUploadedUrl(null);

    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${SERVER_BASE}/ads/upload-image`, {
        method: 'POST',
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed (${res.status})`);
      }
      const data = await res.json() as { url: string };
      const fullUrl = `${SERVER_BASE}${data.url}`;
      setUploadedUrl(fullUrl);
      setValue('image_url', fullUrl);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
      setPreviewSrc(null);
    } finally {
      setUploading(false);
      // Reset file input so same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleUrlBlur = () => {
    const v = imageUrlVal?.trim();
    if (v && v.startsWith('http')) setPreviewSrc(v);
  };

  const clearImage = () => {
    setValue('image_url', '');
    setUploadedUrl(null);
    setPreviewSrc(null);
    setUploadError(null);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

      {/* ── Creative ── */}
      <div className="space-y-4 p-4 bg-ink-3/50 rounded-xl border border-edge-1">
        <div className="text-xs font-semibold text-word-3 uppercase tracking-wider">Creative</div>

        <div>
          <label className="field-label">Ad Title <span className="text-coral-400">*</span></label>
          <Input {...register('title')} placeholder="e.g. Samsung Galaxy S24 — Best Price Guaranteed" error={errors.title?.message} />
        </div>

        <div>
          <label className="field-label">Description <span className="text-coral-400">*</span></label>
          <Textarea {...register('description')} rows={3} placeholder="Compelling ad copy that resonates with your audience…" error={errors.description?.message} />
        </div>

        <div>
          <label className="field-label">Click-Through URL</label>
          <Input {...register('destination_url')} placeholder="https://yoursite.com/landing" error={errors.destination_url?.message} />
        </div>

        {/* ── Image — tab switcher ── */}
        <div>
          <label className="field-label">Creative Image</label>

          {/* Tab row */}
          <div className="flex items-center gap-1 mb-3 p-1 bg-ink-4 rounded-lg w-fit border border-edge-1">
            {(['url', 'upload'] as ImageTab[]).map(tab => (
              <button
                key={tab}
                type="button"
                onClick={() => setImageTab(tab)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-150',
                  imageTab === tab
                    ? 'bg-ink-2 text-word-1 shadow border border-edge-2'
                    : 'text-word-3 hover:text-word-2',
                )}
              >
                {tab === 'url'
                  ? <><Link size={11} /> Image URL</>
                  : <><Upload size={11} /> Upload File</>
                }
              </button>
            ))}
          </div>

          {/* URL tab */}
          {imageTab === 'url' && (
            <div className="space-y-2">
              <Input
                {...register('image_url')}
                placeholder="https://cdn.example.com/creative.jpg"
                error={errors.image_url?.message}
                onBlur={handleUrlBlur}
              />
            </div>
          )}

          {/* Upload tab */}
          {imageTab === 'upload' && (
            <div className="space-y-2">
              {/* Drop zone */}
              <div
                onClick={() => !uploading && fileInputRef.current?.click()}
                className={cn(
                  'relative flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed',
                  'py-8 cursor-pointer transition-all duration-150 text-center',
                  uploading
                    ? 'border-violet-500/40 bg-violet-500/5 cursor-wait'
                    : 'border-edge-2 hover:border-violet-500/50 hover:bg-violet-500/5',
                )}
              >
                {uploading ? (
                  <>
                    <Loader2 size={22} className="text-violet-400 animate-spin" />
                    <span className="text-xs text-word-3">Uploading…</span>
                  </>
                ) : (
                  <>
                    <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                      <Upload size={18} className="text-violet-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-word-2">Click to upload</p>
                      <p className="text-xs text-word-3 mt-0.5">JPEG, PNG, WebP, GIF · max 10 MB</p>
                    </div>
                  </>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="hidden"
                onChange={handleFileChange}
                disabled={uploading}
              />

              {uploadError && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-coral-400/8 border border-coral-400/20 text-xs text-coral-400">
                  <AlertTriangle size={12} className="flex-shrink-0" />
                  {uploadError}
                </div>
              )}

              {uploadedUrl && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-jade-400/8 border border-jade-400/20 text-xs text-jade-400">
                  <CheckCircle2 size={12} className="flex-shrink-0" />
                  <span className="truncate font-mono">{uploadedUrl}</span>
                </div>
              )}
            </div>
          )}

          {/* Preview — shown for both tabs when there's an image */}
          {previewSrc && (
            <div className="relative mt-3 rounded-xl overflow-hidden border border-edge-1 bg-ink-3 aspect-[16/7]">
              <img
                src={previewSrc}
                alt="Preview"
                className="w-full h-full object-cover"
                onError={() => setPreviewSrc(null)}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
              <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-black/50 backdrop-blur-sm text-[10px] text-white font-medium">
                <ImageIcon size={10} /> Preview
              </div>
              <button
                type="button"
                onClick={clearImage}
                className="absolute top-2 right-2 w-6 h-6 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-sm flex items-center justify-center text-white transition-colors"
                title="Remove image"
              >
                <X size={11} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── Targeting ── */}
      <div className="space-y-4 p-4 bg-ink-3/50 rounded-xl border border-edge-1">
        <div className="flex items-center justify-between">
          <div className="text-xs font-semibold text-word-3 uppercase tracking-wider">Targeting</div>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating || !titleVal?.trim() || !descriptionVal?.trim()}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold',
              'transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed active:scale-95',
              'bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400',
              'text-white border border-violet-400/30',
            )}
          >
            {generating
              ? <><Spinner className="text-white" /> Generating…</>
              : <><Sparkles size={13} /> AI Generate</>
            }
          </button>
        </div>

        {genStatus !== 'idle' && (
          <div className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg text-xs border',
            genStatus === 'ok'
              ? 'bg-jade-400/8 border-jade-400/20 text-jade-400'
              : 'bg-coral-400/8 border-coral-400/20 text-coral-400',
          )}>
            {genStatus === 'ok'
              ? <CheckCircle2 size={13} className="flex-shrink-0" />
              : <AlertTriangle size={13} className="flex-shrink-0" />
            }
            <span>{genMessage}</span>
            {genStatus === 'ok' && !genLlmUsed && (
              <span className="ml-auto text-[10px] text-word-3">LLM unavailable — used heuristic</span>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="field-label">
              Category <span className="text-coral-400">*</span>
              <span className="ml-1.5 text-[10px] text-word-3 normal-case font-normal">(type freely or use AI Generate)</span>
            </label>
            <Input {...register('category')} placeholder="e.g. Electronics, Fashion, Automotive…" error={errors.category?.message} />
          </div>
          <div>
            <label className="field-label">Brand</label>
            <Input {...register('brand')} placeholder="e.g. Samsung, Nike…" />
          </div>
        </div>

        <div>
          <label className="field-label">Keywords ({keywords.length}/20)</label>
          <input
            className="field-input mb-2"
            placeholder="Type keyword and press Enter — or click AI Generate above"
            onKeyDown={addKeyword}
          />
          {keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {keywords.map(kw => (
                <span key={kw} className="flex items-center gap-1 pl-2.5 pr-1.5 py-1 rounded-full text-xs font-medium bg-violet-500/10 text-violet-300 border border-violet-500/20">
                  {kw}
                  <button type="button" onClick={() => removeKeyword(kw)} className="w-4 h-4 rounded-full hover:bg-violet-500/30 flex items-center justify-center transition-colors">
                    <X size={10} />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Budget & Status ── */}
      <div className="grid grid-cols-3 gap-3 p-4 bg-ink-3/50 rounded-xl border border-edge-1">
        <div className="col-span-3 text-xs font-semibold text-word-3 uppercase tracking-wider mb-1">Budget & Status</div>
        <div>
          <label className="field-label">Total Budget (USD)</label>
          <Input {...register('budget')} type="number" min={0} step={100} error={errors.budget?.message} />
        </div>
        <div>
          <label className="field-label">Bid CPM (USD)</label>
          <Input {...register('bid_cpm')} type="number" min={0} step={0.5} error={errors.bid_cpm?.message} />
        </div>
        <div className="flex flex-col justify-end pb-0.5">
          <label className="field-label">Active</label>
          <Controller
            name="is_active"
            control={control}
            render={({ field }) => (
              <Toggle checked={field.value} onChange={field.onChange} label={field.value ? 'Will serve' : 'Paused'} />
            )}
          />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-1">
        <button type="button" onClick={onCancel} className="btn-secondary btn">Cancel</button>
        <button type="submit" disabled={isLoading} className="btn-primary btn min-w-[110px]">
          {isLoading ? <Spinner className="text-white" /> : defaultValues ? 'Save Changes' : 'Create Ad'}
        </button>
      </div>
    </form>
  );
}