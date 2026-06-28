"use client";

import type { SubmissionDetail } from "@/types";
import { getDocumentDownloadUrl } from "@/lib/api";

interface Props {
  submission: SubmissionDetail;
}

const TYPE_LABELS: Record<string, string> = {
  insurance_application: "Insurance Application",
  driver_list: "Driver List",
  equipment_list: "Equipment List",
  ifta_report: "IFTA Report",
  loss_run: "Loss Run",
  motor_vehicle_record: "Motor Vehicle Record",
  other: "Other",
};

export default function DocumentsTab({ submission }: Props) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      {submission.documents.map((doc) => (
        <div
          key={doc.id}
          className="card"
          style={{
            display: "flex", alignItems: "center",
            justifyContent: "space-between", padding: "14px 18px",
          }}
        >
          <div>
            <div style={{ fontWeight: 500, fontSize: 14, color: "#1F2937" }}>
              {doc.original_filename}
            </div>
            <div style={{ display: "flex", gap: 12, fontSize: 12, color: "#9CA3AF", marginTop: 3 }}>
              <span>{TYPE_LABELS[doc.classified_type || ""] || doc.classified_type || "Pending"}</span>
              {doc.classification_confidence != null && (
                <span>{Math.round(doc.classification_confidence * 100)}% confidence</span>
              )}
              {doc.quality_score != null && (
                <span>{Math.round(doc.quality_score * 100)}% quality</span>
              )}
              {doc.file_size && <span>{(doc.file_size / 1024).toFixed(0)} KB</span>}
            </div>
          </div>
          <a
            href={getDocumentDownloadUrl(submission.id, doc.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ padding: "5px 12px", fontSize: 12 }}
          >
            Download
          </a>
        </div>
      ))}
    </div>
  );
}
