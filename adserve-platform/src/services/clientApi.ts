// import axios from 'axios';
// import type { InterestSignals } from '@/types';
// import { CLIENT_BASE } from '@/constants';

// const http = axios.create({ baseURL: CLIENT_BASE, timeout: 120_000 });

// export const clientApi = {
//   extract: async (userId: string): Promise<InterestSignals> => {
//     const { data } = await http.post<{
//       top_1_most_recent: Record<string, unknown> | null;
//       top_2_most_dominant_product: Record<string, unknown> | null;
//       top_3_dominant_category_subcategory: Record<string, unknown> | null;
//       top_4_dominant_category: Record<string, unknown> | null;
//       metadata: Record<string, unknown>;
//       success: boolean;
//       error?: string;
//     }>('/extract', { user_id: userId, max_products: 100, verbose: false });

//     if (!data.success && data.error) throw new Error(data.error);

//     return {
//       user_id: userId,
//       top_1_most_recent:                   data.top_1_most_recent   as InterestSignals['top_1_most_recent'],
//       top_2_most_dominant_product:         data.top_2_most_dominant_product as InterestSignals['top_2_most_dominant_product'],
//       top_3_dominant_category_subcategory: data.top_3_dominant_category_subcategory as InterestSignals['top_3_dominant_category_subcategory'],
//       top_4_dominant_category:             data.top_4_dominant_category as InterestSignals['top_4_dominant_category'],
//       client_metadata: data.metadata ?? null,
//     };
//   },
// };
import axios from 'axios';
import type { InterestSignals } from '@/types';
import { CLIENT_BASE } from '@/constants';

const http = axios.create({ baseURL: CLIENT_BASE, timeout: 120_000 });
const exportHttp = axios.create({ baseURL: CLIENT_BASE, timeout: 120_000 });

export interface ExportHistoryResponse {
  success: boolean;
  user_id: string;
  csv_path: string;
  rows_exported: number;
  overwritten: boolean;
  error: string | null;
}

export const clientApi = {
  exportHistory: async (userId: string, chromeProfilePath: string): Promise<ExportHistoryResponse> => {
    const { data } = await exportHttp.post<ExportHistoryResponse>(
      '/browser-history/export',
      { user_id: userId, chrome_profile_path: chromeProfilePath },
    );
    if (!data.success && data.error) throw new Error(data.error);
    return data;
  },

  extract: async (userId: string): Promise<InterestSignals> => {
    const { data } = await http.post<{
      top_1_most_recent: Record<string, unknown> | null;
      top_2_most_dominant_product: Record<string, unknown> | null;
      top_3_dominant_category_subcategory: Record<string, unknown> | null;
      top_4_dominant_category: Record<string, unknown> | null;
      metadata: Record<string, unknown>;
      success: boolean;
      error?: string;
    }>('/extract', { user_id: userId, max_products: 100, verbose: false });

    if (!data.success && data.error) throw new Error(data.error);

    return {
      user_id: userId,
      top_1_most_recent:                   data.top_1_most_recent   as InterestSignals['top_1_most_recent'],
      top_2_most_dominant_product:         data.top_2_most_dominant_product as InterestSignals['top_2_most_dominant_product'],
      top_3_dominant_category_subcategory: data.top_3_dominant_category_subcategory as InterestSignals['top_3_dominant_category_subcategory'],
      top_4_dominant_category:             data.top_4_dominant_category as InterestSignals['top_4_dominant_category'],
      client_metadata: data.metadata ?? null,
    };
  },
};