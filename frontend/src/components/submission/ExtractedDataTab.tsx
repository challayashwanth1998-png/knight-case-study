"use client";

import type { AnalysisResult } from "@/types";

interface Props { analysis: AnalysisResult | null; }

export default function ExtractedDataTab({ analysis }: Props) {
  if (!analysis) return <div className="card" style={{ color: "#9CA3AF" }}>No data yet.</div>;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const biz = analysis.unified_business_info as any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const drivers = analysis.unified_drivers as any[] | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const vehicles = analysis.unified_vehicles as any[] | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ifta = analysis.unified_ifta as any[] | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const completeness = analysis.completeness_report as any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const risk = analysis.risk_assessment as any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const bp = analysis.business_profile as any;
  const effectiveBiz = biz && Object.keys(biz).length > 0 ? biz : bp;

  // Helper: render nested objects (like address)
  const renderValue = (v: unknown): string => {
    if (v == null) return "—";
    if (typeof v === "object" && !Array.isArray(v)) {
      return Object.entries(v as Record<string, unknown>)
        .filter(([, val]) => val != null)
        .map(([, val]) => String(val))
        .join(", ");
    }
    return String(v);
  };

  const riskColor = (tier: string) => {
    const t = String(tier).toLowerCase();
    if (t.includes("low")) return { bg: "#ECFDF5", color: "#059669" };
    if (t.includes("moderate") || t.includes("medium")) return { bg: "#FFFBEB", color: "#D97706" };
    return { bg: "#FEF2F2", color: "#DC2626" };
  };

  return (
    <div style={{ display: "grid", gap: 16 }}>

      {/* ─── Risk Assessment Summary ─── */}
      {risk && (
        <div className="card" style={{ borderLeft: `4px solid ${riskColor(String(risk.risk_tier || "")).color}` }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>📊 Risk Assessment</h3>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
            <div style={{
              padding: "12px 20px", borderRadius: 10, textAlign: "center",
              background: riskColor(String(risk.risk_tier || "")).bg,
            }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: riskColor(String(risk.risk_tier || "")).color }}>
                {String(risk.overall_score || "—")}
              </div>
              <div style={{ fontSize: 10, fontWeight: 600, color: riskColor(String(risk.risk_tier || "")).color, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                {String(risk.risk_tier || "—")} Risk
              </div>
            </div>
            {Array.isArray(risk.factors) && (
              <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
                {(risk.factors as Array<Record<string, unknown>>).slice(0, 6).map((f, i) => (
                  <div key={i} style={{ padding: "8px 10px", background: "#F9FAFB", borderRadius: 6, fontSize: 12 }}>
                    <div style={{ fontWeight: 600, color: "#1F2937" }}>
                      {String(f.factor || "").replace(/_/g, " ")}
                      <span style={{ marginLeft: 6, color: Number(f.score) <= 3 ? "#059669" : Number(f.score) <= 6 ? "#D97706" : "#DC2626", fontWeight: 700 }}>
                        {String(f.score)}/10
                      </span>
                    </div>
                    <div style={{ fontSize: 10, color: "#6B7280", marginTop: 2, lineHeight: 1.3 }}>
                      {String(f.reasoning || "").slice(0, 80)}{String(f.reasoning || "").length > 80 ? "…" : ""}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Completeness Report ─── */}
      {completeness && (completeness as Record<string, unknown>).checklist && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>📋 Submission Completeness</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 8 }}>
            {Object.entries((completeness as Record<string, unknown>).checklist as Record<string, Record<string, unknown>>).map(([k, v]) => (
              <div key={k} style={{
                padding: "8px 12px", borderRadius: 8,
                background: v.present ? "#ECFDF5" : "#FEF2F2",
                border: `1px solid ${v.present ? "#A7F3D0" : "#FECACA"}`,
                display: "flex", alignItems: "center", gap: 8
              }}>
                <span style={{ fontSize: 16 }}>{v.present ? "✅" : "❌"}</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#1F2937" }}>{String(v.label || k.replace(/_/g, " "))}</div>
                  {v.required && <div style={{ fontSize: 9, color: "#6B7280" }}>Required</div>}
                </div>
              </div>
            ))}
          </div>
          {(completeness as Record<string, unknown>).missing_items && Array.isArray((completeness as Record<string, unknown>).missing_items) && ((completeness as Record<string, unknown>).missing_items as string[]).length > 0 && (
            <div style={{ marginTop: 10, padding: "8px 12px", background: "#FEF2F2", borderRadius: 8, fontSize: 12, color: "#DC2626" }}>
              <strong>Missing:</strong> {((completeness as Record<string, unknown>).missing_items as string[]).join(", ")}
            </div>
          )}
        </div>
      )}

      {/* ─── Business Information ─── */}
      {effectiveBiz && Object.keys(effectiveBiz).length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>🏢 Business Information</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 8 }}>
            {Object.entries(effectiveBiz).filter(([, v]) => v != null).map(([k, v]) => (
              <div key={k} style={{ padding: "8px 10px", background: "#F9FAFB", borderRadius: 6 }}>
                <div style={{ fontSize: 10, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  {k.replace(/_/g, " ")}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, marginTop: 2 }}>{renderValue(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Drivers ─── */}
      {drivers && drivers.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>👤 Drivers ({drivers.length})</h3>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th><th>Name</th><th>DOB</th><th>Age</th>
                  <th>License #</th><th>State</th><th>Class</th>
                  <th>Experience</th><th>Hired</th>
                  <th>Violations (3yr)</th><th>Accidents (3yr)</th>
                </tr>
              </thead>
              <tbody>
                {drivers.map((d, i) => {
                  const violations = Number(d.violations_3yr || d.violations || 0);
                  const accidents = Number(d.accidents_3yr || d.accidents || 0);
                  return (
                    <tr key={i}>
                      <td>{(d.number as number) || i + 1}</td>
                      <td style={{ fontWeight: 500 }}>{d.name as string}</td>
                      <td>{(d.date_of_birth as string)?.slice(0, 10)}</td>
                      <td>{d.age as string}</td>
                      <td style={{ fontFamily: "monospace", fontSize: 12 }}>{d.license_number as string}</td>
                      <td>{d.license_state as string}</td>
                      <td>{d.license_class as string || "—"}</td>
                      <td>{d.years_experience ? `${d.years_experience} yr` : d.date_of_hire ? `Since ${(d.date_of_hire as string).slice(0, 10)}` : "—"}</td>
                      <td>{d.date_of_hire ? (d.date_of_hire as string).slice(0, 10) : "—"}</td>
                      <td style={{ color: violations > 0 ? "#DC2626" : "#059669", fontWeight: 600 }}>
                        {violations}
                      </td>
                      <td style={{ color: accidents > 0 ? "#DC2626" : "#059669", fontWeight: 600 }}>
                        {accidents}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── Vehicles ─── */}
      {vehicles && vehicles.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>🚛 Vehicles ({vehicles.length})</h3>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Unit</th><th>Year</th><th>Make</th><th>Model</th>
                  <th>VIN</th><th>Type</th><th>GVW</th><th>Value</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map((v, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{v.unit_number as string || `#${i + 1}`}</td>
                    <td>{v.year as string}</td>
                    <td>{v.make as string}</td>
                    <td>{v.model as string}</td>
                    <td style={{ fontFamily: "monospace", fontSize: 11 }}>{v.vin as string}</td>
                    <td>{v.vehicle_type as string || "—"}</td>
                    <td>{v.gvw as string || "—"}</td>
                    <td style={{ fontWeight: 500 }}>{v.stated_value as string || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── IFTA Data ─── */}
      {ifta && ifta.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>⛽ IFTA Reports ({ifta.length} quarters)</h3>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Quarter</th><th>Company</th><th>IFTA License</th>
                  <th>FEIN</th><th>Total Miles</th><th>States</th>
                </tr>
              </thead>
              <tbody>
                {ifta.map((q, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{q.quarter as string}</td>
                    <td>{q.company_name as string || "—"}</td>
                    <td style={{ fontFamily: "monospace", fontSize: 12 }}>{q.ifta_license as string || "—"}</td>
                    <td style={{ fontFamily: "monospace", fontSize: 12 }}>{q.fein as string || "—"}</td>
                    <td style={{ fontWeight: 500 }}>
                      {q.total_miles ? Number(q.total_miles).toLocaleString() : 
                       q.total_distance ? Number(q.total_distance).toLocaleString() : "—"}
                    </td>
                    <td>
                      {q.state_details && Array.isArray(q.state_details) 
                        ? `${(q.state_details as Array<Record<string, unknown>>).length} states`
                        : q.states_count ? `${q.states_count} states` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
