"use client";

import type { AnalysisResult } from "@/types";

interface Props { analysis: AnalysisResult | null; }

export default function ExtractedDataTab({ analysis }: Props) {
  if (!analysis) return <div className="card" style={{ color: "#9CA3AF" }}>No data yet.</div>;

  const biz = analysis.unified_business_info as Record<string, unknown> | null;
  const drivers = analysis.unified_drivers as Array<Record<string, unknown>> | null;
  const vehicles = analysis.unified_vehicles as Array<Record<string, unknown>> | null;

  return (
    <div style={{ display: "grid", gap: 16 }}>
      {biz && Object.keys(biz).length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>Business Information</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 8 }}>
            {Object.entries(biz).filter(([, v]) => v != null && typeof v !== "object").map(([k, v]) => (
              <div key={k} style={{ padding: "8px 10px", background: "#F9FAFB", borderRadius: 6 }}>
                <div style={{ fontSize: 10, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  {k.replace(/_/g, " ")}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, marginTop: 2 }}>{String(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {drivers && drivers.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>Drivers ({drivers.length})</h3>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr><th>#</th><th>Name</th><th>DOB</th><th>Age</th><th>License</th><th>State</th><th>Exp</th></tr>
              </thead>
              <tbody>
                {drivers.map((d, i) => (
                  <tr key={i}>
                    <td>{(d.number as number) || i + 1}</td>
                    <td style={{ fontWeight: 500 }}>{d.name as string}</td>
                    <td>{(d.date_of_birth as string)?.slice(0, 10)}</td>
                    <td>{d.age as number}</td>
                    <td style={{ fontFamily: "monospace", fontSize: 12 }}>{d.license_number as string}</td>
                    <td>{d.license_state as string}</td>
                    <td>{d.years_experience as string}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {vehicles && vehicles.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>Vehicles ({vehicles.length})</h3>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr><th>Year</th><th>Make</th><th>Model</th><th>VIN</th><th>Type</th></tr>
              </thead>
              <tbody>
                {vehicles.map((v, i) => (
                  <tr key={i}>
                    <td>{v.year as number}</td>
                    <td>{v.make as string}</td>
                    <td>{v.model as string}</td>
                    <td style={{ fontFamily: "monospace", fontSize: 11 }}>{v.vin as string}</td>
                    <td>{v.vehicle_type as string}</td>
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
