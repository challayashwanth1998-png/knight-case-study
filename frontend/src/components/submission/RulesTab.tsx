"use client";

import type { RuleResult } from "@/types";

interface Props {
  rules: RuleResult[];
}

const RESULT_ICON: Record<string, string> = {
  PASS: "✓", FAIL: "✗", WARNING: "!", SKIP: "—", INFO: "i",
};

const RESULT_COLOR: Record<string, string> = {
  PASS: "#059669", FAIL: "#DC2626", WARNING: "#D97706",
  SKIP: "#9CA3AF", INFO: "#2563EB",
};

export default function RulesTab({ rules }: Props) {
  const categories = [...new Set(rules.map((r) => r.category))];

  return (
    <div style={{ display: "grid", gap: 20 }}>
      {categories.map((cat) => (
        <div key={cat}>
          <h3
            style={{
              fontSize: 11, fontWeight: 600, textTransform: "uppercase",
              letterSpacing: "0.5px", color: "#9CA3AF", marginBottom: 8,
            }}
          >
            {cat}
          </h3>
          <div style={{ display: "grid", gap: 6 }}>
            {rules
              .filter((r) => r.category === cat)
              .map((r) => (
                <div
                  key={r.id}
                  className="card"
                  style={{
                    padding: "12px 16px",
                    borderLeft: `3px solid ${RESULT_COLOR[r.result] || "#E5E7EB"}`,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span
                        style={{
                          width: 20, height: 20, borderRadius: "50%",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 11, fontWeight: 700,
                          color: RESULT_COLOR[r.result],
                          background: r.result === "PASS" ? "#ECFDF5" :
                                     r.result === "FAIL" ? "#FEF2F2" :
                                     r.result === "WARNING" ? "#FFFBEB" : "#F9FAFB",
                        }}
                      >
                        {RESULT_ICON[r.result]}
                      </span>
                      <div>
                        <div style={{ fontWeight: 500, fontSize: 13 }}>{r.rule_name}</div>
                        <div style={{ fontSize: 11, color: "#9CA3AF", fontFamily: "monospace" }}>
                          {r.rule_id}
                        </div>
                      </div>
                    </div>
                    <span className={`badge badge-${r.result}`} style={{ fontSize: 11 }}>
                      {r.result}
                    </span>
                  </div>
                  {r.details && (
                    <div style={{ marginTop: 6, fontSize: 12, color: "#6B7280", paddingLeft: 28 }}>
                      {r.details}
                    </div>
                  )}
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
