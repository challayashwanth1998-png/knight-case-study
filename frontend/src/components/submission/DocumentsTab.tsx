"use client";

import type { SubmissionDetail } from "@/types";
import { getDocumentDownloadUrl } from "@/lib/api";

interface Props {
  submission: SubmissionDetail;
}

const TYPE_LABELS: Record<string, string> = {
  insurance_application: "Insurance Application",
  driver_list: "Driver List / Roster",
  equipment_list: "Equipment / Vehicle Schedule",
  ifta_report: "IFTA Report",
  loss_run: "Loss Run Report",
  motor_vehicle_record: "Motor Vehicle Record",
  drivers_license: "Driver's License (CDL)",
  other: "Other Document",
};

const TYPE_ICONS: Record<string, string> = {
  insurance_application: "📄",
  driver_list: "👤",
  equipment_list: "🚛",
  ifta_report: "⛽",
  loss_run: "📊",
  motor_vehicle_record: "🪪",
  drivers_license: "🪪",
  other: "📁",
};

const TYPE_COLORS: Record<string, string> = {
  insurance_application: "#2563EB",
  driver_list: "#7C3AED",
  equipment_list: "#0D9488",
  ifta_report: "#D97706",
  loss_run: "#DC2626",
  motor_vehicle_record: "#4F46E5",
  drivers_license: "#4F46E5",
  other: "#64748B",
};

const FILE_TYPE_ICONS: Record<string, string> = {
  pdf: "📕",
  xlsx: "📗",
  xls: "📗",
  image: "🖼️",
  csv: "📊",
  text: "📝",
};

function ConfidenceBadge({ value }: { value: number | null | undefined }) {
  if (value == null) return null;
  const pct = Math.round(value * 100);
  const color = pct >= 90 ? "#059669" : pct >= 70 ? "#D97706" : "#DC2626";
  return (
    <span
      style={{
        fontSize: 10, fontWeight: 600, padding: "2px 6px",
        borderRadius: 4, background: `${color}15`, color,
      }}
    >
      {pct}% confidence
    </span>
  );
}

function QualityBadge({ value }: { value: number | null | undefined }) {
  if (value == null) return null;
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "#059669" : pct >= 50 ? "#D97706" : "#DC2626";
  return (
    <span
      style={{
        fontSize: 10, fontWeight: 600, padding: "2px 6px",
        borderRadius: 4, background: `${color}15`, color,
      }}
    >
      {pct}% quality
    </span>
  );
}

export default function DocumentsTab({ submission }: Props) {
  // Group documents by type
  const grouped = submission.documents.reduce((acc, doc) => {
    const type = doc.classified_type || "other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(doc);
    return acc;
  }, {} as Record<string, typeof submission.documents>);

  const typeOrder = [
    "insurance_application", "driver_list", "equipment_list",
    "ifta_report", "loss_run", "drivers_license", "motor_vehicle_record", "other"
  ];

  const sortedTypes = typeOrder.filter(t => grouped[t]);
  // Add any types not in our order
  Object.keys(grouped).filter(t => !typeOrder.includes(t)).forEach(t => sortedTypes.push(t));

  return (
    <div>
      {/* Summary bar */}
      <div style={{
        display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap",
      }}>
        {sortedTypes.map(type => (
          <span
            key={type}
            style={{
              fontSize: 11, padding: "4px 10px", borderRadius: 6,
              background: `${TYPE_COLORS[type] || "#64748B"}10`,
              color: TYPE_COLORS[type] || "#64748B",
              fontWeight: 600, border: `1px solid ${TYPE_COLORS[type] || "#64748B"}30`,
            }}
          >
            {TYPE_ICONS[type] || "📁"} {TYPE_LABELS[type] || type} ({grouped[type].length})
          </span>
        ))}
      </div>

      {/* Grouped document cards */}
      {sortedTypes.map(type => (
        <div key={type} style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 12, fontWeight: 600, color: TYPE_COLORS[type] || "#64748B",
            marginBottom: 8, display: "flex", alignItems: "center", gap: 6,
          }}>
            <span>{TYPE_ICONS[type] || "📁"}</span>
            {TYPE_LABELS[type] || type}
          </div>
          <div style={{ display: "grid", gap: 6 }}>
            {grouped[type].map(doc => (
              <div
                key={doc.id}
                className="card"
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "12px 16px", borderLeft: `3px solid ${TYPE_COLORS[type] || "#64748B"}`,
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontWeight: 500, fontSize: 13, color: "#1F2937",
                    display: "flex", alignItems: "center", gap: 6,
                  }}>
                    <span>{FILE_TYPE_ICONS[doc.file_type || ""] || "📄"}</span>
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {doc.original_filename}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
                    <ConfidenceBadge value={doc.classification_confidence} />
                    <QualityBadge value={doc.quality_score} />
                    {doc.file_size && (
                      <span style={{ fontSize: 10, color: "#94A3B8" }}>
                        {doc.file_size > 1024 * 1024
                          ? `${(doc.file_size / (1024 * 1024)).toFixed(1)} MB`
                          : `${(doc.file_size / 1024).toFixed(0)} KB`
                        }
                      </span>
                    )}
                    <span style={{ fontSize: 10, color: "#94A3B8" }}>
                      {doc.file_type?.toUpperCase()}
                    </span>
                    {doc.processing_status && (
                      <span style={{
                        fontSize: 10, padding: "1px 5px", borderRadius: 3,
                        background: doc.processing_status === "complete" ? "#f0fdf4" : "#fef2f2",
                        color: doc.processing_status === "complete" ? "#059669" : "#DC2626",
                      }}>
                        {doc.processing_status}
                      </span>
                    )}
                  </div>
                </div>
                <a
                  href={getDocumentDownloadUrl(submission.id, doc.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                  style={{ padding: "5px 12px", fontSize: 11, flexShrink: 0, marginLeft: 12 }}
                >
                  ⬇ Download
                </a>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Missing docs indicator */}
      {!grouped["loss_run"] && (
        <div style={{
          padding: "10px 14px", background: "#FEF2F2", border: "1px solid #FECACA",
          borderRadius: 8, fontSize: 12, color: "#DC2626", marginTop: 8,
        }}>
          ⚠️ <strong>Missing:</strong> No Loss Run documents detected in this submission.
        </div>
      )}
      {!grouped["drivers_license"] && !grouped["motor_vehicle_record"] && (
        <div style={{
          padding: "10px 14px", background: "#FFFBEB", border: "1px solid #FDE68A",
          borderRadius: 8, fontSize: 12, color: "#D97706", marginTop: 8,
        }}>
          ⚠️ <strong>Note:</strong> No Driver License images detected — CDL verification may be limited.
        </div>
      )}
    </div>
  );
}
