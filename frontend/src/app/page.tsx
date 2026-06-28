"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { listSubmissions, getStats, getAnalytics } from "@/lib/api";
import type { Submission, DashboardStats } from "@/types";

export default function DashboardPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);

  const loadData = useCallback(async () => {
    try {
      const [subs, st] = await Promise.all([listSubmissions(), getStats()]);
      setSubmissions(subs);
      setStats(st);
      // Load analytics in background (non-blocking)
      getAnalytics().then(setAnalytics).catch(() => {});
    } catch { /* backend might be down */ }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const recentSubs = submissions.slice(0, 8);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-description">Knight Specialty Insurance — Operations Overview</p>
        </div>
        <Link href="/submit" className="btn btn-primary">
          + New Submission
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid-5" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-value">{stats?.total_submissions ?? "—"}</div>
          <div className="stat-label">Total Submissions</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--primary)" }}>
            {stats?.processing ?? 0}
          </div>
          <div className="stat-label">Processing</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--success)" }}>
            {stats?.accepted ?? 0}
          </div>
          <div className="stat-label">Accepted</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--error)" }}>
            {stats?.declined ?? 0}
          </div>
          <div className="stat-label">Declined</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--warning-dark)" }}>
            {stats?.referred ?? 0}
          </div>
          <div className="stat-label">Referred</div>
        </div>
      </div>

      {/* Quick Performance Metrics (from analytics) */}
      {analytics?.summary && (
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24,
        }}>
          <div className="card" style={{ textAlign: "center", padding: 14 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#2563EB" }}>
              {analytics.summary.avg_processing_time}s
            </div>
            <div style={{ fontSize: 10, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Avg Processing
            </div>
          </div>
          <div className="card" style={{ textAlign: "center", padding: 14 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#059669" }}>
              ${analytics.summary.avg_ai_cost.toFixed(4)}
            </div>
            <div style={{ fontSize: 10, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Avg AI Cost
            </div>
          </div>
          <div className="card" style={{ textAlign: "center", padding: 14 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#7C3AED" }}>
              {Math.round(analytics.summary.total_ai_calls / Math.max(analytics.summary.total_submissions, 1))}
            </div>
            <div style={{ fontSize: 10, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Avg AI Calls
            </div>
          </div>
          <div className="card" style={{ textAlign: "center", padding: 14 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#D97706" }}>
              ${analytics.summary.total_ai_cost.toFixed(3)}
            </div>
            <div style={{ fontSize: 10, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Total AI Spend
            </div>
          </div>
        </div>
      )}

      {/* Decision Distribution + Recent Activity */}
      <div className="grid-2">
        {/* Decision Breakdown */}
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--ink)" }}>
            Decision Distribution
          </h3>
          {stats && stats.total_submissions > 0 ? (
            <div>
              {[
                { label: "Accepted", count: stats.accepted, color: "var(--success)", bg: "var(--success-light)" },
                { label: "Declined", count: stats.declined, color: "var(--error)", bg: "var(--error-light)" },
                { label: "Referred", count: stats.referred, color: "var(--warning)", bg: "var(--warning-light)" },
                { label: "Pending", count: stats.pending + stats.processing, color: "var(--base)", bg: "var(--surface-alt)" },
              ].map((d) => (
                <div key={d.label} style={{ marginBottom: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                    <span style={{ fontWeight: 500 }}>{d.label}</span>
                    <span style={{ color: "var(--base)" }}>
                      {d.count} ({stats.total_submissions > 0 ? Math.round((d.count / stats.total_submissions) * 100) : 0}%)
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${stats.total_submissions > 0 ? (d.count / stats.total_submissions) * 100 : 0}%`,
                        background: d.color,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: "20px 0" }}>
              <div className="empty-state-desc">No submissions yet</div>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)" }}>
              Recent Activity
            </h3>
            <Link href="/submissions" style={{ fontSize: 11, color: "var(--primary-light)", textDecoration: "none" }}>
              View All →
            </Link>
          </div>
          {recentSubs.length > 0 ? (
            <div>
              {recentSubs.map((s) => (
                <Link key={s.id} href={`/submissions/${s.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                  <div style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "8px 0", borderBottom: "1px solid var(--border-light)",
                  }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {s.email_subject || `Submission ${s.id.slice(0, 8)}`}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--base)", display: "flex", gap: 8 }}>
                        <span>{new Date(s.created_at).toLocaleDateString()}</span>
                        {s.document_count ? <span>· {s.document_count} docs</span> : null}
                        {s.processing_duration_ms ? (
                          <span>· {(s.processing_duration_ms / 1000).toFixed(1)}s</span>
                        ) : null}
                        {s.ai_cost_usd ? (
                          <span>· ${s.ai_cost_usd.toFixed(4)}</span>
                        ) : null}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 6, flexShrink: 0, marginLeft: 8 }}>
                      <span className={`badge badge-${s.status}`}>{s.status}</span>
                      {s.overall_decision && (
                        <span className={`badge badge-${s.overall_decision}`}>{s.overall_decision}</span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: "20px 0" }}>
              <div className="empty-state-desc">No activity yet</div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginTop: 24,
      }}>
        {[
          { href: "/submit", icon: "📤", label: "New Submission", desc: "Upload documents" },
          { href: "/analytics", icon: "📈", label: "Analytics", desc: "View performance" },
          { href: "/rules", icon: "⚖️", label: "Rules Engine", desc: "View underwriting rules" },
          { href: "/architecture", icon: "🏗️", label: "Architecture", desc: "System diagram" },
        ].map((link) => (
          <Link key={link.href} href={link.href} style={{ textDecoration: "none" }}>
            <div className="card" style={{
              textAlign: "center", padding: 20, cursor: "pointer",
              transition: "all 0.2s",
            }}>
              <div style={{ fontSize: 28 }}>{link.icon}</div>
              <div style={{ fontSize: 13, fontWeight: 600, marginTop: 8, color: "var(--ink)" }}>
                {link.label}
              </div>
              <div style={{ fontSize: 11, color: "var(--base)", marginTop: 4 }}>
                {link.desc}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
