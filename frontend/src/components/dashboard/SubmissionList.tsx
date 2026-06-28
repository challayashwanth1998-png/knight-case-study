"use client";

import { useRouter } from "next/navigation";
import type { Submission } from "@/types";

interface Props {
  submissions: Submission[];
  onDelete: (id: string) => void;
  filterStatus?: string;
}

export default function SubmissionList({ submissions, onDelete, filterStatus }: Props) {
  const router = useRouter();

  const formatDate = (d: string | null) => {
    if (!d) return "—";
    return new Date(d).toLocaleString("en-US", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  };

  const filteredSubmissions = filterStatus 
    ? submissions.filter(s => s.status === filterStatus)
    : submissions;

  return (
    <div className="animate-slide-up">
      <h2
        style={{
          fontSize: 15,
          fontWeight: 600,
          marginBottom: 14,
          color: "#1F2937",
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        Submissions
        <span style={{ fontSize: 12, fontWeight: 400, color: "#9CA3AF" }}>
          ({filteredSubmissions.length})
        </span>
      </h2>

      {filteredSubmissions.length === 0 ? (
        <div
          className="card"
          style={{ textAlign: "center", padding: 40, color: "#9CA3AF" }}
        >
          <div style={{ fontSize: 14, fontWeight: 500 }}>No submissions yet</div>
          <div style={{ fontSize: 13, marginTop: 4 }}>
            {filterStatus === "complete" 
              ? "No completed submissions found. Submissions will appear here after AI processing."
              : "Upload documents above to get started"}
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {filteredSubmissions.map((sub) => (
            <div
              key={sub.id}
              className="card card-clickable"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "16px 20px",
              }}
              onClick={() => router.push(`/submissions/${sub.id}`)}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <span style={{ fontSize: 14, fontWeight: 500, color: "#1F2937" }}>
                    {sub.email_subject || `Submission ${sub.id.slice(0, 8)}`}
                  </span>
                  <span className={`badge badge-${sub.status}`}>
                    {sub.status === "processing" && (
                      <span className="spinner" style={{ width: 10, height: 10 }} />
                    )}
                    {sub.status}
                  </span>
                  {sub.overall_decision && (
                    <span className={`badge badge-${sub.overall_decision}`}>
                      {sub.overall_decision}
                    </span>
                  )}
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 16,
                    fontSize: 12,
                    color: "#9CA3AF",
                  }}
                >
                  <span>{sub.document_count || 0} documents</span>
                  <span>{formatDate(sub.created_at)}</span>
                </div>
                {sub.decision_reason && (
                  <div
                    style={{
                      fontSize: 12,
                      color: "#6B7280",
                      marginTop: 4,
                      maxWidth: 600,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {sub.decision_reason}
                  </div>
                )}
              </div>
              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                <button
                  className="btn btn-danger"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm("Delete this submission?")) onDelete(sub.id);
                  }}
                  style={{ padding: "5px 10px", fontSize: 12 }}
                >
                  Delete
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ padding: "5px 10px", fontSize: 12 }}
                >
                  View →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
