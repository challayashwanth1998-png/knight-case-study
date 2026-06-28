"use client";

import { useState, useMemo } from "react";
import type { SubmissionDetail } from "@/types";

interface Props {
  submission: SubmissionDetail;
}

export default function EmailTab({ submission }: Props) {
  const analysis = submission.analysis;
  const completeness = analysis?.completeness_report;
  const rules = submission.rules || [];

  const defaultTo = submission.email_from || "";
  const defaultSubject = `Re: ${submission.email_subject || `Submission ${submission.id.slice(0, 8)}`} — Additional Information Required`;

  // Build list of missing/needed items
  const neededItems = useMemo(() => {
    const items: { label: string; reason: string; priority: "required" | "recommended" }[] = [];

    // From completeness checklist
    if (completeness?.checklist) {
      for (const [, v] of Object.entries(completeness.checklist) as any) {
        if (!v.present && v.required) {
          items.push({ label: v.label, reason: "Not found in submission", priority: "required" });
        }
      }
    }

    // From failed rules
    for (const rule of rules) {
      if (rule.result === "FAIL" && rule.category === "submission") {
        const alreadyListed = items.some(i =>
          i.label.toLowerCase().includes(rule.rule_name.toLowerCase().split(":")[0]) ||
          (rule.details || "").toLowerCase().includes(i.label.toLowerCase().split("(")[0].trim())
        );
        if (!alreadyListed) {
          items.push({ label: rule.rule_name, reason: rule.details, priority: "required" });
        }
      }
    }

    // From warning rules
    for (const rule of rules) {
      if (rule.result === "WARNING") {
        items.push({ label: rule.rule_name, reason: rule.details, priority: "recommended" });
      }
    }

    return items;
  }, [completeness, rules]);

  const requiredItems = neededItems.filter(i => i.priority === "required");
  const recommendedItems = neededItems.filter(i => i.priority === "recommended");

  const buildBody = () => {
    const lines: string[] = [
      `Dear ${defaultTo ? defaultTo.split("@")[0].replace(/[._]/g, " ") : "Applicant"},`,
      "",
      `Thank you for your insurance submission. After our initial review, we have identified the following items that are needed to complete the evaluation of this account.`,
      "",
    ];

    if (requiredItems.length > 0) {
      lines.push("REQUIRED DOCUMENTS / INFORMATION:");
      lines.push("─".repeat(40));
      requiredItems.forEach((item, i) => {
        lines.push(`${i + 1}. ${item.label}`);
        lines.push(`   → ${item.reason}`);
        lines.push("");
      });
    }

    if (recommendedItems.length > 0) {
      lines.push("");
      lines.push("ADDITIONAL ITEMS FOR REVIEW:");
      lines.push("─".repeat(40));
      recommendedItems.forEach((item, i) => {
        lines.push(`${i + 1}. ${item.label}`);
        lines.push(`   → ${item.reason}`);
        lines.push("");
      });
    }

    if (neededItems.length === 0) {
      lines.push("Your submission appears complete. We are proceeding with our review and will follow up shortly with our determination.");
      lines.push("");
    }

    lines.push("");
    lines.push("Please provide the above items at your earliest convenience so we can continue processing your application. If you have any questions, please do not hesitate to contact our underwriting team.");
    lines.push("");
    lines.push("Best regards,");
    lines.push("Knight Specialty Insurance Group");
    lines.push("Underwriting Department");

    return lines.join("\n");
  };

  const [to, setTo] = useState(defaultTo);
  const [subject, setSubject] = useState(defaultSubject);
  const [body, setBody] = useState(buildBody);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const full = `To: ${to}\nSubject: ${subject}\n\n${body}`;
    navigator.clipboard.writeText(full);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleMailto = () => {
    const mailto = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.open(mailto);
  };

  const fieldStyle: React.CSSProperties = {
    width: "100%", padding: "8px 12px", border: "1px solid var(--border)",
    borderRadius: 6, fontSize: 13, fontFamily: "inherit", outline: "none",
    background: "var(--surface)",
  };

  return (
    <div className="card" style={{ padding: 0, overflow: "hidden" }}>
      {/* Summary bar */}
      {neededItems.length > 0 && (
        <div style={{
          padding: "10px 20px", background: "#FEF3C7", borderBottom: "1px solid #FDE68A",
          display: "flex", alignItems: "center", gap: 8, fontSize: 12,
        }}>
          <span style={{ fontWeight: 700 }}>⚠️ {requiredItems.length} required</span>
          {recommendedItems.length > 0 && (
            <span style={{ color: "#92400E" }}>• {recommendedItems.length} recommended</span>
          )}
          <span style={{ color: "#92400E" }}>items to request from submitter</span>
        </div>
      )}

      {/* Email Header */}
      <div style={{
        background: "var(--surface-alt)", borderBottom: "1px solid var(--border)",
        padding: "16px 20px",
      }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)", marginBottom: 12 }}>
          📧 Request for Additional Information
        </div>

        {/* To */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "var(--base)", width: 60, flexShrink: 0 }}>To:</label>
          <input
            type="email"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            placeholder="submitter@example.com"
            style={fieldStyle}
          />
        </div>

        {/* Subject */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "var(--base)", width: 60, flexShrink: 0 }}>Subject:</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            style={fieldStyle}
          />
        </div>
      </div>

      {/* Email Body */}
      <div style={{ padding: "16px 20px" }}>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={20}
          style={{
            ...fieldStyle,
            resize: "vertical",
            lineHeight: 1.7,
            minHeight: 350,
          }}
        />
      </div>

      {/* Actions */}
      <div style={{
        padding: "12px 20px", borderTop: "1px solid var(--border)",
        display: "flex", gap: 8, justifyContent: "flex-end", background: "var(--surface-alt)",
      }}>
        <button className="btn btn-secondary" onClick={handleCopy} style={{ fontSize: 12 }}>
          {copied ? "✓ Copied!" : "📋 Copy to Clipboard"}
        </button>
        <button className="btn btn-primary" onClick={handleMailto} style={{ fontSize: 12 }}>
          ✉️ Open in Mail Client
        </button>
      </div>
    </div>
  );
}
