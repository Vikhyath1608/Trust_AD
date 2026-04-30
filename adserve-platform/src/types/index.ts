// ─── Ad Types ─────────────────────────────────────────────────────────────────
export interface Ad {
  id: number;
  title: string;
  description: string;
  image_url: string | null;
  destination_url: string | null;
  category: string;
  brand: string | null;
  keywords: string[];
  budget: number;
  bid_cpm: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  impression_count: number | null;
  click_count: number | null;
  ctr: number | null;
}

export interface AdSummary
  extends Pick<Ad, 'id' | 'title' | 'category' | 'brand' | 'is_active'
    | 'impression_count' | 'click_count' | 'ctr' | 'created_at'> {}

export interface PaginatedAds {
  items: AdSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdFormValues {
  title: string;
  description: string;
  image_url: string;
  destination_url: string;
  category: string;
  brand: string;
  keywords: string[];
  budget: number;
  bid_cpm: number;
  is_active: boolean;
}

// ─── Analytics Types ──────────────────────────────────────────────────────────
export interface CategoryStat {
  category: string;
  ad_count: number;
  total_impressions: number;
  total_clicks: number;
  avg_ctr: number;
}

export interface AdStat {
  ad_id: number;
  title: string;
  category: string;
  brand: string | null;
  impression_count: number;
  click_count: number;
  ctr: number;
  budget: number;
  bid_cpm: number;
  is_active: boolean;
  created_at: string;
}

export interface PlatformOverview {
  total_ads: number;
  active_ads: number;
  inactive_ads: number;
  total_impressions: number;
  total_clicks: number;
  overall_ctr: number;
  top_categories: CategoryStat[];
  top_ads_by_impressions: AdStat[];
  top_ads_by_ctr: AdStat[];
}

export interface TimePoint { day: string; impressions: number; }

// ─── Interest / Pipeline Types ────────────────────────────────────────────────
export interface InterestSignal {
  category?: string;
  subcategory?: string;
  product?: string;
  brand?: string;
  query?: string;
  total_engagement_score?: number;
  [key: string]: unknown;
}

export interface InterestSignals {
  user_id: string;
  top_1_most_recent:                   InterestSignal | null;
  top_2_most_dominant_product:         InterestSignal | null;
  top_3_dominant_category_subcategory: InterestSignal | null;
  top_4_dominant_category:             InterestSignal | null;
  client_metadata: Record<string, unknown> | null;
}

export interface MatchScores {
  category_score: number;
  keyword_score:  number;
  brand_score:    number;
  composite_score: number;
}

export interface ServedAd {
  ad_id: number;
  title: string;
  description: string;
  image_url: string | null;
  destination_url: string | null;
  category: string;
  brand: string | null;
  keywords: string[];
  relevance_score: number;
  match_rank: number;
  matched_signals: MatchScores;
  impression_id: number | null;
}

export interface ServeResult {
  user_id: string;
  ads: ServedAd[];
  total_candidates_evaluated: number;
  signals_used: { categories: string[]; brands: string[]; interest_tokens: string[] };
}

export type PipelineStage =
  | 'idle'
  | 'extracting'
  | 'extracted'
  | 'serving'
  | 'complete'
  | 'error';
