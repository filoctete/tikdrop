const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface OpportunitySummary {
  candidate_key: string;
  total_score: number;
  recommendation: string;
  recommendation_reason: string;
  status: string;
  scored_at: string;
}

export interface DimensionScore {
  raw_score: number;
  weight: number;
  weighted_contribution: number;
}

export interface ProductScoreResult {
  product_name: string;
  dimensions: Record<string, DimensionScore>;
  total_score: number;
  recommendation: string;
  recommendation_reason: string;
}

export interface ProductScoreInput {
  product_name: string;
  portugal_opportunity: {
    pt_competitor_count: number;
    differentiation_score: number;
  };
  costs: {
    sale_price: number;
    product_cost: number;
    shipping_cost: number;
    payment_fees: number;
    ad_cost_per_unit: number;
    returns_cost_estimate: number;
    other_costs: number;
  };
  supplier: Record<string, boolean>;
  logistics: {
    weight_grams: number;
    avg_shipping_days: number;
    fragile: boolean;
    size_category: string;
  };
}

export interface OpportunityDetail {
  result: ProductScoreResult;
  input: ProductScoreInput | null;
}

export interface QuickScoreRequest {
  name: string;
  product_cost: number;
  sale_price: number;
  weight_grams: number;
  demo_video_feasibility?: number;
  ugc_potential?: number;
  avg_shipping_days?: number;
}

export interface VatCheckRequest {
  country_code: string;
  vat_number: string;
}

export interface VatCheckResult {
  country_code: string;
  vat_number: string;
  valid: boolean;
  name: string | null;
  address: string | null;
  request_date: string | null;
}

export async function listOpportunities(status?: string): Promise<OpportunitySummary[]> {
  const url = new URL(`${API_URL}/opportunities`);
  if (status) url.searchParams.set("status", status);
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch opportunities: ${res.status}`);
  return res.json();
}

export async function getOpportunity(candidateKey: string): Promise<OpportunityDetail> {
  const res = await fetch(`${API_URL}/opportunities/${encodeURIComponent(candidateKey)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch opportunity: ${res.status}`);
  return res.json();
}

export async function quickScore(req: QuickScoreRequest): Promise<ProductScoreResult> {
  const res = await fetch(`${API_URL}/opportunities/quick-score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to score candidate: ${res.status} ${detail}`);
  }
  return res.json();
}

export async function checkVat(req: VatCheckRequest): Promise<VatCheckResult> {
  const res = await fetch(`${API_URL}/suppliers/vat-check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`VAT check failed: ${res.status} ${detail}`);
  }
  return res.json();
}
