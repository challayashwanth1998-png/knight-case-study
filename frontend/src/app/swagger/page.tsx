"use client";

import { useState, useEffect } from "react";

const METHOD_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  get: { bg: "#EFF6FF", text: "#1D4ED8", border: "#93C5FD" },
  post: { bg: "#F0FDF4", text: "#15803D", border: "#86EFAC" },
  put: { bg: "#FFFBEB", text: "#B45309", border: "#FDE68A" },
  patch: { bg: "#FFF7ED", text: "#C2410C", border: "#FDBA74" },
  delete: { bg: "#FEF2F2", text: "#B91C1C", border: "#FECACA" },
};

interface Endpoint {
  path: string;
  method: string;
  summary: string;
  description: string;
  tags: string[];
  parameters: any[];
  requestBody: any;
  responses: Record<string, any>;
}

export default function SwaggerPage() {
  const [spec, setSpec] = useState<any>(null);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterTag, setFilterTag] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const backendUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
    fetch(`${backendUrl}/openapi.json`)
      .then((r) => r.json())
      .then((data) => {
        setSpec(data);
        const eps: Endpoint[] = [];
        for (const [path, methods] of Object.entries(data.paths || {})) {
          for (const [method, detail] of Object.entries(methods as any)) {
            if (["get", "post", "put", "patch", "delete"].includes(method)) {
              eps.push({
                path,
                method,
                summary: (detail as any).summary || "",
                description: (detail as any).description || "",
                tags: (detail as any).tags || ["Other"],
                parameters: (detail as any).parameters || [],
                requestBody: (detail as any).requestBody || null,
                responses: (detail as any).responses || {},
              });
            }
          }
        }
        setEndpoints(eps);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const allTags = [...new Set(endpoints.flatMap((e) => e.tags))].sort();

  const filtered = endpoints.filter((e) => {
    if (filterTag !== "all" && !e.tags.includes(filterTag)) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        e.path.toLowerCase().includes(q) ||
        e.summary.toLowerCase().includes(q) ||
        e.method.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const resolveRef = (ref: string) => {
    if (!spec || !ref) return null;
    const parts = ref.replace("#/", "").split("/");
    let obj: any = spec;
    for (const p of parts) obj = obj?.[p];
    return obj;
  };

  const renderSchema = (schema: any, depth = 0): React.ReactNode => {
    if (!schema) return null;
    if (schema.$ref) {
      schema = resolveRef(schema.$ref);
      if (!schema) return <span style={{ color: "#94A3B8" }}>unknown</span>;
    }
    if (schema.allOf) {
      const merged: any = {};
      for (const s of schema.allOf) {
        const resolved = s.$ref ? resolveRef(s.$ref) : s;
        if (resolved?.properties) Object.assign(merged, resolved.properties);
      }
      return renderSchema({ type: "object", properties: merged }, depth);
    }

    if (schema.type === "object" && schema.properties) {
      return (
        <div style={{ marginLeft: depth > 0 ? 16 : 0 }}>
          {Object.entries(schema.properties).map(([key, val]: any) => {
            const propSchema = val.$ref ? resolveRef(val.$ref) : val;
            const type = propSchema?.type || (val.$ref ? "object" : "any");
            const required = schema.required?.includes(key);
            return (
              <div key={key} style={{
                display: "flex", gap: 8, alignItems: "baseline",
                padding: "3px 0", fontSize: 12,
              }}>
                <code style={{ color: "#1F2937", fontWeight: 600 }}>{key}</code>
                <span style={{
                  fontSize: 10, padding: "1px 6px", borderRadius: 3,
                  background: "#F1F5F9", color: "#475569",
                }}>{type}</span>
                {required && (
                  <span style={{ fontSize: 9, color: "#DC2626", fontWeight: 600 }}>required</span>
                )}
                {propSchema?.description && (
                  <span style={{ fontSize: 11, color: "#94A3B8" }}>{propSchema.description}</span>
                )}
              </div>
            );
          })}
        </div>
      );
    }
    if (schema.type === "array" && schema.items) {
      return (
        <div>
          <span style={{ fontSize: 11, color: "#475569" }}>array of:</span>
          {renderSchema(schema.items, depth + 1)}
        </div>
      );
    }
    return <span style={{ fontSize: 11, color: "#64748B" }}>{schema.type || "any"}</span>;
  };

  if (loading) return <div className="page-container"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1>🔌 API Documentation</h1>
            <p className="page-subtitle">
              {spec?.info?.title || "Knight Insurance API"} — v{spec?.info?.version || "1.0"} — {endpoints.length} endpoints
            </p>
          </div>
          <a
            href={`${typeof window !== "undefined" ? `${window.location.protocol}//${window.location.hostname}:8000` : ""}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: 12, padding: "6px 14px", borderRadius: 6,
              background: "#3B82F6", color: "white", textDecoration: "none",
              fontWeight: 600,
            }}
          >
            Open Swagger UI ↗
          </a>
        </div>
      </div>

      {/* Base URL */}
      <div style={{
        padding: "10px 16px", background: "#F8FAFC", border: "1px solid #E2E8F0",
        borderRadius: 8, marginBottom: 16, display: "flex", alignItems: "center", gap: 10,
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: "#64748B" }}>BASE URL</span>
        <code style={{
          fontSize: 13, color: "#1F2937", background: "white",
          padding: "4px 10px", borderRadius: 4, border: "1px solid #E2E8F0",
        }}>
          {typeof window !== "undefined" ? `${window.location.protocol}//${window.location.hostname}:8000` : ""}
        </code>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
        <input
          type="text"
          className="logs-search"
          placeholder="Search endpoints..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ flex: 1, minWidth: 200 }}
        />
        <select
          className="logs-select"
          value={filterTag}
          onChange={(e) => setFilterTag(e.target.value)}
        >
          <option value="all">All Tags ({endpoints.length})</option>
          {allTags.map((t) => (
            <option key={t} value={t}>{t} ({endpoints.filter(e => e.tags.includes(t)).length})</option>
          ))}
        </select>
        <span style={{ display: "flex", alignItems: "center", fontSize: 12, color: "#64748B" }}>
          {filtered.length} endpoint{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Method summary */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["get", "post", "put", "delete"].map((m) => {
          const count = endpoints.filter((e) => e.method === m).length;
          if (count === 0) return null;
          const c = METHOD_COLORS[m];
          return (
            <div key={m} style={{
              padding: "4px 12px", borderRadius: 6,
              background: c.bg, border: `1px solid ${c.border}`,
              fontSize: 11, fontWeight: 700, color: c.text,
            }}>
              {m.toUpperCase()} ({count})
            </div>
          );
        })}
      </div>

      {/* Endpoints */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {filtered.map((ep) => {
          const id = `${ep.method}-${ep.path}`;
          const expanded = expandedId === id;
          const mc = METHOD_COLORS[ep.method] || METHOD_COLORS.get;

          return (
            <div key={id} style={{
              border: `1px solid ${expanded ? mc.border : "#E2E8F0"}`,
              borderRadius: 8, overflow: "hidden",
              transition: "all 0.2s ease",
            }}>
              {/* Header */}
              <div
                onClick={() => setExpandedId(expanded ? null : id)}
                style={{
                  display: "flex", alignItems: "center", gap: 12,
                  padding: "10px 16px", cursor: "pointer",
                  background: expanded ? mc.bg : "white",
                  transition: "background 0.15s ease",
                }}
              >
                <span style={{
                  fontSize: 11, fontWeight: 800, letterSpacing: "0.5px",
                  padding: "3px 10px", borderRadius: 4,
                  background: mc.bg, color: mc.text,
                  border: `1px solid ${mc.border}`,
                  minWidth: 55, textAlign: "center",
                }}>
                  {ep.method.toUpperCase()}
                </span>
                <code style={{ fontSize: 13, fontWeight: 600, color: "#1F2937" }}>
                  {ep.path}
                </code>
                <span style={{ fontSize: 12, color: "#64748B", flex: 1 }}>
                  {ep.summary}
                </span>
                <span style={{ fontSize: 11, color: "#94A3B8", transform: expanded ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
                  ▼
                </span>
              </div>

              {/* Expanded Detail */}
              {expanded && (
                <div style={{ padding: "16px 20px", borderTop: `1px solid ${mc.border}`, background: "#FAFBFC" }}>
                  {ep.description && (
                    <p style={{ fontSize: 13, color: "#475569", marginBottom: 16, lineHeight: 1.5 }}>
                      {ep.description}
                    </p>
                  )}

                  {/* Parameters */}
                  {ep.parameters.length > 0 && (
                    <div style={{ marginBottom: 16 }}>
                      <div style={{
                        fontSize: 11, fontWeight: 700, color: "#1F2937",
                        textTransform: "uppercase", letterSpacing: "0.5px",
                        marginBottom: 8,
                      }}>
                        Parameters
                      </div>
                      <div style={{
                        background: "white", borderRadius: 6,
                        border: "1px solid #E2E8F0", overflow: "hidden",
                      }}>
                        {ep.parameters.map((p: any, i: number) => (
                          <div key={i} style={{
                            display: "flex", gap: 10, alignItems: "center",
                            padding: "8px 12px",
                            borderBottom: i < ep.parameters.length - 1 ? "1px solid #F1F5F9" : "none",
                          }}>
                            <code style={{ fontSize: 12, fontWeight: 600, color: "#1F2937" }}>
                              {p.name}
                            </code>
                            <span style={{
                              fontSize: 10, padding: "1px 6px", borderRadius: 3,
                              background: "#F1F5F9", color: "#475569",
                            }}>
                              {p.in} • {p.schema?.type || "string"}
                            </span>
                            {p.required && (
                              <span style={{ fontSize: 9, color: "#DC2626", fontWeight: 600 }}>required</span>
                            )}
                            {p.description && (
                              <span style={{ fontSize: 11, color: "#94A3B8" }}>{p.description}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Request Body */}
                  {ep.requestBody && (
                    <div style={{ marginBottom: 16 }}>
                      <div style={{
                        fontSize: 11, fontWeight: 700, color: "#1F2937",
                        textTransform: "uppercase", letterSpacing: "0.5px",
                        marginBottom: 8,
                      }}>
                        Request Body
                      </div>
                      <div style={{
                        background: "white", borderRadius: 6,
                        border: "1px solid #E2E8F0", padding: "10px 12px",
                      }}>
                        {Object.entries(ep.requestBody.content || {}).map(([contentType, schema]: any) => (
                          <div key={contentType}>
                            <span style={{
                              fontSize: 10, padding: "2px 8px", borderRadius: 3,
                              background: "#EFF6FF", color: "#1D4ED8", fontWeight: 600,
                            }}>
                              {contentType}
                            </span>
                            <div style={{ marginTop: 8 }}>
                              {renderSchema(schema.schema)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Responses */}
                  <div>
                    <div style={{
                      fontSize: 11, fontWeight: 700, color: "#1F2937",
                      textTransform: "uppercase", letterSpacing: "0.5px",
                      marginBottom: 8,
                    }}>
                      Responses
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {Object.entries(ep.responses).map(([code, detail]: any) => {
                        const isSuccess = code.startsWith("2");
                        return (
                          <div key={code} style={{
                            display: "flex", gap: 10, alignItems: "flex-start",
                            padding: "8px 12px", background: "white",
                            borderRadius: 6, border: "1px solid #E2E8F0",
                          }}>
                            <span style={{
                              fontSize: 11, fontWeight: 700, padding: "2px 8px",
                              borderRadius: 4, minWidth: 32, textAlign: "center",
                              background: isSuccess ? "#F0FDF4" : "#FEF2F2",
                              color: isSuccess ? "#15803D" : "#B91C1C",
                              border: `1px solid ${isSuccess ? "#BBF7D0" : "#FECACA"}`,
                            }}>
                              {code}
                            </span>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 12, color: "#475569" }}>
                                {detail.description || "Successful response"}
                              </div>
                              {detail.content && Object.entries(detail.content).map(([ct, s]: any) => (
                                <div key={ct} style={{ marginTop: 6 }}>
                                  {renderSchema(s.schema)}
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div style={{ textAlign: "center", padding: 40, color: "#94A3B8" }}>
          No endpoints match your search.
        </div>
      )}
    </div>
  );
}
