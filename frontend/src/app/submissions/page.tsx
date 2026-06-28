"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { listSubmissions, deleteSubmission } from "@/lib/api";
import type { Submission } from "@/types";

export default function SubmissionsPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const loadData = useCallback(async () => {
    try {
      setSubmissions(await listSubmissions());
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this submission?")) return;
    await deleteSubmission(id);
    loadData();
  };

  const filtered = submissions.filter((s) => {
    if (filter !== "all") {
      if (["accept", "decline", "refer"].includes(filter)) {
        if (s.overall_decision !== filter) return false;
      } else {
        if (s.status !== filter) return false;
      }
    }
    if (search) {
      const q = search.toLowerCase();
      return (
        s.id.toLowerCase().includes(q) ||
        s.email_subject?.toLowerCase().includes(q) ||
        s.email_from?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const filters = [
    { key: "all", label: "All" },
    { key: "processing", label: "Processing" },
    { key: "complete", label: "Complete" },
    { key: "accept", label: "Accepted" },
    { key: "decline", label: "Declined" },
    { key: "refer", label: "Referred" },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">All Submissions</h1>
          <p className="page-description">{submissions.length} total submissions</p>
        </div>
        <Link href="/submit" className="btn btn-primary">
          + New Submission
        </Link>
      </div>

      {/* Filters + Search */}
      <div className="card" style={{ marginBottom: 16, padding: 14, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 4 }}>
          {filters.map((f) => (
            <button
              key={f.key}
              className={`btn btn-sm ${filter === f.key ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Search submissions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            marginLeft: "auto",
            padding: "6px 12px",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            fontSize: 13,
            width: 220,
            outline: "none",
            fontFamily: "inherit",
          }}
        />
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {filtered.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Submission</th>
                <th>Source</th>
                <th>Status</th>
                <th>Decision</th>
                <th>Documents</th>
                <th>AI Cost</th>
                <th>Date</th>
                <th style={{ width: 60 }}></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr key={s.id}>
                  <td>
                    <Link href={`/submissions/${s.id}`} style={{ color: "var(--primary)", textDecoration: "none", fontWeight: 500 }}>
                      {s.email_subject || `Sub. ${s.id.slice(0, 8)}`}
                    </Link>
                    <div style={{ fontSize: 10, color: "var(--base)", fontFamily: "monospace" }}>
                      {s.id.slice(0, 12)}...
                    </div>
                  </td>
                  <td style={{ fontSize: 12 }}>{s.email_from}</td>
                  <td>
                    <span className={`badge badge-${s.status}`}>
                      {s.status === "processing" && <span className="spinner" style={{ width: 8, height: 8 }} />}
                      {s.status}
                    </span>
                  </td>
                  <td>
                    {s.overall_decision ? (
                      <span className={`badge badge-${s.overall_decision}`}>{s.overall_decision}</span>
                    ) : (
                      <span style={{ fontSize: 12, color: "var(--base)" }}>—</span>
                    )}
                  </td>
                  <td style={{ fontSize: 13 }}>{s.document_count ?? 0}</td>
                  <td style={{ fontSize: 12, fontFamily: "monospace" }}>
                    {s.ai_cost_usd > 0 ? `$${s.ai_cost_usd.toFixed(4)}` : "—"}
                  </td>
                  <td style={{ fontSize: 12, color: "var(--base)" }}>
                    {new Date(s.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      style={{ padding: "2px 6px", fontSize: 10 }}
                      onClick={() => handleDelete(s.id)}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">📋</div>
            <div className="empty-state-title">No submissions found</div>
            <div className="empty-state-desc">
              {search ? "Try adjusting your search" : "Upload documents to get started"}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
