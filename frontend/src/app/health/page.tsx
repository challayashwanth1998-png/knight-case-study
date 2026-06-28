"use client";

import { useState, useEffect } from "react";
import { getHealth, getAnalytics } from "@/lib/api";

export default function HealthPage() {
  const [health, setHealth] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const refresh = () => {
    setLoading(true);
    Promise.all([getHealth(), getAnalytics()])
      .then(([h, a]) => { setHealth(h); setAnalytics(a); setLastChecked(new Date()); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { refresh(); }, []);

  // Auto-refresh every 30s
  useEffect(() => {
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) return <div className="page-container"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1>🏥 System Health</h1>
          <p className="page-subtitle">Real-time infrastructure monitoring</p>
        </div>
        <button className="health-refresh-btn" onClick={refresh} disabled={loading}>
          {loading ? "⟳ Checking..." : "⟳ Refresh"}
        </button>
      </div>

      {health && (
        <>
          {/* Overall Status */}
          <div className={`health-status-banner ${health.status === "healthy" ? "healthy" : "degraded"}`}>
            <span className="health-status-icon">
              {health.status === "healthy" ? "✅" : "⚠️"}
            </span>
            <div>
              <div className="health-status-text">
                System {health.status === "healthy" ? "Healthy" : "Degraded"}
              </div>
              <div className="health-status-time">
                Last checked: {lastChecked?.toLocaleTimeString() || "—"} • Auto-refresh: 30s
              </div>
            </div>
          </div>

          {/* Service Cards */}
          <div className="health-grid">
            {/* Database */}
            <div className="health-card">
              <div className="health-card-header">
                <span className="health-card-icon">🗃️</span>
                <span className={`health-dot ${health.database.status === "healthy" ? "green" : "red"}`} />
              </div>
              <h3>Database</h3>
              <div className="health-detail">
                <span>Status</span><span className="health-val">{health.database.status}</span>
              </div>
              <div className="health-detail">
                <span>Latency</span><span className="health-val">{health.database.latency_ms}ms</span>
              </div>
              <div className="health-detail">
                <span>Submissions</span><span className="health-val">{health.counts.submissions}</span>
              </div>
              <div className="health-detail">
                <span>Documents</span><span className="health-val">{health.counts.documents}</span>
              </div>
            </div>

            {/* AI Service */}
            <div className="health-card">
              <div className="health-card-header">
                <span className="health-card-icon">🧠</span>
                <span className={`health-dot ${health.ai_service.status === "configured" ? "green" : "yellow"}`} />
              </div>
              <h3>AI Service</h3>
              <div className="health-detail">
                <span>Status</span><span className="health-val">{health.ai_service.status}</span>
              </div>
              <div className="health-detail">
                <span>Model</span><span className="health-val">{health.ai_service.model}</span>
              </div>
              <div className="health-detail">
                <span>Processing</span><span className="health-val">{health.counts.currently_processing} active</span>
              </div>
            </div>

            {/* Storage */}
            <div className="health-card">
              <div className="health-card-header">
                <span className="health-card-icon">💾</span>
                <span className={`health-dot ${health.storage.disk_free_gb > 1 ? "green" : "red"}`} />
              </div>
              <h3>Storage</h3>
              <div className="health-detail">
                <span>Free Space</span><span className="health-val">{health.storage.disk_free_gb} GB</span>
              </div>
              <div className="health-detail">
                <span>Total</span><span className="health-val">{health.storage.disk_total_gb} GB</span>
              </div>
              <div className="health-detail">
                <span>Used</span>
                <span className="health-val">
                  {health.storage.disk_total_gb ? Math.round(((health.storage.disk_total_gb - health.storage.disk_free_gb) / health.storage.disk_total_gb) * 100) : 0}%
                </span>
              </div>
              <div className="disk-bar">
                <div
                  className="disk-bar-fill"
                  style={{
                    width: `${health.storage.disk_total_gb ? Math.round(((health.storage.disk_total_gb - health.storage.disk_free_gb) / health.storage.disk_total_gb) * 100) : 0}%`,
                  }}
                />
              </div>
            </div>

            {/* API */}
            <div className="health-card">
              <div className="health-card-header">
                <span className="health-card-icon">🌐</span>
                <span className="health-dot green" />
              </div>
              <h3>API Server</h3>
              <div className="health-detail">
                <span>Status</span><span className="health-val">Running</span>
              </div>
              <div className="health-detail">
                <span>Version</span><span className="health-val">{health.version}</span>
              </div>
              <div className="health-detail">
                <span>Framework</span><span className="health-val">FastAPI</span>
              </div>
            </div>
          </div>

          {/* Cost Summary */}
          {analytics && analytics.summary && (
            <div className="health-card" style={{ marginTop: 16 }}>
              <h3>💰 Cumulative AI Costs</h3>
              <div className="cost-summary-grid">
                <div className="cost-item">
                  <div className="cost-value">${analytics.summary.total_ai_cost.toFixed(4)}</div>
                  <div className="cost-label">Total Spend</div>
                </div>
                <div className="cost-item">
                  <div className="cost-value">${analytics.summary.avg_ai_cost.toFixed(4)}</div>
                  <div className="cost-label">Per Submission</div>
                </div>
                <div className="cost-item">
                  <div className="cost-value">{analytics.summary.total_ai_calls}</div>
                  <div className="cost-label">Total API Calls</div>
                </div>
                <div className="cost-item">
                  <div className="cost-value">{((analytics.summary.total_input_tokens + analytics.summary.total_output_tokens) / 1000).toFixed(1)}K</div>
                  <div className="cost-label">Total Tokens</div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
