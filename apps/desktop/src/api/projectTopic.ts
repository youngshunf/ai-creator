import request from "./request";

export interface ProjectTopic {
  id: string;
  project_id: string;
  user_id: string;
  title: string;
  potential_score: number;
  heat_index: number;
  reason: string;
  keywords: string[];
  platform_heat: Record<string, unknown>;
  heat_sources: unknown[];
  trend: Record<string, unknown>;
  industry_tags: string[];
  target_audience: unknown[] | Record<string, unknown>;
  creative_angles: string[];
  content_outline: unknown[] | Record<string, unknown>;
  format_suggestions: string[];
  material_clues: unknown[] | Record<string, unknown>;
  risk_notes: string[];
  source_info: Record<string, unknown>;
  batch_date: string | null;
  source_uid: string | null;
  status: number;
  is_deleted: boolean;
  last_sync_at: string | null;
  server_version: number;
  created_time: string;
  updated_time: string | null;
}

export function getProjectTopicsApi(projectId: string) {
  return request.get<any, ProjectTopic[]>(`/projects/${projectId}/topics`);
}
