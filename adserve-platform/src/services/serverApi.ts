import axios from 'axios';
import type {
  Ad, PaginatedAds, AdFormValues, PlatformOverview,
  TimePoint, ServeResult, InterestSignals,
} from '@/types';
import { SERVER_BASE } from '@/constants';

const http = axios.create({ baseURL: SERVER_BASE, timeout: 60_000 });

http.interceptors.response.use(
  (r) => r,
  (err) => {
    const d = err.response?.data;
    const msg = d?.detail?.message ?? d?.detail ?? d?.message ?? err.message;
    return Promise.reject(new Error(typeof msg === 'string' ? msg : JSON.stringify(msg)));
  }
);

// Ad AI Generation
export const adGenerateApi = {
  generate: (payload: { title: string; description: string; brand?: string; destination_url?: string }) =>
    http.post<{ category: string; keywords: string[]; confidence: number; llm_used: boolean }>(
      '/ads/generate', payload
    ).then(r => r.data),
};

// Ads
export const adsApi = {
  list: (p?: { page?: number; page_size?: number; active_only?: boolean; category?: string }) =>
    http.get<PaginatedAds>('/ads/', { params: p }).then(r => r.data),

  get: (id: number) =>
    http.get<Ad>(`/ads/${id}`).then(r => r.data),

  create: (v: Omit<AdFormValues, 'image_url' | 'destination_url' | 'brand'> & {
    image_url?: string | null; destination_url?: string | null; brand?: string | null;
  }) => http.post<Ad>('/ads/', v).then(r => r.data),

  update: (id: number, v: Partial<AdFormValues>) =>
    http.patch<Ad>(`/ads/${id}`, v).then(r => r.data),

  toggle: (id: number) =>
    http.patch<Ad>(`/ads/${id}/toggle`, {}).then(r => r.data),

  remove: (id: number) => http.delete(`/ads/${id}`),

  recordClick: (adId: number, opts?: { impression_id?: number | null; user_id?: string }) =>
    http.post(`/ads/${adId}/click`, null, { params: opts }).catch(() => {}),
};

// Analytics
export const analyticsApi = {
  overview: (topN = 8) =>
    http.get<PlatformOverview>('/analytics/overview', { params: { top_n: topN } }).then(r => r.data),

  keywords: (limit = 15) =>
    http.get<{ keywords: Record<string, number> }>('/analytics/keywords', { params: { limit } }).then(r => r.data),

  timeSeries: () =>
    http.get<{ series: TimePoint[] }>('/analytics/impressions/time').then(r => r.data),
};

// Serving
export const servingApi = {
  fromSignals: (signals: InterestSignals, maxAds = 3) =>
    http.post<ServeResult>('/serve/from-signals', { signals, max_ads: maxAds, record_impression: true }).then(r => r.data),
};

// Health
export const healthApi = {
  ping: () => http.get('/health').then(r => r.data as { status: string }),
};