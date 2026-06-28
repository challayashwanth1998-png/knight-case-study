"use client";

interface Props {
  conflicts: Array<Record<string, unknown>>;
}

const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
const SEV_COLOR: Record<string, string> = {
  critical: "#DC2626", high: "#D97706", medium: "#2563EB", low: "#9CA3AF",
};

export default function ConflictsTab({ conflicts }: Props) {
  if (conflicts.length === 0) {
    return (
      <div className="card" style={{ textAlign: "center", padding: 32, color: "#9CA3AF" }}>
        No conflicts detected
      </div>
    );
  }

  const sorted = [...conflicts].sort(
    (a, b) =>
      (SEV_ORDER[a.severity as keyof typeof SEV_ORDER] ?? 4) -
      (SEV_ORDER[b.severity as keyof typeof SEV_ORDER] ?? 4),
  );

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {sorted.map((c, i) => (
        <div
          key={i}
          className="card"
          style={{ borderLeft: `3px solid ${SEV_COLOR[c.severity as string] || "#E5E7EB"}` }}
        >
          <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
            <span className={`badge badge-${c.severity === "critical" || c.severity === "high" ? "fail" : "warning"}`}>
              {c.severity as string}
            </span>
            <span style={{ fontSize: 11, color: "#9CA3AF", textTransform: "uppercase" }}>
              {c.type as string}
            </span>
          </div>
          <div style={{ fontSize: 13 }}>{c.description as string}</div>
        </div>
      ))}
    </div>
  );
}
