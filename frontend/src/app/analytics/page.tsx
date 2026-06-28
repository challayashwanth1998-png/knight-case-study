"use client";

import { useState, useEffect } from "react";
import { getAnalytics } from "@/lib/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalytics().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;
  if (!data) return <div className="page-container"><p>No analytics data available.</p></div>;

  const { summary, decisions, rule_stats, timeline, document_types } = data;

  const decisionColors: Record<string, string> = {
    accept: "#059669", decline: "#DC2626", refer: "#D97706",
  };

  const maxTime = Math.max(...(timeline || []).map((t: any) => t.time_seconds || 0), 1);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📈 Analytics Dashboard</h1>
        <p className="page-subtitle">AI pipeline performance metrics and submission insights</p>
      </div>

      {/* KPI Cards */}
      <div className="analytics-kpis">
        <div className="kpi-card">
          <div className="kpi-value">{summary.total_submissions}</div>
          <div className="kpi-label">Total Processed</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{summary.avg_processing_time}s</div>
          <div className="kpi-label">Avg Processing Time</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">${summary.total_ai_cost.toFixed(3)}</div>
          <div className="kpi-label">Total AI Cost</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">${summary.avg_ai_cost.toFixed(4)}</div>
          <div className="kpi-label">Avg Cost / Submission</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{summary.total_ai_calls}</div>
          <div className="kpi-label">Total AI Calls</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{((summary.total_input_tokens + summary.total_output_tokens) / 1000).toFixed(1)}K</div>
          <div className="kpi-label">Total Tokens</div>
        </div>
      </div>

      {/* Decision Breakdown + Document Types */}
      <div className="analytics-row">
        <div className="analytics-card">
          <h3>Decision Breakdown</h3>
          <div className="decision-bars">
            {Object.entries(decisions).map(([key, count]) => {
              const total = Object.values(decisions).reduce((a: number, b: any) => a + (b as number), 0) as number;
              const pct = total ? Math.round(((count as number) / total) * 100) : 0;
              return (
                <div key={key} className="decision-bar-row">
                  <span className="decision-label" style={{ color: decisionColors[key] }}>
                    {key === "accept" ? "✅" : key === "decline" ? "❌" : "⚠️"} {key.toUpperCase()}
                  </span>
                  <div className="decision-bar-track">
                    <div
                      className="decision-bar-fill"
                      style={{ width: `${pct}%`, background: decisionColors[key] }}
                    />
                  </div>
                  <span className="decision-count">{count as number} ({pct}%)</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="analytics-card">
          <h3>Document Types Processed</h3>
          <div className="doc-type-grid">
            {Object.entries(document_types).map(([type, count]) => (
              <div key={type} className="doc-type-item">
                <span className="doc-type-icon">
                  {type === "insurance_application" ? "📄" :
                   type === "driver_list" ? "👤" :
                   type === "equipment_list" ? "🚛" :
                   type === "ifta_report" ? "⛽" :
                   type === "loss_run" ? "📊" :
                   type === "drivers_license" ? "🪪" : "📁"}
                </span>
                <span className="doc-type-name">{type.replace(/_/g, " ")}</span>
                <span className="doc-type-count">{count as number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Processing Time Chart */}
      <div className="analytics-card">
        <h3>Processing Time History</h3>
        <div className="time-chart">
          {(timeline || []).map((t: any, i: number) => (
            <div key={i} className="time-bar-col" title={`${t.company}: ${t.time_seconds}s`}>
              <div
                className="time-bar"
                style={{
                  height: `${(t.time_seconds / maxTime) * 100}%`,
                  background: t.decision === "accept" ? "#059669" :
                              t.decision === "decline" ? "#DC2626" : "#D97706",
                }}
              />
              <span className="time-bar-label">{t.time_seconds}s</span>
            </div>
          ))}
        </div>
        <div className="chart-legend">
          <span><span className="legend-dot" style={{ background: "#059669" }} /> Accept</span>
          <span><span className="legend-dot" style={{ background: "#D97706" }} /> Refer</span>
          <span><span className="legend-dot" style={{ background: "#DC2626" }} /> Decline</span>
        </div>
      </div>

      {/* Rule Stats */}
      <div className="analytics-card">
        <h3>Rule Performance</h3>
        <div className="rule-stats-table">
          <div className="rule-stats-header">
            <span>Rule ID</span><span>Pass</span><span>Fail</span><span>Warning</span><span>Pass Rate</span>
          </div>
          {Object.entries(rule_stats)
            .sort(([, a]: any, [, b]: any) => b.fail - a.fail)
            .map(([id, stats]: any) => {
              const total = stats.pass + stats.fail + stats.warning;
              const passRate = total ? Math.round((stats.pass / total) * 100) : 100;
              return (
                <div key={id} className="rule-stats-row">
                  <span className="rule-id-mono">{id}</span>
                  <span className="stat-pass">{stats.pass}</span>
                  <span className="stat-fail">{stats.fail}</span>
                  <span className="stat-warn">{stats.warning}</span>
                  <span>
                    <span
                      className="pass-rate-bar"
                      style={{
                        width: `${passRate}%`,
                        background: passRate === 100 ? "#059669" : passRate > 80 ? "#D97706" : "#DC2626",
                      }}
                    />
                    {passRate}%
                  </span>
                </div>
              );
          })}
        </div>
      </div>

      {/* Performance Stats */}
      <div className="analytics-row">
        <div className="analytics-card">
          <h3>Processing Speed</h3>
          <div className="perf-stats">
            <div className="perf-stat">
              <span className="perf-label">Fastest</span>
              <span className="perf-value" style={{ color: "#059669" }}>{summary.min_processing_time}s</span>
            </div>
            <div className="perf-stat">
              <span className="perf-label">Average</span>
              <span className="perf-value" style={{ color: "#2563EB" }}>{summary.avg_processing_time}s</span>
            </div>
            <div className="perf-stat">
              <span className="perf-label">Slowest</span>
              <span className="perf-value" style={{ color: "#DC2626" }}>{summary.max_processing_time}s</span>
            </div>
          </div>
        </div>
        <div className="analytics-card">
          <h3>Token Usage</h3>
          <div className="perf-stats">
            <div className="perf-stat">
              <span className="perf-label">Input Tokens</span>
              <span className="perf-value">{summary.total_input_tokens.toLocaleString()}</span>
            </div>
            <div className="perf-stat">
              <span className="perf-label">Output Tokens</span>
              <span className="perf-value">{summary.total_output_tokens.toLocaleString()}</span>
            </div>
            <div className="perf-stat">
              <span className="perf-label">Avg Calls/Sub</span>
              <span className="perf-value">
                {summary.total_submissions ? Math.round(summary.total_ai_calls / summary.total_submissions) : 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
