"use client";

import type { AuditLog } from "@/types";

interface Props {
  logs: AuditLog[];
}

export default function AuditTab({ logs }: Props) {
  return (
    <div style={{ position: "relative", paddingLeft: 20 }}>
      <div
        style={{
          position: "absolute", left: 5, top: 0, bottom: 0,
          width: 1.5, background: "#E5E7EB",
        }}
      />
      {logs.map((log) => (
        <div key={log.id} style={{ position: "relative", marginBottom: 16 }}>
          <div
            style={{
              position: "absolute", left: -17, top: 3,
              width: 8, height: 8, borderRadius: "50%",
              background: "#1F2937",
            }}
          />
          <div style={{ fontSize: 11, color: "#9CA3AF", marginBottom: 2 }}>
            {new Date(log.timestamp).toLocaleString()}
          </div>
          <div style={{ fontWeight: 500, fontSize: 13 }}>
            {log.action.replace(/_/g, " ")}
          </div>
          {log.details && (
            <div style={{ fontSize: 12, color: "#6B7280", marginTop: 1 }}>
              {log.details}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
