export type Summary = {
  properties_available: number; clients: number; active_requirements: number; new_matches: number;
  leads_by_stage: Record<string, number>; leads_by_source: Record<string, number>; conversion_rate: number;
};
export type Property = {
  id: string; title: string; purpose: "sale" | "rent"; property_type: string; status: string; price: number;
  currency: string; bedrooms: number | null; city: string | null; area_name: string | null;
  area_value: number | null; area_unit: string | null; permit_number: string | null;
};
export type Client = { id: string; name: string; phone: string; email: string | null; source: string | null; notes: string | null };
export type Lead = { id: string; client_id: string; stage: string; source: string | null; value: number | null; currency: string | null };
export type Breakdown = Record<string, { points: number; max: number; note: string }>;
export type DetailedMatch = {
  id: string; score: number; breakdown: Breakdown; status: string;
  property: { id: string; title: string; price: number; currency: string; city: string | null; area_name: string | null; bedrooms: number | null; purpose: string };
  client: { id: string; name: string; phone: string };
  requirement: { id: string; urgency: string; budget_max: number | null; currency: string; preferred_areas: string[] };
};
export type Activity = { id: string; type: string; note: string | null; due_at: string | null; lead_id: string | null };
export const STAGES = ["new", "contacted", "viewing", "negotiation", "won", "lost"] as const;
