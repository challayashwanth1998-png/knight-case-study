"use client";

import type { AnalysisResult, SubmissionDetail } from "@/types";

interface Props {
  analysis: AnalysisResult | null;
  submission: SubmissionDetail;
}

export default function SummaryTab({ analysis }: Props) {
  const completeness = analysis?.completeness_report as Record<string, unknown> | null;
  const risk = analysis?.risk_assessment as Record<string, unknown> | null;

  if (!analysis) {
    return (
      <div className="card" style={{ textAlign: "center", padding: 32, color: "var(--base)" }}>
        <div style={{ fontSize: 24, marginBottom: 8 }}>🔄</div>
        <div style={{ fontSize: 14, fontWeight: 500 }}>Analysis not yet available</div>
        <div style={{ fontSize: 12, marginTop: 4 }}>Processing may still be in progress.</div>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      {/* AI Summary */}
      {analysis.summary && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: "var(--ink)" }}>
            🤖 AI Summary
          </h3>
          <div className="prose" style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.7, color: "var(--text2)" }}>
            {analysis.summary}
          </div>
        </div>
      )}

      {/* Submission Completeness */}
      {completeness !== null && completeness !== undefined && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "var(--ink)" }}>
            📋 Submission Completeness
          </h3>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
            <div className="progress-bar" style={{ flex: 1, height: 10 }}>
              <div
                className="progress-fill"
                style={{
                  width: `${(completeness.completeness_percentage as number) || 0}%`,
                  background: (completeness.completeness_percentage as number) >= 80 ? "var(--success)" :
                             (completeness.completeness_percentage as number) >= 50 ? "var(--warning)" : "var(--error)",
                }}
              />
            </div>
            <span style={{ fontWeight: 700, fontSize: 16, minWidth: 48, textAlign: "right" }}>
              {(completeness.completeness_percentage as number)?.toFixed(0) || 0}%
            </span>
          </div>

          {((completeness.received_documents as string[]) || []).length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--success)", marginBottom: 6 }}>
                ✅ Received Documents
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {(completeness.received_documents as string[]).map((item, i) => (
                  <span key={i} style={{
                    fontSize: 11, padding: "3px 10px", borderRadius: 4,
                    background: "var(--success-light)", color: "var(--success)", fontWeight: 500,
                  }}>
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {((completeness.missing_required as string[]) || []).length > 0 && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--error)", marginBottom: 6 }}>
                ❌ Missing Required Items
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {(completeness.missing_required as string[]).map((item, i) => (
                  <span key={i} style={{
                    fontSize: 11, padding: "3px 10px", borderRadius: 4,
                    background: "var(--error-light)", color: "var(--error)", fontWeight: 500,
                  }}>
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Risk Assessment */}
      {risk !== null && risk !== undefined && (risk as Record<string, unknown>).overall_score !== undefined && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "var(--ink)" }}>
            ⚠️ Risk Assessment
          </h3>
          <div style={{ display: "flex", gap: 20, marginBottom: 16, alignItems: "center" }}>
            <div style={{
              width: 64, height: 64, borderRadius: 12,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              background: (risk.overall_score as number) > 7 ? "var(--error-light)" :
                         (risk.overall_score as number) > 4 ? "var(--warning-light)" : "var(--success-light)",
            }}>
              <span style={{
                fontSize: 24, fontWeight: 800,
                color: (risk.overall_score as number) > 7 ? "var(--error)" :
                       (risk.overall_score as number) > 4 ? "var(--warning-dark)" : "var(--success)",
              }}>
                {risk.overall_score as number}
              </span>
              <span style={{ fontSize: 9, color: "var(--base)", fontWeight: 600 }}>/10</span>
            </div>
            <div>
              <span className={`badge badge-${
                (risk.risk_tier as string)?.toLowerCase() === "low" ? "pass" :
                (risk.risk_tier as string)?.toLowerCase() === "medium" ? "warning" : "fail"
              }`} style={{ fontSize: 13, padding: "4px 12px" }}>
                {(risk.risk_tier as string)?.toUpperCase()} RISK
              </span>
            </div>
          </div>
          {(risk.factors as Array<Record<string, unknown>>)?.map((f, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 12,
              padding: "10px 0", borderBottom: "1px solid var(--border-light)",
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: 6,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontWeight: 700, fontSize: 13,
                background: (f.score as number) > 7 ? "var(--error-light)" :
                           (f.score as number) > 4 ? "var(--warning-light)" : "var(--success-light)",
                color: (f.score as number) > 7 ? "var(--error)" :
                       (f.score as number) > 4 ? "var(--warning-dark)" : "var(--success)",
              }}>
                {f.score as number}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{f.factor as string}</div>
                <div style={{ fontSize: 12, color: "var(--base)", marginTop: 2 }}>{f.reasoning as string}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
