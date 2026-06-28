"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { listSubmissions, getStats } from "@/lib/api";
import type { Submission, DashboardStats } from "@/types";

export default function AdminDashboardPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [subs, st] = await Promise.all([listSubmissions(), getStats()]);
      setSubmissions(subs);
      setStats(st);
    } catch { /* backend might be down */ }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const recentSubs = submissions.slice(0, 5);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div className="page-header">
        <h1 className="page-title">Admin Dashboard</h1>
        <p className="page-description">Knight Specialty Insurance — Global Operations Overview</p>
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

      {/* Quick Actions */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <Link href="/submissions" style={{ textDecoration: "none" }}>
          <div className="card card-clickable" style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 8,
              background: "var(--info-light)", color: "var(--accent-cool-dark)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 20,
            }}>📋</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Manage All Submissions</div>
              <div style={{ fontSize: 12, color: "var(--base)" }}>
                Browse, filter, and delete raw submissions
              </div>
            </div>
          </div>
        </Link>
        <Link href="/rules" style={{ textDecoration: "none" }}>
          <div className="card card-clickable" style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 8,
              background: "var(--primary-lighter)", color: "var(--primary)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 20,
            }}>⚖️</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Configure Rules Engine</div>
              <div style={{ fontSize: 12, color: "var(--base)" }}>
                View current underwriting parameters
              </div>
            </div>
          </div>
        </Link>
      </div>

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
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--ink)" }}>
            Recent Activity (All)
          </h3>
          {recentSubs.length > 0 ? (
            <div>
              {recentSubs.map((s) => (
                <Link key={s.id} href={`/submissions/${s.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                  <div style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "8px 0", borderBottom: "1px solid var(--border-light)",
                  }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>
                        {s.email_subject || `Submission ${s.id.slice(0, 8)}`}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--base)" }}>
                        {new Date(s.created_at).toLocaleDateString()}
                        {s.document_count ? ` · ${s.document_count} docs` : ""}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 6 }}>
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
    </div>
  );
}
