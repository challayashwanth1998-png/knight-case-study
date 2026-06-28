"use client";

import { useState, useEffect } from "react";
import { getRulesReference } from "@/lib/api";
import type { RuleDefinition } from "@/types";

const CATEGORIES = [
  { key: "all", label: "All Rules" },
  { key: "eligibility", label: "Eligibility" },
  { key: "driver", label: "Driver" },
  { key: "exposure", label: "Exposure" },
  { key: "submission", label: "Submission" },
  { key: "ifta", label: "IFTA" },
  { key: "selective", label: "Selective" },
];

const CATEGORY_ICONS: Record<string, string> = {
  eligibility: "🎯",
  driver: "🚛",
  exposure: "⚠️",
  submission: "📋",
  ifta: "⛽",
  selective: "🔍",
};

export default function RulesPage() {
  const [rules, setRules] = useState<RuleDefinition[]>([]);
  const [category, setCategory] = useState("all");

  useEffect(() => {
    getRulesReference().then(setRules).catch(() => {
      // Fallback: use hardcoded list if backend is down
    });
  }, []);

  const filtered = category === "all" ? rules : rules.filter((r) => r.category === category);

  const severityCounts = {
    critical: filtered.filter((r) => r.severity === "critical").length,
    high: filtered.filter((r) => r.severity === "high").length,
    medium: filtered.filter((r) => r.severity === "medium").length,
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div className="page-header">
        <h1 className="page-title">Rules Engine</h1>
        <p className="page-description">
          {rules.length} business rules based on Knight Specialty Insurance underwriting guidelines
        </p>
      </div>

      {/* Severity Stats */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span className="badge badge-critical" style={{ fontSize: 14, padding: "4px 10px" }}>
            {severityCounts.critical}
          </span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>Critical Rules</div>
            <div style={{ fontSize: 11, color: "var(--base)" }}>Auto-decline on failure</div>
          </div>
        </div>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span className="badge badge-high" style={{ fontSize: 14, padding: "4px 10px" }}>
            {severityCounts.high}
          </span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>High Severity</div>
            <div style={{ fontSize: 11, color: "var(--base)" }}>Refer to underwriter</div>
          </div>
        </div>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span className="badge badge-medium" style={{ fontSize: 14, padding: "4px 10px" }}>
            {severityCounts.medium}
          </span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>Medium Severity</div>
            <div style={{ fontSize: 11, color: "var(--base)" }}>Advisory warning</div>
          </div>
        </div>
      </div>

      {/* Category Filter */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
        {CATEGORIES.map((c) => (
          <button
            key={c.key}
            className={`btn btn-sm ${category === c.key ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setCategory(c.key)}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Rules List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {filtered.map((rule) => (
          <div key={rule.rule_id} className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ fontSize: 20 }}>{CATEGORY_ICONS[rule.category] || "📌"}</span>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{
                      fontFamily: "monospace", fontSize: 11, fontWeight: 700,
                      color: "var(--primary)", background: "var(--primary-lighter)",
                      padding: "1px 6px", borderRadius: 3,
                    }}>
                      {rule.rule_id}
                    </span>
                    <span style={{ fontSize: 14, fontWeight: 600 }}>{rule.rule_name}</span>
                  </div>
                  <div style={{ fontSize: 13, color: "var(--base-dark)", lineHeight: 1.5 }}>
                    {rule.description}
                  </div>
                </div>
              </div>
              <span className={`badge badge-${rule.severity}`} style={{ flexShrink: 0 }}>
                {rule.severity}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
