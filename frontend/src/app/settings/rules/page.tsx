"use client";

import { useState, useEffect, useCallback } from "react";
import { getRulesConfig, updateRuleConfig, resetRulesConfig } from "@/lib/api";
import type { RuleConfig } from "@/lib/api";

const CATEGORIES = [
  { key: "all", label: "All Rules", icon: "📌" },
  { key: "eligibility", label: "Eligibility", icon: "🎯" },
  { key: "driver", label: "Driver", icon: "🚛" },
  { key: "exposure", label: "Exposure", icon: "⚠️" },
  { key: "submission", label: "Submission", icon: "📋" },
  { key: "ifta", label: "IFTA", icon: "⛽" },
  { key: "selective", label: "Selective", icon: "🔍" },
];

const SEVERITY_OPTIONS = ["critical", "high", "medium", "low", "info"];

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#DC2626",
  high: "#EA580C",
  medium: "#D97706",
  low: "#2563EB",
  info: "#6B7280",
};

export default function RulesConfigPage() {
  const [rules, setRules] = useState<RuleConfig[]>([]);
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const loadRules = useCallback(() => {
    getRulesConfig().then(setRules).catch(console.error);
  }, []);

  useEffect(() => { loadRules(); }, [loadRules]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const handleToggle = async (ruleId: string, enabled: boolean) => {
    setSaving(ruleId);
    try {
      await updateRuleConfig(ruleId, { enabled });
      setRules((prev) =>
        prev.map((r) => (r.rule_id === ruleId ? { ...r, enabled } : r))
      );
      showToast(`${ruleId} ${enabled ? "enabled" : "disabled"}`);
    } catch (e) {
      console.error(e);
    }
    setSaving(null);
  };

  const handleSeverity = async (ruleId: string, severity: string) => {
    setSaving(ruleId);
    try {
      await updateRuleConfig(ruleId, { severity });
      setRules((prev) =>
        prev.map((r) =>
          r.rule_id === ruleId ? { ...r, severity_override: severity, severity } : r
        )
      );
      showToast(`${ruleId} severity → ${severity}`);
    } catch (e) {
      console.error(e);
    }
    setSaving(null);
  };

  const handleReset = async () => {
    if (!confirm("Reset all rules to default configuration?")) return;
    await resetRulesConfig();
    loadRules();
    showToast("All rules reset to defaults");
  };

  const filtered = rules.filter((r) => {
    const matchCat = category === "all" || r.category === category;
    const matchSearch =
      !search ||
      r.rule_id.toLowerCase().includes(search.toLowerCase()) ||
      r.rule_name.toLowerCase().includes(search.toLowerCase()) ||
      r.description.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  const enabledCount = filtered.filter((r) => r.enabled).length;
  const disabledCount = filtered.filter((r) => !r.enabled).length;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Toast */}
      {toast && (
        <div
          style={{
            position: "fixed",
            top: 20,
            right: 20,
            zIndex: 1000,
            background: "#059669",
            color: "white",
            padding: "10px 20px",
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 500,
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            animation: "fadeIn 0.2s ease-out",
          }}
        >
          ✅ {toast}
        </div>
      )}

      {/* Header */}
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">⚙️ Rules Configuration</h1>
          <p className="page-description">
            Enable, disable, or adjust the severity of underwriting rules. Changes apply to new submissions.
          </p>
        </div>
        <button
          className="btn btn-sm"
          onClick={handleReset}
          style={{
            background: "var(--red-soft)",
            color: "#DC2626",
            border: "1px solid #FCA5A5",
            fontSize: 12,
            marginTop: 4,
          }}
        >
          ↺ Reset All to Defaults
        </button>
      </div>

      {/* Stats */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 12, padding: 14 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: "#DCFCE7", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>✓</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>{enabledCount}</div>
            <div style={{ fontSize: 11, color: "var(--base)" }}>Active Rules</div>
          </div>
        </div>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 12, padding: 14 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: "#FEF2F2", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>✕</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>{disabledCount}</div>
            <div style={{ fontSize: 11, color: "var(--base)" }}>Disabled Rules</div>
          </div>
        </div>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 12, padding: 14 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: "#EFF6FF", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>📊</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>{rules.length}</div>
            <div style={{ fontSize: 11, color: "var(--base)" }}>Total Rules</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 4, flex: 1 }}>
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              className={`btn btn-sm ${category === c.key ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setCategory(c.key)}
              style={{ fontSize: 11 }}
            >
              {c.icon} {c.label}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Search rules..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            padding: "6px 12px",
            fontSize: 12,
            borderRadius: 6,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            width: 200,
            outline: "none",
          }}
        />
      </div>

      {/* Rules List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {filtered.map((rule) => {
          const currentSeverity = rule.severity_override || rule.severity;
          const isModified = rule.severity_override && rule.severity_override !== rule.original_severity;

          return (
            <div
              key={rule.rule_id}
              className="card"
              style={{
                padding: "14px 18px",
                opacity: rule.enabled ? 1 : 0.5,
                transition: "opacity 0.2s",
                borderLeft: `3px solid ${rule.enabled ? SEVERITY_COLORS[currentSeverity] || "#ccc" : "#D1D5DB"}`,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
                {/* Left: Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span
                      style={{
                        fontFamily: "monospace",
                        fontSize: 10,
                        fontWeight: 700,
                        color: "var(--primary)",
                        background: "var(--primary-lighter)",
                        padding: "1px 6px",
                        borderRadius: 3,
                      }}
                    >
                      {rule.rule_id}
                    </span>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{rule.rule_name}</span>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "1px 6px",
                        borderRadius: 3,
                        background: "var(--bg)",
                        color: "var(--base)",
                        textTransform: "capitalize",
                      }}
                    >
                      {rule.category}
                    </span>
                    {isModified && (
                      <span
                        style={{
                          fontSize: 9,
                          padding: "1px 5px",
                          borderRadius: 3,
                          background: "#FEF3C7",
                          color: "#92400E",
                          fontWeight: 600,
                        }}
                      >
                        MODIFIED
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--base-dark)", lineHeight: 1.45 }}>
                    {rule.description}
                  </div>
                </div>

                {/* Right: Controls */}
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                  {/* Severity Dropdown */}
                  <select
                    value={currentSeverity}
                    onChange={(e) => handleSeverity(rule.rule_id, e.target.value)}
                    disabled={!rule.enabled || saving === rule.rule_id}
                    style={{
                      fontSize: 11,
                      padding: "4px 8px",
                      borderRadius: 4,
                      border: `1px solid ${SEVERITY_COLORS[currentSeverity] || "#D1D5DB"}`,
                      color: SEVERITY_COLORS[currentSeverity] || "#333",
                      fontWeight: 600,
                      background: "white",
                      cursor: rule.enabled ? "pointer" : "not-allowed",
                      textTransform: "capitalize",
                    }}
                  >
                    {SEVERITY_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>

                  {/* Toggle Switch */}
                  <label
                    style={{
                      position: "relative",
                      display: "inline-block",
                      width: 40,
                      height: 22,
                      cursor: saving === rule.rule_id ? "wait" : "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={rule.enabled}
                      onChange={(e) => handleToggle(rule.rule_id, e.target.checked)}
                      disabled={saving === rule.rule_id}
                      style={{ opacity: 0, width: 0, height: 0 }}
                    />
                    <span
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: rule.enabled ? "#059669" : "#D1D5DB",
                        borderRadius: 22,
                        transition: "background 0.2s",
                      }}
                    >
                      <span
                        style={{
                          position: "absolute",
                          content: '""',
                          height: 16,
                          width: 16,
                          left: rule.enabled ? 20 : 3,
                          bottom: 3,
                          backgroundColor: "white",
                          borderRadius: "50%",
                          transition: "left 0.2s",
                          boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
                        }}
                      />
                    </span>
                  </label>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 40, color: "var(--base)" }}>
          No rules match your filter.
        </div>
      )}
    </div>
  );
}
