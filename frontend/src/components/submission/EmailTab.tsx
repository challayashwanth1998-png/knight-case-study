"use client";

import { useState } from "react";
import type { SubmissionDetail } from "@/types";

interface Props {
  submission: SubmissionDetail;
}

export default function EmailTab({ submission }: Props) {
  const analysis = submission.analysis;
  const aiSummary = analysis?.summary || "";
  
  const defaultTo = submission.email_from || "";
  const defaultSubject = `Re: ${submission.email_subject || `Submission ${submission.id.slice(0, 8)}`}`;
  
  const decisionLabel = submission.overall_decision === "accept" ? "ACCEPTED" :
                        submission.overall_decision === "decline" ? "DECLINED" :
                        submission.overall_decision === "refer" ? "REFERRED FOR REVIEW" : "";

  const defaultBody = [
    `Dear ${defaultTo || "Applicant"},`,
    "",
    `Thank you for your submission. Below is a summary of our initial review:`,
    "",
    aiSummary,
    "",
    decisionLabel ? `Decision: ${decisionLabel}` : "",
    submission.decision_reason ? `Reason: ${submission.decision_reason}` : "",
    "",
    "Please do not hesitate to reach out if you have any questions.",
    "",
    "Best regards,",
    "Knight Specialty Insurance Group",
    "Underwriting Department",
  ].filter(line => line !== undefined).join("\n");

  const [to, setTo] = useState(defaultTo);
  const [subject, setSubject] = useState(defaultSubject);
  const [body, setBody] = useState(defaultBody);
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
      {/* Email Header */}
      <div style={{
        background: "var(--surface-alt)", borderBottom: "1px solid var(--border)",
        padding: "16px 20px",
      }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)", marginBottom: 12 }}>
          📧 Draft Response Email
        </div>

        {/* To */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "var(--base)", width: 60, flexShrink: 0 }}>To:</label>
          <input
            type="email"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            placeholder="recipient@example.com"
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
          rows={18}
          style={{
            ...fieldStyle,
            resize: "vertical",
            lineHeight: 1.7,
            minHeight: 300,
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
