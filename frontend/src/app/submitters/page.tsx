"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getSubmitters, getSubmitterSubmissions, type Submitter } from "@/lib/api";
import type { Submission } from "@/types";

const decisionColor: Record<string, { bg: string; color: string; label: string }> = {
  accept: { bg: "var(--success-light)", color: "var(--success)", label: "Accepted" },
  decline: { bg: "var(--error-light)", color: "var(--error)", label: "Declined" },
  refer: { bg: "var(--warning-light)", color: "var(--warning)", label: "Referred" },
};

const statusStyles: Record<string, { bg: string; color: string }> = {
  received: { bg: "var(--info-light)", color: "var(--info)" },
  processing: { bg: "var(--warning-light)", color: "var(--warning)" },
  complete: { bg: "var(--success-light)", color: "var(--success)" },
  failed: { bg: "var(--error-light)", color: "var(--error)" },
};

export default function SubmittersPage() {
  const [submitters, setSubmitters] = useState<Submitter[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState<string | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loadingSubs, setLoadingSubs] = useState(false);

  useEffect(() => {
    getSubmitters().then(setSubmitters).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleSelectSubmitter = async (email: string) => {
    if (selectedEmail === email) {
      setSelectedEmail(null);
      setSubmissions([]);
      return;
    }
    setSelectedEmail(email);
    setLoadingSubs(true);
    try {
      const subs = await getSubmitterSubmissions(email);
      setSubmissions(subs);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSubs(false);
    }
  };

  const fmtDate = (d: string | null) => {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  const fmtTime = (d: string | null) => {
    if (!d) return "";
    return new Date(d).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Stats row */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <div className="card" style={{ flex: 1, minWidth: 140, textAlign: "center", padding: 16 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--primary)" }}>{submitters.length}</div>
          <div style={{ fontSize: 11, color: "var(--base)", fontWeight: 500 }}>Total Submitters</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 140, textAlign: "center", padding: 16 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--info)" }}>
            {submitters.filter(s => !s.is_ui_upload).length}
          </div>
          <div style={{ fontSize: 11, color: "var(--base)", fontWeight: 500 }}>Email Submitters</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 140, textAlign: "center", padding: 16 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--accent-warm)" }}>
            {submitters.filter(s => s.is_ui_upload).length}
          </div>
          <div style={{ fontSize: 11, color: "var(--base)", fontWeight: 500 }}>UI Uploads</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 140, textAlign: "center", padding: 16 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--success)" }}>
            {submitters.reduce((a, s) => a + s.submission_count, 0)}
          </div>
          <div style={{ fontSize: 11, color: "var(--base)", fontWeight: 500 }}>Total Submissions</div>
        </div>
      </div>

      {/* Submitter List */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "var(--surface-alt)", borderBottom: "1px solid var(--border)" }}>
              <th style={{ textAlign: "left", padding: "10px 16px", fontWeight: 600, color: "var(--base-dark)" }}>Submitter</th>
              <th style={{ textAlign: "left", padding: "10px 12px", fontWeight: 600, color: "var(--base-dark)" }}>Source</th>
              <th style={{ textAlign: "center", padding: "10px 12px", fontWeight: 600, color: "var(--base-dark)" }}>Submissions</th>
              <th style={{ textAlign: "center", padding: "10px 12px", fontWeight: 600, color: "var(--base-dark)" }}>Accepted</th>
              <th style={{ textAlign: "center", padding: "10px 12px", fontWeight: 600, color: "var(--base-dark)" }}>Declined</th>
              <th style={{ textAlign: "center", padding: "10px 12px", fontWeight: 600, color: "var(--base-dark)" }}>Referred</th>
              <th style={{ textAlign: "left", padding: "10px 12px", fontWeight: 600, color: "var(--base-dark)" }}>Last Activity</th>
            </tr>
          </thead>
          <tbody>
            {submitters.map(sub => (
              <>
                <tr
                  key={sub.email}
                  onClick={() => handleSelectSubmitter(sub.email)}
                  style={{
                    cursor: "pointer",
                    borderBottom: "1px solid var(--border-light)",
                    background: selectedEmail === sub.email ? "var(--primary-lighter)" : undefined,
                    transition: ".15s",
                  }}
                  onMouseEnter={e => { if (selectedEmail !== sub.email) (e.currentTarget as HTMLElement).style.background = "var(--surface-alt)" }}
                  onMouseLeave={e => { if (selectedEmail !== sub.email) (e.currentTarget as HTMLElement).style.background = "" }}
                >
                  <td style={{ padding: "10px 16px" }}>
                    <div style={{ fontWeight: 600, color: "var(--ink)" }}>{sub.name}</div>
                    <div style={{ fontSize: 11, color: "var(--base)" }}>{sub.email}</div>
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    <span style={{
                      padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600,
                      background: sub.is_ui_upload ? "var(--warning-light)" : "var(--info-light)",
                      color: sub.is_ui_upload ? "var(--warning-dark)" : "var(--info)",
                    }}>
                      {sub.is_ui_upload ? "📤 UI Upload" : "📧 Email"}
                    </span>
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "center", fontWeight: 700, color: "var(--ink)" }}>{sub.submission_count}</td>
                  <td style={{ padding: "10px 12px", textAlign: "center", fontWeight: 600, color: "var(--success)" }}>{sub.accepted || "—"}</td>
                  <td style={{ padding: "10px 12px", textAlign: "center", fontWeight: 600, color: "var(--error)" }}>{sub.declined || "—"}</td>
                  <td style={{ padding: "10px 12px", textAlign: "center", fontWeight: 600, color: "var(--warning)" }}>{sub.referred || "—"}</td>
                  <td style={{ padding: "10px 12px", color: "var(--base-dark)", fontSize: 11 }}>{fmtDate(sub.last_submission)}</td>
                </tr>

                {/* Expanded submissions */}
                {selectedEmail === sub.email && (
                  <tr key={`${sub.email}-expand`}>
                    <td colSpan={7} style={{ padding: 0, background: "var(--surface-alt)" }}>
                      {loadingSubs ? (
                        <div style={{ padding: 20, textAlign: "center" }}><div className="spinner" /></div>
                      ) : (
                        <div style={{ padding: "12px 24px 16px" }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--base-dark)", marginBottom: 8 }}>
                            Submissions from {sub.name}
                          </div>
                          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                            {submissions.map(s => {
                              const dec = s.overall_decision ? decisionColor[s.overall_decision] : null;
                              const st = statusStyles[s.status] || statusStyles.received;
                              return (
                                <Link
                                  key={s.id}
                                  href={`/submissions/${s.id}`}
                                  style={{
                                    display: "flex", alignItems: "center", gap: 12,
                                    padding: "10px 14px", background: "var(--surface)",
                                    border: "1px solid var(--border)", borderRadius: 8,
                                    textDecoration: "none", color: "var(--ink)",
                                    transition: ".15s",
                                  }}
                                  onMouseEnter={e => (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 8px rgba(0,0,0,.06)"}
                                  onMouseLeave={e => (e.currentTarget as HTMLElement).style.boxShadow = ""}
                                >
                                  <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 12, fontWeight: 600 }}>
                                      {s.email_subject || `Submission ${s.id.slice(0, 8)}`}
                                    </div>
                                    <div style={{ fontSize: 10, color: "var(--base)", marginTop: 2 }}>
                                      {fmtDate(s.created_at)} {fmtTime(s.created_at)} · {s.document_count || 0} docs
                                    </div>
                                  </div>
                                  <span style={{
                                    padding: "3px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600,
                                    background: st.bg, color: st.color,
                                  }}>
                                    {s.status}
                                  </span>
                                  {dec && (
                                    <span style={{
                                      padding: "3px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600,
                                      background: dec.bg, color: dec.color,
                                    }}>
                                      {dec.label}
                                    </span>
                                  )}
                                  <span style={{ fontSize: 14, color: "var(--base-light)" }}>→</span>
                                </Link>
                              );
                            })}
                            {submissions.length === 0 && (
                              <div style={{ padding: 12, fontSize: 11, color: "var(--base)", textAlign: "center" }}>
                                No submissions found
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>

        {submitters.length === 0 && (
          <div style={{ padding: 40, textAlign: "center", color: "var(--base)" }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📭</div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>No submitters yet</div>
            <div style={{ fontSize: 11, marginTop: 4 }}>Submit documents via email or the upload form</div>
          </div>
        )}
      </div>
    </div>
  );
}
