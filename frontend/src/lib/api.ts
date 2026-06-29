/**
 * API Client — all backend communication.
 */
import type {
  Submission, SubmissionDetail, DashboardStats, RuleDefinition,
} from "@/types";

const API_BASE = typeof window !== "undefined"
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const uploadSubmission = (files: File[]): Promise<Submission> => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return api("/api/submissions/upload", { method: "POST", body: form });
};

export const processSubmission = (id: string) =>
  api<{ status: string }>(`/api/submissions/${id}/process`, { method: "POST" });

export const listSubmissions = () =>
  api<Submission[]>("/api/submissions");

export const getSubmission = (id: string) =>
  api<SubmissionDetail>(`/api/submissions/${id}`);

export const getStats = () =>
  api<DashboardStats>("/api/submissions/stats");

export const deleteSubmission = (id: string) =>
  api<void>(`/api/submissions/${id}`, { method: "DELETE" });

export const getDocumentDownloadUrl = (submissionId: string, documentId: string) =>
  `${API_BASE}/api/submissions/${submissionId}/documents/${documentId}/download`;

export const getRulesReference = () =>
  api<RuleDefinition[]>("/api/submissions/meta/rules");

export interface RuleConfig extends RuleDefinition {
  enabled: boolean;
  severity_override: string | null;
  original_severity: string;
}

export const getRulesConfig = () =>
  api<RuleConfig[]>("/api/submissions/meta/rules-config");

export const updateRuleConfig = (ruleId: string, body: { enabled?: boolean; severity?: string }) =>
  api<{ rule_id: string }>(`/api/submissions/meta/rules-config/${ruleId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const resetRulesConfig = () =>
  api<{ status: string }>("/api/submissions/meta/rules-config/reset", { method: "POST" });

export const getAnalytics = () =>
  api<any>("/api/submissions/analytics");

export const getLogs = (limit = 200) =>
  api<any[]>(`/api/submissions/logs?limit=${limit}`);

export const getHealth = () =>
  api<any>("/api/submissions/health");

export const reviewSubmission = (id: string, body: {
  action: "approve" | "reject" | "override";
  notes?: string;
  decision_override?: string;
  reviewer_name?: string;
}) =>
  api<{ status: string; review_status: string; overall_decision: string; message: string }>(
    `/api/submissions/${id}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
