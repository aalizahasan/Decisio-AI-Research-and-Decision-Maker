export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  version: string;
}

export interface UserProfile {
  id: number;
  email: string;
  full_name?: string;
  auth_provider: string;
  created_at: string;
}

export interface AuthResponse {
  status: string;
  message: string;
  access_token: str;
  user: UserProfile;
}

export interface FeatureItem {
  id: string;
  title: string;
  description: string;
  status: 'planned' | 'upcoming';
  tag: string;
}

export interface SourceReference {
  document_id: number;
  filename: string;
  page_number?: number;
  chunk_index?: number;
}

export interface DocumentItem {
  id: number;
  filename: string;
  file_type: string;
  created_at: string;
  chunks_count: number;
}

export interface MatrixCriterion {
  name: string;
  weight: number;
}

export interface OptionRanking {
  option: string;
  score: number;
  rank: number;
}

export interface DecisionMatrixData {
  options: string[];
  criteria: MatrixCriterion[];
  scores: Record<string, Record<string, number>>;
  rankings: OptionRanking[];
}

export interface DecisionInput {
  problem: string;
  context: string;
  constraints: string;
  document_id?: number;
  response_preference?: 'auto' | 'concise' | 'detailed';
}

export interface AnalysisResponse {
  status: string;
  message: string;
  analysis_id?: number;
  problem: string;
  context: string;
  constraints: string;
  analysis?: string;
  request_type?: string;
  response_depth?: string;
  multi_agent_used?: boolean;
  agents_metadata?: Record<string, any>[];
  sources?: SourceReference[];
  matrix?: DecisionMatrixData | null;
}

export interface AnalysisHistoryItem {
  id: number;
  problem: string;
  request_type: string;
  response_depth: string;
  multi_agent_used?: boolean;
  created_at: string;
}

export interface AnalysisDetail {
  id: number;
  problem: string;
  context: string;
  constraints: string;
  analysis: string;
  request_type: string;
  response_depth: string;
  multi_agent_used?: boolean;
  agents_metadata?: Record<string, any>[];
  sources?: SourceReference[];
  matrix?: DecisionMatrixData | null;
  created_at: string;
}
