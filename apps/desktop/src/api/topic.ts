import request from "./request";

export interface IndustryNode {
  id: number;
  name: string;
  parent_id: number | null;
  keywords: string[] | null;
  description?: string | null;
  sort: number;
  children: IndustryNode[];
}

export interface SysTopic {
  id: number;
  title: string;
  industry_id: number | null;
  potential_score: number;
  heat_index: number;
  reason: string | null;
  keywords: string[] | null;
  platform_heat: Record<string, unknown> | null;
  heat_sources: unknown[] | string[] | null;
  trend: Record<string, unknown> | unknown[] | null;
  industry_tags: string[] | null;
  target_audience: unknown[] | Record<string, unknown> | null;
  creative_angles: string[] | null;
  content_outline: unknown[] | Record<string, unknown> | null;
  format_suggestions: string[] | null;
  material_clues: unknown[] | Record<string, unknown> | null;
  risk_notes: string[] | null;
  status: number;
  created_at: string | null;
}

export function getIndustriesApi() {
  return request.get<any, IndustryNode[]>("/topic/industries");
}

export function getSysTopicRecommendationsApi(params?: {
  industry_id?: number;
  limit?: number;
}) {
  return request.get<any, SysTopic[]>("/topic/recommendations", { params });
}
