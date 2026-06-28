/**
 * Shared TypeScript types for the Knight Insurance frontend.
 */

export interface Submission {
  id: string;
  email_from: string | null;
  email_subject: string | null;
  email_body: string | null;
  status: string;
  overall_decision: string | null;
  decision_reason: string | null;
  received_at: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string | null;
  document_count: number | null;
  // AI Metrics
  ai_input_tokens: number;
  ai_output_tokens: number;
  ai_cost_usd: number;
  ai_calls_count: number;
  processing_duration_ms: number | null;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number | null;
  classified_type: string | null;
  classification_confidence: number | null;
  quality_score: number | null;
  processing_status: string;
  extracted_data: Record<string, unknown> | null;
  created_at: string;
}

export interface RuleResult {
  id: string;
  rule_id: string;
  rule_name: string;
  category: string;
  result: string;
  severity: string;
  details: string | null;
  data_used: Record<string, unknown> | null;
}

export interface AnalysisResult {
  id: string;
  summary: string | null;
  business_profile: Record<string, unknown> | null;
  completeness_report: Record<string, unknown> | null;
  conflicts: Array<Record<string, unknown>> | null;
  risk_assessment: Record<string, unknown> | null;
  recommendations: Array<Record<string, unknown>> | null;
  confidence_score: number | null;
  unified_business_info: Record<string, unknown> | null;
  unified_drivers: Array<Record<string, unknown>> | null;
  unified_vehicles: Array<Record<string, unknown>> | null;
  unified_ifta: Array<Record<string, unknown>> | null;
  created_at: string;
}

export interface AuditLog {
  id: string;
  action: string;
  details: string | null;
  step_number: number | null;
  timestamp: string;
}

export interface SubmissionDetail extends Submission {
  documents: Document[];
  analysis: AnalysisResult | null;
  rules: RuleResult[];
  audit_log: AuditLog[];
}

export interface DashboardStats {
  total_submissions: number;
  pending: number;
  processing: number;
  complete: number;
  accepted: number;
  declined: number;
  referred: number;
}

export interface RuleDefinition {
  rule_id: string;
  rule_name: string;
  category: string;
  severity: string;
  description: string;
}

export type Tab =
  | "email"
  | "summary"
  | "documents"
  | "data"
  | "conflicts"
  | "rules"
  | "recommendations"
  | "audit";
