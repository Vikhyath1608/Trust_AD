// ─── Live Demo Profile Configuration ─────────────────────────────────────────
// Edit this list with real names / emails / Chrome paths.
// user_id is auto-generated from name at runtime ("Vikhyath" → "vikhyath")
export const LIVE_PROFILES = [
  {
    name:        'Vikhyath',
    email:       'vikhyathraims0901@gmail.com',
    chrome_path: 'C:\\Users\\lapca\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 3',
    color:       '#8b5cf6',
  },
] as const;

export type LiveProfile = (typeof LIVE_PROFILES)[number] & { user_id: string };

export const AD_CATEGORIES = [
  'Electronics', 'Fashion', 'Home Appliances', 'Automotive',
  'Health & Fitness', 'Food & Grocery', 'Travel', 'Education',
  'Beauty & Personal Care', 'Sports & Outdoors', 'Finance',
  'Real Estate', 'Technology', 'Other',
] as const;

export const DEMO_USERS = [
  { id: 'user1', initials: 'U1', color: '#8b5cf6', hue: 'violet' },
  { id: 'user2', initials: 'U2', color: '#34d399', hue: 'jade' },
  { id: 'user3', initials: 'U3', color: '#fbbf24', hue: 'sun' },
  { id: 'user4', initials: 'U4', color: '#f87171', hue: 'coral' },
  { id: 'user5', initials: 'U5', color: '#a78bfa', hue: 'violet' },
  { id: 'vikhyath_rai', initials: 'U6', color: '#38bdf8', hue: 'sky' },
] as const;

export const CHART_COLORS = [
  '#8b5cf6', '#34d399', '#fbbf24', '#f87171',
  '#38bdf8', '#a78bfa', '#f97316', '#e879f9',
  '#84cc16', '#06b6d4',
];

export const SERVER_BASE = '/api/server';
export const CLIENT_BASE = '/api/v1';