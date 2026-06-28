"use client";

import { useState, useRef } from "react";

interface Props {
  selectedFiles: File[];
  onFilesSelected: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onUpload: () => void;
  uploading: boolean;
}

const FILE_ICONS: Record<string, string> = {
  pdf: "📄",
  xlsx: "📊",
  xls: "📊",
  docx: "📝",
  png: "🖼️",
  jpg: "🖼️",
  jpeg: "🖼️",
};

export default function UploadZone({
  selectedFiles,
  onFilesSelected,
  onRemoveFile,
  onUpload,
  uploading,
}: Props) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    onFilesSelected(Array.from(e.dataTransfer.files));
  };

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) onFilesSelected(Array.from(e.target.files));
  };

  const getIcon = (name: string) => {
    const ext = name.split(".").pop()?.toLowerCase() || "";
    return FILE_ICONS[ext] || "📎";
  };

  return (
    <div className="card" style={{ marginBottom: 28 }}>
      <h2
        style={{
          fontSize: 15,
          fontWeight: 600,
          marginBottom: 14,
          color: "#1F2937",
        }}
      >
        New Submission
      </h2>

      <div
        className={`upload-zone ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          onChange={handleSelect}
          style={{ display: "none" }}
          accept=".pdf,.xlsx,.xls,.docx,.png,.jpg,.jpeg,.csv,.txt"
        />
        <div style={{ fontSize: 28, marginBottom: 8, opacity: 0.5 }}>
          {dragOver ? "↓" : "📎"}
        </div>
        <div
          style={{ fontSize: 14, fontWeight: 500, color: "#374151", marginBottom: 4 }}
        >
          {dragOver ? "Drop files here" : "Drag & drop documents"}
        </div>
        <div style={{ fontSize: 13, color: "#9CA3AF" }}>
          PDF, Excel, Word, Images — or click to browse
        </div>
      </div>

      {selectedFiles.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: "#6B7280",
              marginBottom: 8,
            }}
          >
            {selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""} selected
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {selectedFiles.map((file, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "5px 10px",
                  background: "#F9FAFB",
                  border: "1px solid #E5E7EB",
                  borderRadius: 6,
                  fontSize: 13,
                }}
              >
                <span>{getIcon(file.name)}</span>
                <span
                  style={{
                    maxWidth: 180,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {file.name}
                </span>
                <span style={{ color: "#9CA3AF", fontSize: 11 }}>
                  {(file.size / 1024).toFixed(0)}KB
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFile(i);
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#9CA3AF",
                    cursor: "pointer",
                    fontSize: 14,
                    padding: 0,
                    lineHeight: 1,
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <button
            className="btn btn-primary"
            onClick={onUpload}
            disabled={uploading}
            style={{ marginTop: 14 }}
          >
            {uploading ? (
              <>
                <span className="spinner" /> Uploading...
              </>
            ) : (
              "Upload & Analyze"
            )}
          </button>
        </div>
      )}
    </div>
  );
}
