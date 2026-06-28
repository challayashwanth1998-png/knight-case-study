"use client";

import { useState, useEffect } from "react";
import { getLogs } from "@/lib/api";
import Link from "next/link";

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

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    getLogs(500).then(setLogs).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (filter !== "all" && log.action !== filter) return false;
    if (searchTerm && !JSON.stringify(log).toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const actionTypes = [...new Set(logs.map((l) => l.action))].sort();

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📋 System Logs</h1>
        <p className="page-subtitle">Audit trail and pipeline processing history</p>
      </div>

      {/* Filters */}
      <div className="logs-filters">
        <input
          type="text"
          className="logs-search"
          placeholder="Search logs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          className="logs-select"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All Actions ({logs.length})</option>
          {actionTypes.map((a) => (
            <option key={a} value={a}>
              {ACTION_ICONS[a] || "📌"} {a.replace(/_/g, " ")} ({logs.filter((l) => l.action === a).length})
            </option>
          ))}
        </select>
        <span className="logs-count">{filteredLogs.length} entries</span>
      </div>

      {/* Log Entries */}
      <div className="logs-list">
        {filteredLogs.map((log) => (
          <div key={log.id} className="log-entry">
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
                  <span className="log-step">Step {log.step_number}</span>
                )}
                {log.duration_ms && (
                  <span className="log-duration">{(log.duration_ms / 1000).toFixed(1)}s</span>
                )}
              </div>
              <div className="log-details">{log.details}</div>
              <div className="log-meta">
                <Link href={`/submissions/${log.submission_id}`} className="log-submission-link">
                  {log.submission_name}
                </Link>
                <span className="log-time">
                  {log.timestamp ? new Date(log.timestamp).toLocaleString() : "—"}
                </span>
              </div>
            </div>
          </div>
        ))}
        {filteredLogs.length === 0 && (
          <div className="logs-empty">No log entries found matching your filters.</div>
        )}
      </div>
    </div>
  );
}
