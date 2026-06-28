"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { listSubmissions, deleteSubmission } from "@/lib/api";
import type { Submission } from "@/types";

const PIPELINE_STEPS = [
  { key: "extract", label: "Extract", icon: "📄" },
  { key: "classify", label: "Classify", icon: "🏷️" },
  { key: "data", label: "Data", icon: "🔍" },
  { key: "analyze", label: "Analyze", icon: "🤖" },
  { key: "rules", label: "Rules", icon: "⚖️" },
  { key: "decision", label: "Decision", icon: "✅" },
];

function getPipelineProgress(sub: Submission): number {
  // If complete or error, it's done
  if (sub.status === "complete" || sub.status === "error") return 6;
  if (sub.status === "received") return 0;
  // Estimate based on processing duration — rough heuristic
  if (sub.processing_duration_ms) {
    const seconds = sub.processing_duration_ms / 1000;
    if (seconds > 30) return 5;
    if (seconds > 20) return 4;
    if (seconds > 12) return 3;
    if (seconds > 6) return 2;
    return 1;
  }
  return 1; // At least started
}

function getStatusColor(status: string): string {
  switch (status) {
    case "complete": return "var(--success)";
    case "processing": return "var(--primary)";
    case "error": return "var(--error)";
    default: return "var(--base)";
  }
}

function getDecisionStyle(decision: string | null) {
  switch (decision) {
    case "accept": return { bg: "var(--success-light)", color: "var(--success)", label: "ACCEPTED" };
    case "decline": return { bg: "var(--error-light)", color: "var(--error)", label: "DECLINED" };
    case "refer": return { bg: "var(--warning-light)", color: "var(--warning-dark)", label: "REFERRED" };
    default: return null;
  }
}

