"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { uploadSubmission, processSubmission } from "@/lib/api";

const ALLOWED_TYPES = [".pdf", ".xlsx", ".xls", ".docx", ".csv", ".txt", ".png", ".jpg", ".jpeg"];

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "pdf": return "📄";
    case "xlsx": case "xls": case "csv": return "📊";
    case "docx": case "doc": return "📝";
    case "png": case "jpg": case "jpeg": return "🖼️";
    default: return "📎";
  }
}

export default function SubmitPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const addFiles = (newFiles: FileList | File[]) => {
    const arr = Array.from(newFiles);
    const valid: File[] = [];
    const errors: string[] = [];

    for (const f of arr) {
      const ext = "." + f.name.split(".").pop()?.toLowerCase();
      if (!ALLOWED_TYPES.includes(ext)) {
        errors.push(`${f.name}: unsupported type`);
        continue;
      }
      if (f.size > 25 * 1024 * 1024) {
        errors.push(`${f.name}: exceeds 25MB limit`);
        continue;
      }
      if (files.some((existing) => existing.name === f.name && existing.size === f.size)) {
        errors.push(`${f.name}: duplicate`);
        continue;
      }
      valid.push(f);
    }

    if (errors.length) setError(errors.join("; "));
    else setError(null);

    if (valid.length) setFiles((prev) => [...prev, ...valid]);
  };

  const handleUpload = async () => {
    if (!files.length) return;
    setUploading(true);
    setError(null);
    try {
      const sub = await uploadSubmission(files);
      await processSubmission(sub.id);
      router.push(`/submissions/${sub.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <div className="page-header">
        <h1 className="page-title">New Submission</h1>
        <p className="page-description">
          Upload insurance documents for AI-powered analysis and underwriting review
        </p>
      </div>

      {/* Info Banner */}
      <div className="usa-alert usa-alert-info" style={{ marginBottom: 20 }}>
        <strong>Accepted formats:</strong> PDF, Excel, Word, CSV, Images (PNG/JPG).
        Max 25MB per file, up to 20 files per submission.
      </div>

      {/* Upload Zone */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div
          className={`upload-zone ${dragOver ? "drag-over" : ""}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            addFiles(e.dataTransfer.files);
          }}
        >
          <input
            ref={fileRef}
            type="file"
            multiple
            accept={ALLOWED_TYPES.join(",")}
            style={{ display: "none" }}
            onChange={(e) => e.target.files && addFiles(e.target.files)}
          />
          <div style={{ fontSize: 36, marginBottom: 8 }}>📂</div>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
            Drop files here or click to browse
          </div>
          <div style={{ fontSize: 12, color: "var(--base)" }}>
            Application, driver list, equipment schedule, IFTA reports, loss runs, MVRs
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="usa-alert usa-alert-error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            marginBottom: 12,
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 700 }}>
              Selected Files ({files.length})
            </h3>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => setFiles([])}
            >
              Clear All
            </button>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}></th>
                <th>File Name</th>
                <th>Size</th>
                <th style={{ width: 60 }}></th>
              </tr>
            </thead>
            <tbody>
              {files.map((f, i) => (
                <tr key={i}>
                  <td style={{ fontSize: 18 }}>{getFileIcon(f.name)}</td>
                  <td style={{ fontWeight: 500 }}>{f.name}</td>
                  <td style={{ color: "var(--base)" }}>{formatSize(f.size)}</td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      style={{ padding: "2px 6px", fontSize: 11 }}
                      onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Submit */}
      {files.length > 0 && (
        <div style={{ display: "flex", gap: 12 }}>
          <button
            className="btn btn-primary btn-lg"
            onClick={handleUpload}
            disabled={uploading}
            style={{ flex: 1 }}
          >
            {uploading ? (
              <>
                <span className="spinner" style={{ width: 14, height: 14 }} />
                Processing...
              </>
            ) : (
              `Submit ${files.length} Document${files.length > 1 ? "s" : ""} for Analysis`
            )}
          </button>
        </div>
      )}
    </div>
  );
}
