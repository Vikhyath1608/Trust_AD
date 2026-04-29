
import { useState, useCallback } from 'react';
import type { PipelineStage, InterestSignals, ServeResult } from '@/types';
import { clientApi } from '@/services/clientApi';
import { servingApi } from '@/services/serverApi';
import { getErrorMessage } from '@/lib/utils';

interface PipelineState {
  stage: PipelineStage;
  userId: string | null;
  interests: InterestSignals | null;
  result: ServeResult | null;
  error: string | null;
  timings: { extract?: number; serve?: number };
  isHighInterest: boolean;
  highInterestCategory: string | null;
  premiumCpmMultiplier: number;
}

const INIT: PipelineState = {
  stage: 'idle', userId: null, interests: null, result: null,
  error: null, timings: {}, isHighInterest: false,
  highInterestCategory: null, premiumCpmMultiplier: 1.0,
};

function normCat(signal: Record<string, unknown> | null): string | null {
  if (!signal) return null;
  return (signal.category as string | undefined)?.toLowerCase().trim() ?? null;
}

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(INIT);

  const reset = useCallback(() => setState(INIT), []);

  // ── Shared: given interests already fetched, detect high-interest and serve ads ──
  const _serveAds = useCallback(async (
    userId: string,
    interests: InterestSignals,
    extractMs: number,
  ) => {
    const cat1 = normCat(interests.top_1_most_recent as Record<string, unknown> | null);
    const cat2 = normCat(interests.top_2_most_dominant_product as Record<string, unknown> | null);
    const isHighInterest = !!(cat1 && cat2 && cat1 === cat2);
    const highInterestCategory = isHighInterest
      ? (interests.top_1_most_recent as Record<string, unknown>)?.category as string
      : null;
    const premiumCpmMultiplier = isHighInterest ? 2.5 : 1.0;

    setState(s => ({
      ...s, stage: 'extracted', interests, userId, timings: { extract: extractMs },
      isHighInterest, highInterestCategory, premiumCpmMultiplier,
    }));

    await new Promise(r => setTimeout(r, 600));
    setState(s => ({ ...s, stage: 'serving' }));

    const t1 = Date.now();
    let result: ServeResult;
    try {
      result = await servingApi.fromSignals(interests, 3);
    } catch (err) {
      setState(s => ({ ...s, stage: 'error', error: `Server API error: ${getErrorMessage(err)}` }));
      return;
    }
    const serveMs = Date.now() - t1;

    setState(s => ({
      ...s, stage: 'complete', result,
      timings: { extract: extractMs, serve: serveMs },
    }));
  }, []);

  /**
   * Standard demo-user flow (user_1..user_6):
   * extract interests from existing CSV → serve ads
   */
  const run = useCallback(async (userId: string) => {
    setState({ ...INIT, stage: 'extracting', userId });

    const t0 = Date.now();
    let interests: InterestSignals;
    try {
      interests = await clientApi.extract(userId);
    } catch (err) {
      setState(s => ({ ...s, stage: 'error', error: `Client API error: ${getErrorMessage(err)}` }));
      return;
    }

    await _serveAds(userId, interests, Date.now() - t0);
  }, [_serveAds]);

  /**
   * Live-profile flow:
   * 1. Export Chrome history to CSV
   * 2. Extract interests from that fresh CSV
   * 3. Serve ads using the extracted interests
   * Returns the export result for the UI banner.
   */
  const runLive = useCallback(async (userId: string, chromeProfilePath: string) => {
    setState({ ...INIT, stage: 'extracting', userId });

    const t0 = Date.now();

    // Step 1 — export Chrome history
    let exportResult;
    try {
      exportResult = await clientApi.exportHistory(userId, chromeProfilePath);
    } catch (err) {
      setState(s => ({ ...s, stage: 'error', error: `Export error: ${getErrorMessage(err)}` }));
      return null;
    }

    // Step 2 — extract interests (reads the CSV just written)
    let interests: InterestSignals;
    try {
      interests = await clientApi.extract(userId);
    } catch (err) {
      setState(s => ({ ...s, stage: 'error', error: `Extract error: ${getErrorMessage(err)}` }));
      return null;
    }

    // Step 3 — serve ads using those interests
    await _serveAds(userId, interests, Date.now() - t0);

    return exportResult;
  }, [_serveAds]);

  return { ...state, run, runLive, reset };
}