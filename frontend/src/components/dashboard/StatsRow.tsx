"use client";

import type { DashboardStats } from "@/types";

interface Props {
  stats: DashboardStats | null;
}

const items = [
  { key: "total_submissions", label: "Total", color: "#1F2937" },
  { key: "pending", label: "Pending", color: "#2563EB" },
  { key: "processing", label: "Processing", color: "#D97706" },
  { key: "complete", label: "Complete", color: "#059669" },
  { key: "accepted", label: "Accepted", color: "#059669" },
  { key: "declined", label: "Declined", color: "#DC2626" },
  { key: "referred", label: "Referred", color: "#D97706" },
] as const;

export default function StatsRow({ stats }: Props) {
  if (!stats) return null;

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
        gap: 12,
        marginBottom: 28,
      }}
    >
      {items.map((item) => (
        <div key={item.key} className="stat-card">
          <div style={{ fontSize: 24, fontWeight: 700, color: item.color }}>
            {stats[item.key as keyof DashboardStats]}
          </div>
          <div
            style={{
              fontSize: 11,
              color: "#9CA3AF",
              marginTop: 2,
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              fontWeight: 500,
            }}
          >
            {item.label}
          </div>
        </div>
      ))}
    </div>
  );
}
