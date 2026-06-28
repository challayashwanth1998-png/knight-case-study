"use client";

export default function ApiDocsPage() {
  const API_SECTIONS = [
    {
      title: "Submission Lifecycle",
      endpoints: [
        { method: "POST", path: "/api/submissions/upload", desc: "Upload documents to create a new submission", params: "files: File[] (multipart), email_from?, email_subject?, email_body?", returns: "SubmissionResponse" },
        { method: "POST", path: "/api/submissions/{id}/process", desc: "Trigger the AI processing pipeline", params: "submission_id: string", returns: "{ status, submission_id }" },
        { method: "GET", path: "/api/submissions", desc: "List all submissions", params: "none", returns: "SubmissionResponse[]" },
        { method: "GET", path: "/api/submissions/{id}", desc: "Get full submission detail with documents, rules, analysis, audit log", params: "submission_id: string", returns: "SubmissionDetailResponse" },
        { method: "DELETE", path: "/api/submissions/{id}", desc: "Delete a submission and its files", params: "submission_id: string", returns: "{ status: 'deleted' }" },
      ],
    },
    {
      title: "Analytics & Monitoring",
      endpoints: [
        { method: "GET", path: "/api/submissions/stats", desc: "Dashboard statistics (counts by status/decision)", params: "none", returns: "DashboardStats" },
        { method: "GET", path: "/api/submissions/analytics", desc: "Rich analytics: processing times, AI costs, rule stats, timeline", params: "none", returns: "AnalyticsResponse" },
        { method: "GET", path: "/api/submissions/logs", desc: "Cross-submission audit trail", params: "limit?: number (default 200)", returns: "AuditLogEntry[]" },
        { method: "GET", path: "/api/submissions/health", desc: "System health: database, AI service, storage, API status", params: "none", returns: "HealthResponse" },
      ],
    },
    {
      title: "Documents",
      endpoints: [
        { method: "GET", path: "/api/submissions/{id}/documents/{docId}/download", desc: "Download original document file", params: "submission_id, document_id", returns: "FileResponse" },
      ],
    },
    {
      title: "Rules Configuration",
      endpoints: [
        { method: "GET", path: "/api/submissions/meta/rules", desc: "List all business rule definitions", params: "none", returns: "RuleDefinition[]" },
        { method: "GET", path: "/api/submissions/meta/rules-config", desc: "List rules with configuration (enabled, severity overrides)", params: "none", returns: "RuleConfig[]" },
        { method: "PUT", path: "/api/submissions/meta/rules-config/{ruleId}", desc: "Update a rule's enabled state or severity", params: "{ enabled?: boolean, severity?: string }", returns: "{ rule_id, ...override }" },
        { method: "POST", path: "/api/submissions/meta/rules-config/reset", desc: "Reset all rules to default configuration", params: "none", returns: "{ status: 'reset' }" },
      ],
    },
  ];

  const METHOD_COLORS: Record<string, { bg: string; color: string }> = {
    GET: { bg: "#ECFDF5", color: "#059669" },
    POST: { bg: "#EFF6FF", color: "#2563EB" },
    PUT: { bg: "#FFFBEB", color: "#D97706" },
    DELETE: { bg: "#FEF2F2", color: "#DC2626" },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📡 API Reference</h1>
        <p className="page-subtitle">
          RESTful API documentation for the Knight Insurance underwriting platform.
          Base URL: <code style={{ background: "#F1F5F9", padding: "2px 6px", borderRadius: 4, fontSize: 12 }}>
            http://&lt;host&gt;:8000
          </code>
        </p>
      </div>

      {/* Quick stats */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        {Object.entries(
          API_SECTIONS.flatMap(s => s.endpoints).reduce((acc, e) => {
            acc[e.method] = (acc[e.method] || 0) + 1;
            return acc;
          }, {} as Record<string, number>)
        ).map(([method, count]) => (
          <span
            key={method}
            style={{
              padding: "4px 12px", borderRadius: 6, fontSize: 12, fontWeight: 600,
              background: METHOD_COLORS[method]?.bg || "#F1F5F9",
              color: METHOD_COLORS[method]?.color || "#64748B",
            }}
          >
            {method} × {count}
          </span>
        ))}
        <span style={{ fontSize: 12, color: "#94A3B8", alignSelf: "center" }}>
          {API_SECTIONS.flatMap(s => s.endpoints).length} endpoints total
        </span>
      </div>

      {API_SECTIONS.map((section) => (
        <div key={section.title} style={{ marginBottom: 28 }}>
          <h2 style={{
            fontSize: 14, fontWeight: 700, color: "#0F172A",
            borderBottom: "2px solid #E2E8F0", paddingBottom: 8, marginBottom: 12,
          }}>
            {section.title}
          </h2>
          <div style={{ display: "grid", gap: 8 }}>
            {section.endpoints.map((ep, i) => {
              const mc = METHOD_COLORS[ep.method] || { bg: "#F1F5F9", color: "#64748B" };
              return (
                <div
                  key={i}
                  className="card"
                  style={{ padding: "14px 18px", borderLeft: `3px solid ${mc.color}` }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 700, padding: "3px 8px",
                      borderRadius: 4, background: mc.bg, color: mc.color,
                      fontFamily: "monospace", letterSpacing: "0.5px",
                    }}>
                      {ep.method}
                    </span>
                    <code style={{ fontSize: 13, fontWeight: 600, color: "#1E293B" }}>
                      {ep.path}
                    </code>
                  </div>
                  <p style={{ fontSize: 12, color: "#64748B", margin: "0 0 8px" }}>
                    {ep.desc}
                  </p>
                  <div style={{ display: "flex", gap: 20, fontSize: 11 }}>
                    <div>
                      <span style={{ color: "#94A3B8", fontWeight: 500 }}>Params:</span>{" "}
                      <span style={{ color: "#475569" }}>{ep.params}</span>
                    </div>
                    <div>
                      <span style={{ color: "#94A3B8", fontWeight: 500 }}>Returns:</span>{" "}
                      <code style={{ fontSize: 11, color: "#2563EB" }}>{ep.returns}</code>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Pipeline section */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{
          fontSize: 14, fontWeight: 700, color: "#0F172A",
          borderBottom: "2px solid #E2E8F0", paddingBottom: 8, marginBottom: 12,
        }}>
          Pipeline Steps
        </h2>
        <div className="card" style={{ padding: 18 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 8 }}>
            {[
              { step: 1, name: "Text Extract", icon: "📄", desc: "PDF/Excel/Image OCR" },
              { step: 2, name: "Classify", icon: "🏷️", desc: "Content-based (not filename)" },
              { step: 3, name: "Data Extract", icon: "🔍", desc: "Structured data from docs" },
              { step: 4, name: "AI Analysis", icon: "🧠", desc: "4 parallel Gemini calls" },
              { step: 5, name: "Rules Engine", icon: "⚖️", desc: "21+ underwriting rules" },
              { step: 6, name: "Decision", icon: "✅", desc: "Accept/Decline/Refer" },
            ].map((s) => (
              <div key={s.step} style={{
                textAlign: "center", padding: 12, background: "#F8FAFC", borderRadius: 8,
              }}>
                <div style={{ fontSize: 22 }}>{s.icon}</div>
                <div style={{ fontSize: 11, fontWeight: 600, marginTop: 4 }}>{s.name}</div>
                <div style={{ fontSize: 9, color: "#94A3B8", marginTop: 2 }}>{s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
