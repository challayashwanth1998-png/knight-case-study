"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { getSubmission, reviewSubmission } from "@/lib/api";
import type { SubmissionDetail, Tab } from "@/types";
import ProgressTracker from "@/components/submission/ProgressTracker";
import AICostCard from "@/components/submission/AICostCard";
import EmailTab from "@/components/submission/EmailTab";
import SummaryTab from "@/components/submission/SummaryTab";
import DocumentsTab from "@/components/submission/DocumentsTab";
import ExtractedDataTab from "@/components/submission/ExtractedDataTab";
import ConflictsTab from "@/components/submission/ConflictsTab";
import RulesTab from "@/components/submission/RulesTab";
import RecommendationsTab from "@/components/submission/RecommendationsTab";
import AuditTab from "@/components/submission/AuditTab";

const TABS: { key: Tab; label: string }[] = [
  { key: "summary", label: "Summary" },
  { key: "email", label: "Email" },
  { key: "documents", label: "Documents" },
  { key: "data", label: "Extracted Data" },
  { key: "conflicts", label: "Conflicts" },
  { key: "rules", label: "Rules" },
  { key: "recommendations", label: "Recommendations" },
  { key: "audit", label: "Audit Log" },
];

const TEAM_COLORS: Record<string, string> = {
  "Senior Underwriting": "#dc2626",
  "Specialty Risk": "#d97706",
  "Driver Review": "#7c3aed",
  "Operations": "#2563eb",
  "Standard Review": "#059669",
  "General Underwriting": "#6b7280",
};

