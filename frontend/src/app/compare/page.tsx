"use client";

import { useState, useEffect } from "react";
import { listSubmissions, getSubmission } from "@/lib/api";
import type { Submission, SubmissionDetail } from "@/types";

export default function ComparePage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [leftId, setLeftId] = useState<string>("");
  const [rightId, setRightId] = useState<string>("");
  const [leftDetail, setLeftDetail] = useState<SubmissionDetail | null>(null);
  const [rightDetail, setRightDetail] = useState<SubmissionDetail | null>(null);

  useEffect(() => {
    listSubmissions().then((subs) => {
      const complete = subs.filter(s => s.status === "complete");
      setSubmissions(complete);
      if (complete.length >= 2) {
        setLeftId(complete[0].id);
        setRightId(complete[1].id);
      }
    });
  }, []);

  useEffect(() => {
    if (leftId) getSubmission(leftId).then(setLeftDetail);
    if (rightId) getSubmission(rightId).then(setRightDetail);
  }, [leftId, rightId]);

  const completeSubs = submissions.filter(s => s.status === "complete");

  const compareMetric = (
    label: string,
    leftVal: string | number,
    rightVal: string | number,
    lowerIsBetter = false,
  ) => {
    const lNum = typeof leftVal === "number" ? leftVal : parseFloat(leftVal) || 0;
    const rNum = typeof rightVal === "number" ? rightVal : parseFloat(rightVal) || 0;
    const leftBetter = lowerIsBetter ? lNum < rNum : lNum > rNum;
    const rightBetter = lowerIsBetter ? rNum < lNum : rNum > lNum;

    return (
      <div style={{
        display: "grid", gridTemplateColumns: "1fr auto 1fr",
        gap: 12, padding: "10px 0", borderBottom: "1px solid #E2E8F0",
        alignItems: "center",
      }}>
        <div style={{
          textAlign: "right", fontWeight: 600, fontSize: 14,
          color: leftBetter ? "#059669" : "#1F2937",
        }}>
          {leftVal}
          {leftBetter && <span style={{ marginLeft: 6, fontSize: 10, color: "#059669" }}>✓</span>}
        </div>
        <div style={{
          fontSize: 11, color: "#94A3B8", fontWeight: 500,
          textTransform: "uppercase", letterSpacing: "0.5px",
          textAlign: "center", minWidth: 140,
        }}>
          {label}
        </div>
        <div style={{
          textAlign: "left", fontWeight: 600, fontSize: 14,
          color: rightBetter ? "#059669" : "#1F2937",
        }}>
          {rightVal}
          {rightBetter && <span style={{ marginLeft: 6, fontSize: 10, color: "#059669" }}>✓</span>}
        </div>
      </div>
    );
  };

  const getConflictCount = (d: SubmissionDetail) => {
    try {
      const conflicts = (d as any).conflicts || [];
      return Array.isArray(conflicts) ? conflicts.length : 0;
    } catch { return 0; }
  };

  const getRiskScore = (d: SubmissionDetail) => {
    try {
      return (d as any).risk_score || (d as any).ai_risk_score || "—";
    } catch { return "—"; }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>🔀 Compare Submissions</h1>
        <p className="page-subtitle">Side-by-side comparison of two processed submissions — metrics, rules, and risk analysis</p>
      </div>

      {/* Selector */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr auto 1fr",
        gap: 16, marginBottom: 24, alignItems: "center",
      }}>
        <select
          className="logs-select"
          style={{ width: "100%", padding: "10px 14px", fontSize: 13 }}
          value={leftId}
          onChange={(e) => setLeftId(e.target.value)}
        >
          <option value="">Select submission A</option>
          {completeSubs.map(s => (
            <option key={s.id} value={s.id}>
              {s.email_subject || `Sub. ${s.id.slice(0, 8)}`} — {s.overall_decision}
            </option>
          ))}
        </select>
        <span style={{ fontSize: 20, color: "#94A3B8" }}>⇔</span>
        <select
          className="logs-select"
          style={{ width: "100%", padding: "10px 14px", fontSize: 13 }}
          value={rightId}
          onChange={(e) => setRightId(e.target.value)}
        >
          <option value="">Select submission B</option>
          {completeSubs.map(s => (
            <option key={s.id} value={s.id}>
              {s.email_subject || `Sub. ${s.id.slice(0, 8)}`} — {s.overall_decision}
            </option>
          ))}
        </select>
      </div>

      {leftDetail && rightDetail && (
        <div>
          {/* Decision Header */}
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 1fr",
            gap: 16, marginBottom: 20,
          }}>
            {[leftDetail, rightDetail].map((d, i) => {
              const color = d.overall_decision === "accept" ? "#059669" :
                            d.overall_decision === "decline" ? "#DC2626" : "#D97706";
              return (
                <div key={i} style={{
                  padding: 16, background: `${color}08`, border: `1px solid ${color}30`,
                  borderRadius: 10, textAlign: "center",
                }}>
                  <div style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4 }}>
                    {d.documents?.length || 0} documents • {d.rules?.filter(r => r.result === "PASS").length || 0}/{d.rules?.length || 0} rules passed
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 800, color }}>
                    {d.overall_decision?.toUpperCase() || "PENDING"}
                  </div>
                  <div style={{ fontSize: 12, color: "#64748B", marginTop: 4 }}>
                    {(d as any).email_subject || `Submission ${d.id.slice(0, 8)}`}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Performance Metrics */}
          <div className="analytics-card" style={{ marginBottom: 16 }}>
            <h3>⚡ Performance Metrics</h3>
            {compareMetric(
              "Processing Time",
              `${((leftDetail.processing_duration_ms || 0) / 1000).toFixed(1)}s`,
              `${((rightDetail.processing_duration_ms || 0) / 1000).toFixed(1)}s`,
              true,
            )}
            {compareMetric(
              "AI Cost",
              `$${(leftDetail.ai_cost_usd || 0).toFixed(4)}`,
              `$${(rightDetail.ai_cost_usd || 0).toFixed(4)}`,
              true,
            )}
            {compareMetric(
              "AI Calls",
              leftDetail.ai_calls_count || 0,
              rightDetail.ai_calls_count || 0,
              true,
            )}
            {compareMetric(
              "Input Tokens",
              (leftDetail.ai_input_tokens || 0).toLocaleString(),
              (rightDetail.ai_input_tokens || 0).toLocaleString(),
              true,
            )}
            {compareMetric(
              "Output Tokens",
              (leftDetail.ai_output_tokens || 0).toLocaleString(),
              (rightDetail.ai_output_tokens || 0).toLocaleString(),
              true,
            )}
          </div>

          {/* Document Metrics */}
          <div className="analytics-card" style={{ marginBottom: 16 }}>
            <h3>📄 Document Metrics</h3>
            {compareMetric(
              "Total Documents",
              leftDetail.documents?.length || 0,
              rightDetail.documents?.length || 0,
            )}
            {compareMetric(
              "PDF Documents",
              leftDetail.documents?.filter(d => d.file_type === "pdf").length || 0,
              rightDetail.documents?.filter(d => d.file_type === "pdf").length || 0,
            )}
            {compareMetric(
              "Excel Documents",
              leftDetail.documents?.filter(d => d.file_type === "xlsx" || d.file_type === "xls").length || 0,
              rightDetail.documents?.filter(d => d.file_type === "xlsx" || d.file_type === "xls").length || 0,
            )}
            {compareMetric(
              "CDL Images",
              leftDetail.documents?.filter(d => d.file_type === "image").length || 0,
              rightDetail.documents?.filter(d => d.file_type === "image").length || 0,
            )}
            {compareMetric(
              "Conflicts Found",
              getConflictCount(leftDetail),
              getConflictCount(rightDetail),
              true,
            )}
          </div>

          {/* Rules Comparison */}
          <div className="analytics-card" style={{ marginBottom: 16 }}>
            <h3>⚖️ Rules Comparison</h3>
            {compareMetric(
              "Rules Passed",
              leftDetail.rules?.filter(r => r.result === "PASS").length || 0,
              rightDetail.rules?.filter(r => r.result === "PASS").length || 0,
            )}
            {compareMetric(
              "Rules Failed",
              leftDetail.rules?.filter(r => r.result === "FAIL").length || 0,
              rightDetail.rules?.filter(r => r.result === "FAIL").length || 0,
              true,
            )}
            {compareMetric(
              "Warnings",
              leftDetail.rules?.filter(r => r.result === "WARNING").length || 0,
              rightDetail.rules?.filter(r => r.result === "WARNING").length || 0,
              true,
            )}
            {compareMetric(
              "Info Items",
              leftDetail.rules?.filter(r => r.result === "INFO").length || 0,
              rightDetail.rules?.filter(r => r.result === "INFO").length || 0,
            )}
            {compareMetric(
              "Pass Rate",
              `${leftDetail.rules?.length
                ? Math.round((leftDetail.rules.filter(r => r.result === "PASS").length / leftDetail.rules.length) * 100)
                : 0}%`,
              `${rightDetail.rules?.length
                ? Math.round((rightDetail.rules.filter(r => r.result === "PASS").length / rightDetail.rules.length) * 100)
                : 0}%`,
            )}
          </div>

          {/* Rule-by-Rule Detail */}
          <div className="analytics-card">
            <h3>📋 Rule-by-Rule Comparison</h3>
            <div style={{ marginTop: 12 }}>
              {/* Header */}
              <div style={{
                display: "grid", gridTemplateColumns: "80px 1fr 80px 80px",
                gap: 8, padding: "8px 12px", background: "#F1F5F9", borderRadius: 6,
                fontSize: 10, fontWeight: 600, color: "#64748B", textTransform: "uppercase",
                letterSpacing: "0.5px",
              }}>
                <span>Rule ID</span>
                <span>Rule Name</span>
                <span style={{ textAlign: "center" }}>Left</span>
                <span style={{ textAlign: "center" }}>Right</span>
              </div>

              {/* Rows — combine rules from both submissions */}
              {(() => {
                const allRuleIds = new Set([
                  ...(leftDetail.rules || []).map(r => r.rule_id),
                  ...(rightDetail.rules || []).map(r => r.rule_id),
                ]);
                const ruleIds = Array.from(allRuleIds).sort();

                const resultColors: Record<string, string> = {
                  PASS: "#059669", FAIL: "#DC2626", WARNING: "#D97706", INFO: "#3B82F6",
                };
                const resultBg: Record<string, string> = {
                  PASS: "#F0FDF4", FAIL: "#FEF2F2", WARNING: "#FFFBEB", INFO: "#EFF6FF",
                };

                return ruleIds.map(ruleId => {
                  const leftRule = leftDetail.rules?.find(r => r.rule_id === ruleId);
                  const rightRule = rightDetail.rules?.find(r => r.rule_id === ruleId);
                  const differ = leftRule?.result !== rightRule?.result;

                  return (
                    <div key={ruleId} style={{
                      display: "grid", gridTemplateColumns: "80px 1fr 80px 80px",
                      gap: 8, padding: "8px 12px", borderBottom: "1px solid #F1F5F9",
                      alignItems: "center",
                      background: differ ? "#FFFBEB08" : "transparent",
                    }}>
                      <span style={{ fontSize: 10, fontWeight: 600, fontFamily: "monospace", color: "#475569" }}>{ruleId}</span>
                      <span style={{ fontSize: 11, color: "#64748B" }}>{leftRule?.rule_name || rightRule?.rule_name || "—"}</span>
                      {[leftRule, rightRule].map((r, idx) => (
                        <span key={idx} style={{
                          textAlign: "center", fontSize: 10, fontWeight: 600, padding: "3px 8px",
                          borderRadius: 4,
                          background: r ? resultBg[r.result] || "#F1F5F9" : "#F1F5F9",
                          color: r ? resultColors[r.result] || "#64748B" : "#94A3B8",
                        }}>
                          {r?.result || "N/A"}
                        </span>
                      ))}
                    </div>
                  );
                });
              })()}
            </div>
          </div>

          {/* Failed rules detail */}
          <div className="analytics-card" style={{ marginTop: 16 }}>
            <h3>❌ Failed Rules Detail</h3>
            <div style={{
              display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 12,
            }}>
              {[leftDetail, rightDetail].map((d, i) => {
                const failures = d.rules?.filter(r => r.result === "FAIL") || [];
                const warnings = d.rules?.filter(r => r.result === "WARNING") || [];
                return (
                  <div key={i}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#DC2626", marginBottom: 8 }}>
                      Failed ({failures.length}) • Warnings ({warnings.length})
                    </div>
                    {failures.length > 0 ? failures.map(r => (
                      <div key={r.id} style={{
                        fontSize: 11, padding: "6px 8px", marginBottom: 4,
                        background: "#FEF2F2", borderRadius: 4, borderLeft: "3px solid #DC2626",
                      }}>
                        <strong>{r.rule_id}</strong>: {r.details?.slice(0, 80) || r.rule_name}
                      </div>
                    )) : (
                      <div style={{ fontSize: 11, color: "#059669" }}>✅ No failures</div>
                    )}
                    {warnings.length > 0 && warnings.map(r => (
                      <div key={r.id} style={{
                        fontSize: 11, padding: "6px 8px", marginBottom: 4, marginTop: 4,
                        background: "#FFFBEB", borderRadius: 4, borderLeft: "3px solid #D97706",
                      }}>
                        <strong>{r.rule_id}</strong>: {r.details?.slice(0, 80) || r.rule_name}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {completeSubs.length < 2 && (
        <div className="analytics-card" style={{ textAlign: "center", padding: 40 }}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>📊</div>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>Need at least 2 completed submissions</div>
          <div style={{ fontSize: 12, color: "#94A3B8" }}>Process more submissions to enable comparison</div>
        </div>
      )}
    </div>
  );
}
