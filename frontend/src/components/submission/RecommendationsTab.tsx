"use client";

interface Props {
  recommendations: Array<Record<string, unknown>>;
}

export default function RecommendationsTab({ recommendations }: Props) {
  if (recommendations.length === 0) {
    return <div className="card" style={{ color: "#9CA3AF" }}>No recommendations yet.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {recommendations.map((r, i) => (
        <div key={i} className="card">
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>{r.title as string}</span>
            <span
              className={`badge ${(r.priority as string) === "critical" ? "badge-fail" : (r.priority as string) === "high" ? "badge-warning" : "badge-info"}`}
              style={{ fontSize: 11 }}
            >
              {r.priority as string}
            </span>
          </div>
          <div style={{ fontSize: 13, color: "#6B7280" }}>{r.description as string}</div>
        </div>
      ))}
    </div>
  );
}
