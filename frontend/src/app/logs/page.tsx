"use client";

import { useState, useEffect, useMemo } from "react";
import { getLogs, listSubmissions } from "@/lib/api";
import Link from "next/link";
import type { Submission } from "@/types";

const ACTION_ICONS: Record<string, string> = {
  submission_created: "📤",
  pipeline_started: "▶️",
  text_extraction: "📝",
  classification: "🏷️",
  data_extraction: "🔍",
  ai_analysis: "🧠",
  rules_evaluation: "📏",
  decision_made: "✅",
  pipeline_completed: "🏁",
  pipeline_error: "❌",
};

const ACTION_COLORS: Record<string, string> = {
  submission_created: "#2563EB",
  pipeline_started: "#2563EB",
  pipeline_completed: "#059669",
  pipeline_error: "#DC2626",
  decision_made: "#059669",
  text_extraction: "#0D9488",
  classification: "#7C3AED",
  data_extraction: "#D97706",
  ai_analysis: "#4F46E5",
  rules_evaluation: "#D97706",
};

const ACTION_DESCRIPTIONS: Record<string, string> = {
  submission_created: "New submission uploaded with documents",
  pipeline_started: "AI processing pipeline initiated",
  text_extraction: "Extracting text from PDFs and parsing Excel/CSV files",
  classification: "Classifying documents using Gemini AI (batched)",
  data_extraction: "Extracting structured data from classified documents",
  ai_analysis: "Running 4 parallel AI risk analyses (company, driver, fleet, financial)",
  rules_evaluation: "Evaluating 21 business rules against extracted data",
  decision_made: "Final underwriting decision rendered",
  pipeline_completed: "Full pipeline processing completed successfully",
  pipeline_error: "Pipeline encountered an error during processing",
};

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [subs, setSubs] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState("all");
  const [subFilter, setSubFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    Promise.all([
      getLogs(500),
      listSubmissions(),
    ]).then(([logsData, subsData]) => {
      setLogs(logsData);
      setSubs(subsData);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      // Action filter
      if (actionFilter !== "all" && log.action !== actionFilter) return false;
      // Submission filter
      if (subFilter !== "all" && log.submission_id !== subFilter) return false;
      // Date filter
      if (dateFilter !== "all" && log.timestamp) {
        const logDate = new Date(log.timestamp);
        const now = new Date();
        if (dateFilter === "today") {
          const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          if (logDate < today) return false;
        } else if (dateFilter === "7days") {
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          if (logDate < weekAgo) return false;
        } else if (dateFilter === "24h") {
          const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
          if (logDate < dayAgo) return false;
        }
      }
      // Search
      if (searchTerm && !JSON.stringify(log).toLowerCase().includes(searchTerm.toLowerCase())) return false;
      return true;
    });
  }, [logs, actionFilter, subFilter, dateFilter, searchTerm]);

  const actionTypes = [...new Set(logs.map((l) => l.action))].sort();

  // Unique submissions in logs
  const logSubmissions = useMemo(() => {
    const map = new Map<string, string>();
    logs.forEach(l => {
      if (l.submission_id && !map.has(l.submission_id)) {
        map.set(l.submission_id, l.submission_name || `Sub ${l.submission_id.slice(0, 8)}`);
      }
    });
    return Array.from(map.entries());
  }, [logs]);

  // Stats
  const errorCount = logs.filter(l => l.action === "pipeline_error").length;
  const avgDuration = (() => {
    const durations = logs.filter(l => l.duration_ms).map(l => l.duration_ms);
    return durations.length ? (durations.reduce((a: number, b: number) => a + b, 0) / durations.length / 1000).toFixed(1) : "—";
  })();

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📋 System Logs</h1>
        <p className="page-subtitle">Audit trail and pipeline processing history — {logs.length} total entries</p>
      </div>

      {/* Stats Bar */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20,
      }}>
        <div style={{
          padding: "12px 16px", borderRadius: 10, background: "#F0F9FF", border: "1px solid #BAE6FD",
        }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#0369A1" }}>{logs.length}</div>
          <div style={{ fontSize: 11, color: "#0284C7" }}>Total Events</div>
        </div>
        <div style={{
          padding: "12px 16px", borderRadius: 10, background: "#F0FDF4", border: "1px solid #BBF7D0",
        }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#15803D" }}>{logSubmissions.length}</div>
          <div style={{ fontSize: 11, color: "#16A34A" }}>Submissions</div>
        </div>
        <div style={{
          padding: "12px 16px", borderRadius: 10, background: "#FEF2F2", border: "1px solid #FECACA",
        }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#B91C1C" }}>{errorCount}</div>
          <div style={{ fontSize: 11, color: "#DC2626" }}>Errors</div>
        </div>
        <div style={{
          padding: "12px 16px", borderRadius: 10, background: "#FFFBEB", border: "1px solid #FDE68A",
        }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#B45309" }}>{avgDuration}s</div>
          <div style={{ fontSize: 11, color: "#D97706" }}>Avg Step Duration</div>
        </div>
      </div>

      {/* Filters */}
      <div className="logs-filters" style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
        <input
          type="text"
          className="logs-search"
          placeholder="Search logs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ flex: 1, minWidth: 200 }}
        />
        <select
          className="logs-select"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
        >
          <option value="all">All Actions ({logs.length})</option>
          {actionTypes.map((a) => (
            <option key={a} value={a}>
              {ACTION_ICONS[a] || "📌"} {a.replace(/_/g, " ")} ({logs.filter((l) => l.action === a).length})
            </option>
          ))}
        </select>
        <select
          className="logs-select"
          value={subFilter}
          onChange={(e) => setSubFilter(e.target.value)}
        >
          <option value="all">All Submissions</option>
          {logSubmissions.map(([id, name]) => (
            <option key={id} value={id}>
              {name} ({logs.filter(l => l.submission_id === id).length} events)
            </option>
          ))}
        </select>
        <select
          className="logs-select"
          value={dateFilter}
          onChange={(e) => setDateFilter(e.target.value)}
        >
          <option value="all">All Time</option>
          <option value="24h">Last 24 Hours</option>
          <option value="today">Today</option>
          <option value="7days">Last 7 Days</option>
        </select>
        <span className="logs-count" style={{
          display: "flex", alignItems: "center", padding: "0 12px",
          fontSize: 12, fontWeight: 600, color: "#64748B",
        }}>
          {filteredLogs.length} entries
        </span>
      </div>

      {/* Log Entries */}
      <div className="logs-list">
        {filteredLogs.map((log, idx) => {
          // Check if this is a new submission group
          const prevLog = idx > 0 ? filteredLogs[idx - 1] : null;
          const isNewGroup = !prevLog || prevLog.submission_id !== log.submission_id;

          return (
            <div key={log.id}>
              {isNewGroup && subFilter === "all" && (
                <div style={{
                  padding: "8px 14px", marginTop: idx > 0 ? 12 : 0, marginBottom: 4,
                  background: "#F8FAFC", borderRadius: 8, border: "1px solid #E2E8F0",
                  fontSize: 11, fontWeight: 600, color: "#475569",
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}>
                  <span>📦 {log.submission_name || `Submission ${log.submission_id?.slice(0, 8)}`}</span>
                  <Link
                    href={`/submissions/${log.submission_id}`}
                    style={{ fontSize: 10, color: "#3B82F6", textDecoration: "none" }}
                  >
                    View →
                  </Link>
                </div>
              )}
              <div className="log-entry">
                <div
                  className="log-icon"
                  style={{ background: `${ACTION_COLORS[log.action] || "#64748B"}20`, color: ACTION_COLORS[log.action] || "#64748B" }}
                >
                  {ACTION_ICONS[log.action] || "📌"}
                </div>
                <div className="log-content">
                  <div className="log-action">
                    {log.action.replace(/_/g, " ")}
                    {log.step_number > 0 && (
                      <span className="log-step">Step {log.step_number}/6</span>
                    )}
                    {log.duration_ms && (
                      <span className="log-duration">{(log.duration_ms / 1000).toFixed(1)}s</span>
                    )}
                  </div>
                  <div className="log-details">
                    {log.details || ACTION_DESCRIPTIONS[log.action] || "—"}
                  </div>
                  <div className="log-meta">
                    {subFilter !== "all" ? null : (
                      <Link href={`/submissions/${log.submission_id}`} className="log-submission-link">
                        {log.submission_name}
                      </Link>
                    )}
                    <span className="log-time">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : "—"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        {filteredLogs.length === 0 && (
          <div className="logs-empty">No log entries found matching your filters.</div>
        )}
      </div>
    </div>
  );
}
