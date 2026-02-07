// Trial Types
export interface Condition {
  name: string;
}

export interface Intervention {
  intervention_type: string;
  name: string;
  description?: string;
}

export interface Trial {
  nct_id: string;
  brief_title: string;
  official_title?: string;
  phase: string;
  overall_status: string;
  study_type?: string;
  brief_summaries_description?: string;
  detailed_description?: string;
  conditions: Condition[];
  interventions?: Intervention[];
  enrollment?: number;
  start_date?: string;
  completion_date?: string;
  source?: string;
}

export interface TrialDetail extends Trial {
  sponsors?: Array<{ name: string }>;
  facilities?: Array<{
    name?: string;
    city?: string;
    state?: string;
    country?: string;
  }>;
}

// Search Types
export interface SearchRequest {
  query: string;
  page?: number;
  page_size?: number;
  phases?: string[];
  statuses?: string[];
  city?: string;
}

export interface SearchResponse {
  query: string;
  results: Trial[];
  total_results: number;
  page: number;
  page_size: number;
  total_pages: number;
  search_type: 'intelligent' | 'hybrid' | 'basic';
  confidence?: number;
  extracted_entities?: ExtractedEntities;
}

export interface ExtractedEntities {
  phase?: string | null;
  conditions?: string[] | null;
  interventions?: string[] | null;
  status?: string | null;
  study_type?: string | null;
  sponsors?: string[] | null;
  locations?: string[] | null;
  keywords?: string[] | null;
}

// Filter Types
export interface FiltersResponse {
  phases: Record<string, number>;
  statuses: Record<string, number>;
  study_types: Record<string, number>;
  top_conditions: Array<{ name: string; count: number }>;
  top_sponsors: Array<{ name: string; count: number }>;
}