export default function SubmissionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("summary");
  const [loading, setLoading] = useState(true);
  const [reviewNotes, setReviewNotes] = useState("");
  const [overrideDecision, setOverrideDecision] = useState("accept");
  const [reviewLoading, setReviewLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setSubmission(await getSubmission(id));
    } catch { /* silent */ }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [load]);

  const handleReview = async (action: "approve" | "reject" | "override") => {
    setReviewLoading(true);
    try {
      await reviewSubmission(id, {
        action,
        notes: reviewNotes,
        decision_override: action === "override" ? overrideDecision : undefined,
        reviewer_name: "Underwriter",
      });
      await load();
      setReviewNotes("");
    } catch (e) {
      console.error("Review failed:", e);
    }
    setReviewLoading(false);
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "50vh" }}>
        <div className="spinner" style={{ width: 28, height: 28 }} />
      </div>
    );
  }

  if (!submission) {
    return (
      <div style={{ padding: 32, textAlign: "center" }}>
        <div style={{ fontSize: 14, marginBottom: 12 }}>Submission not found</div>
        <button className="btn btn-secondary" onClick={() => router.push("/submissions")}>
          ← Back to Submissions
        </button>
      </div>
    );
  }

  const isProcessing = submission.status === "processing";
  const ruleStats = {
    pass: submission.rules.filter((r) => r.result === "PASS").length,
    fail: submission.rules.filter((r) => r.result === "FAIL").length,
    warning: submission.rules.filter((r) => r.result === "WARNING").length,
  };

  const tabCounts: Record<Tab, number | undefined> = {
    email: undefined,
    summary: undefined,
    documents: submission.documents.length,
    data: undefined,
    conflicts: submission.analysis?.conflicts?.length || 0,
    rules: submission.rules.length,
    recommendations: submission.analysis?.recommendations?.length || 0,
    audit: submission.audit_log.length,
  };

  const teamColor = TEAM_COLORS[submission.assigned_team || ""] || "#6b7280";
  const reviewBadge = submission.review_status ? ({
    approved: { bg: "#dcfce7", color: "#15803d", label: "✅ Approved" },
    rejected: { bg: "#fee2e2", color: "#b91c1c", label: "❌ Rejected" },
    overridden: { bg: "#fef3c7", color: "#92400e", label: "⚡ Overridden" },
    pending_review: { bg: "#e0e7ff", color: "#3730a3", label: "⏳ Pending Review" },
  } as Record<string, { bg: string; color: string; label: string }>)[submission.review_status] : null;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Header */}
      <div className="animate-fade-in" style={{ marginBottom: 16 }}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => router.push("/submissions")}
          style={{ marginBottom: 12 }}
        >
          ← Back
        </button>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20 }}>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>
              {submission.email_subject || `Submission ${id.slice(0, 8)}`}
            </h1>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <span className={`badge badge-${submission.status}`}>
                {isProcessing && <span className="spinner" style={{ width: 10, height: 10 }} />}
                {submission.status}
              </span>
              {submission.overall_decision && (
                <span className={`badge badge-${submission.overall_decision}`}>
                  {submission.overall_decision}
                </span>
              )}
              {submission.assigned_team && (
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: "2px 10px", borderRadius: 4,
                  background: `${teamColor}18`, color: teamColor, border: `1px solid ${teamColor}40`,
                }}>
                  📋 {submission.assigned_team}
                </span>
              )}
              {reviewBadge && (
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: "2px 10px", borderRadius: 4,
                  background: reviewBadge.bg, color: reviewBadge.color,
                }}>
                  {reviewBadge.label}
                </span>
              )}
              <span style={{ fontSize: 11, color: "var(--base)", fontFamily: "monospace" }}>
                {id.slice(0, 12)}
              </span>
              {submission.analysis?.confidence_score != null && (
                <span style={{
                  fontSize: 12, fontWeight: 700, color: "var(--primary)",
                  background: "var(--primary-lighter)", padding: "2px 8px",
                  borderRadius: 4,
                }}>
                  {Math.round(submission.analysis.confidence_score * 100)}% confidence
                </span>
              )}
            </div>
          </div>

          {/* AI Cost Card */}
          <div style={{ width: 300, flexShrink: 0 }}>
            <AICostCard
              inputTokens={submission.ai_input_tokens}
              outputTokens={submission.ai_output_tokens}
              costUsd={submission.ai_cost_usd}
              callsCount={submission.ai_calls_count}
              durationMs={submission.processing_duration_ms}
            />
          </div>
        </div>

        {/* Decision Banner */}
        {submission.decision_reason && (
          <div
            className={`usa-alert ${
              submission.overall_decision === "decline" ? "usa-alert-error" :
              submission.overall_decision === "refer" ? "usa-alert-warning" : "usa-alert-success"
            }`}
            style={{ marginTop: 12 }}
          >
            {submission.decision_reason}
          </div>
        )}

        {/* Underwriter Review Panel */}
        {submission.status === "complete" && submission.review_status === "pending_review" && (
          <div className="card" style={{
            marginTop: 12, padding: 16,
            border: "1px solid var(--primary)", background: "var(--primary-lighter)",
          }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, color: "var(--ink)" }}>
              🔍 Underwriter Review Required
            </div>
            <textarea
              placeholder="Review notes (optional)..."
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              rows={2}
              style={{
                width: "100%", padding: 8, borderRadius: 6, border: "1px solid var(--border)",
                fontSize: 13, marginBottom: 10, resize: "vertical", fontFamily: "inherit",
              }}
            />
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <button
                className="btn btn-sm"
                style={{ background: "#059669", color: "white", border: "none", cursor: "pointer" }}
                onClick={() => handleReview("approve")}
                disabled={reviewLoading}
              >
                ✅ Approve
              </button>
              <button
                className="btn btn-sm"
                style={{ background: "#dc2626", color: "white", border: "none", cursor: "pointer" }}
                onClick={() => handleReview("reject")}
                disabled={reviewLoading}
              >
                ❌ Reject
              </button>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <select
                  value={overrideDecision}
                  onChange={(e) => setOverrideDecision(e.target.value)}
                  style={{ padding: "4px 8px", borderRadius: 4, fontSize: 12, border: "1px solid var(--border)" }}
                >
                  <option value="accept">Accept</option>
                  <option value="refer">Refer</option>
                  <option value="decline">Decline</option>
                </select>
                <button
                  className="btn btn-sm"
                  style={{ background: "#d97706", color: "white", border: "none", cursor: "pointer" }}
                  onClick={() => handleReview("override")}
                  disabled={reviewLoading}
                >
                  ⚡ Override
                </button>
              </div>
              {reviewLoading && <span className="spinner" style={{ width: 14, height: 14 }} />}
            </div>
          </div>
        )}

        {/* Review Result */}
        {submission.reviewed_by && submission.review_status !== "pending_review" && (
          <div className="card" style={{ marginTop: 12, padding: 12, fontSize: 12 }}>
            <span style={{ fontWeight: 600 }}>
              Reviewed by {submission.reviewed_by}
            </span>
            {submission.reviewed_at && (
              <span style={{ color: "var(--base)", marginLeft: 8 }}>
                {new Date(submission.reviewed_at).toLocaleString()}
              </span>
            )}
            {submission.review_notes && (
              <div style={{ marginTop: 6, color: "var(--text2)", fontStyle: "italic" }}>
                &ldquo;{submission.review_notes}&rdquo;
              </div>
            )}
          </div>
        )}
      </div>

      {/* Progress Tracker */}
      <ProgressTracker auditLog={submission.audit_log} status={submission.status} />

      {/* Rule Summary */}
      {submission.rules.length > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {ruleStats.pass > 0 && <div className="badge badge-pass">{ruleStats.pass} Passed</div>}
          {ruleStats.fail > 0 && <div className="badge badge-fail">{ruleStats.fail} Failed</div>}
          {ruleStats.warning > 0 && <div className="badge badge-warning">{ruleStats.warning} Warnings</div>}
        </div>
      )}

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 20 }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab ${activeTab === t.key ? "active" : ""}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
            {tabCounts[t.key] != null && tabCounts[t.key]! > 0 && (
              <span
                style={{
                  marginLeft: 4, padding: "0 5px", borderRadius: 100, fontSize: 10,
                  background: activeTab === t.key ? "var(--primary)" : "var(--surface-alt)",
                  color: activeTab === t.key ? "white" : "var(--base)",
                }}
              >
                {tabCounts[t.key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in" key={activeTab}>
        {activeTab === "email" && <EmailTab submission={submission} />}
        {activeTab === "summary" && <SummaryTab analysis={submission.analysis} submission={submission} />}
        {activeTab === "documents" && <DocumentsTab submission={submission} />}
        {activeTab === "data" && <ExtractedDataTab analysis={submission.analysis} />}
        {activeTab === "conflicts" && <ConflictsTab conflicts={submission.analysis?.conflicts || []} />}
        {activeTab === "rules" && <RulesTab rules={submission.rules} />}
        {activeTab === "recommendations" && <RecommendationsTab recommendations={submission.analysis?.recommendations || []} />}
        {activeTab === "audit" && <AuditTab logs={submission.audit_log} />}
      </div>
    </div>
  );
}