export default function UnderwriterViewPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const router = useRouter();

  const loadData = useCallback(async () => {
    try {
      setSubmissions(await listSubmissions());
    } catch { /* backend might be down */ }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000); // Faster polling to see progress
    return () => clearInterval(interval);
  }, [loadData]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this submission?")) return;
    await deleteSubmission(id);
    loadData();
  };

  const filtered = submissions.filter((s) => {
    if (filter === "all") return true;
    if (filter === "processing") return s.status === "processing";
    if (filter === "complete") return s.status === "complete";
    if (filter === "accepted") return s.overall_decision === "accept";
    if (filter === "declined") return s.overall_decision === "decline";
    if (filter === "referred") return s.overall_decision === "refer";
    return true;
  });

  const counts = {
    all: submissions.length,
    processing: submissions.filter(s => s.status === "processing").length,
    complete: submissions.filter(s => s.status === "complete").length,
    accepted: submissions.filter(s => s.overall_decision === "accept").length,
    declined: submissions.filter(s => s.overall_decision === "decline").length,
    referred: submissions.filter(s => s.overall_decision === "refer").length,
  };

  const filters = [
    { key: "all", label: "All" },
    { key: "processing", label: "Processing" },
    { key: "complete", label: "Complete" },
    { key: "accepted", label: "Accepted" },
    { key: "declined", label: "Declined" },
    { key: "referred", label: "Referred" },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">Underwriter View</h1>
          <p className="page-description">All submissions with real-time AI pipeline progress tracking.</p>
        </div>
        <Link href="/submit" className="btn btn-primary">
          + New Submission
        </Link>
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ marginBottom: 16, padding: 12, display: "flex", gap: 6, flexWrap: "wrap" }}>
        {filters.map((f) => (
          <button
            key={f.key}
            className={`btn btn-sm ${filter === f.key ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setFilter(f.key)}
            style={{ fontSize: 12 }}
          >
            {f.label}
            <span style={{
              marginLeft: 4, padding: "1px 6px", borderRadius: 10,
              background: filter === f.key ? "rgba(255,255,255,0.2)" : "var(--surface-alt)",
              fontSize: 11,
            }}>
              {counts[f.key as keyof typeof counts]}
            </span>
          </button>
        ))}
      </div>

      {/* Submissions */}
      {filtered.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48, color: "var(--base)" }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📋</div>
          <div style={{ fontSize: 15, fontWeight: 600 }}>No submissions found</div>
          <div style={{ fontSize: 13, marginTop: 4 }}>
            {filter !== "all" ? "Try a different filter" : "Upload documents to begin"}
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {filtered.map((sub) => {
            const progress = getPipelineProgress(sub);
            const decision = getDecisionStyle(sub.overall_decision);

            return (
              <div
                key={sub.id}
                className="card card-clickable"
                style={{ padding: 0, overflow: "hidden" }}
                onClick={() => router.push(`/submissions/${sub.id}`)}
              >
                {/* Top section */}
                <div style={{ padding: "16px 20px 12px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)" }}>
                        {sub.email_subject || `Submission ${sub.id.slice(0, 8)}`}
                      </span>
                      <span className={`badge badge-${sub.status}`}>
                        {sub.status === "processing" && (
                          <span className="spinner" style={{ width: 10, height: 10 }} />
                        )}
                        {sub.status}
                      </span>
                      {decision && (
                        <span style={{
                          fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 4,
                          background: decision.bg, color: decision.color,
                        }}>
                          {decision.label}
                        </span>
                      )}
                    </div>
                    <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--base)" }}>
                      <span>📂 {sub.document_count || 0} docs</span>
                      <span>🕒 {new Date(sub.created_at).toLocaleString("en-US", {
                        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                      })}</span>
                      {sub.ai_cost_usd > 0 && (
                        <span>💰 ${sub.ai_cost_usd.toFixed(4)}</span>
                      )}
                      {sub.processing_duration_ms && sub.processing_duration_ms > 0 && (
                        <span>⏱️ {(sub.processing_duration_ms / 1000).toFixed(1)}s</span>
                      )}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={(e) => handleDelete(sub.id, e)}
                      style={{ padding: "4px 10px", fontSize: 11 }}
                    >
                      ✕
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ padding: "4px 10px", fontSize: 11 }}
                    >
                      View →
                    </button>
                  </div>
                </div>

                {/* Pipeline Progress Bar */}
                <div style={{
                  padding: "8px 20px 14px",
                  borderTop: "1px solid var(--border-light)",
                  background: sub.status === "processing" ? "var(--surface-alt)" : "transparent",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
                    {PIPELINE_STEPS.map((step, i) => {
                      const isDone = i < progress;
                      const isCurrent = i === progress && sub.status === "processing";
                      const isPending = i > progress;

                      return (
                        <div key={step.key} style={{ flex: 1, display: "flex", alignItems: "center" }}>
                          {/* Step dot */}
                          <div style={{
                            display: "flex", flexDirection: "column", alignItems: "center",
                            position: "relative", zIndex: 1,
                          }}>
                            <div style={{
                              width: 28, height: 28, borderRadius: "50%",
                              display: "flex", alignItems: "center", justifyContent: "center",
                              fontSize: 13,
                              background: isDone ? "var(--success)" :
                                         isCurrent ? "var(--primary)" :
                                         "var(--border)",
                              color: isDone || isCurrent ? "white" : "var(--base)",
                              fontWeight: 600,
                              transition: "all 0.3s ease",
                              boxShadow: isCurrent ? "0 0 0 3px var(--primary-lighter)" : "none",
                              animation: isCurrent ? "pulse 1.5s ease-in-out infinite" : "none",
                            }}>
                              {isDone ? "✓" : step.icon}
                            </div>
                            <div style={{
                              fontSize: 9, fontWeight: 500, marginTop: 3,
                              color: isDone ? "var(--success)" :
                                     isCurrent ? "var(--primary)" :
                                     "var(--base)",
                            }}>
                              {step.label}
                            </div>
                          </div>
                          {/* Connector line */}
                          {i < PIPELINE_STEPS.length - 1 && (
                            <div style={{
                              flex: 1, height: 3, marginTop: -14,
                              background: isDone ? "var(--success)" : "var(--border)",
                              borderRadius: 2,
                              transition: "all 0.3s ease",
                            }} />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Decision reason preview */}
                {sub.decision_reason && (
                  <div style={{
                    padding: "8px 20px 12px",
                    borderTop: "1px solid var(--border-light)",
                    fontSize: 12, color: "var(--base)",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  }}>
                    💡 {sub.decision_reason}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
