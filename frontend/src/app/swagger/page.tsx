"use client";

import { API_BASE_URL } from "@/lib/api";

export default function SwaggerPage() {
  return (
    <div className="page-container" style={{ padding: 0, height: "calc(100vh - 60px)" }}>
      <iframe
        src={`${API_BASE_URL.replace('/api/submissions', '')}/docs`}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
          borderRadius: 8,
        }}
        title="API Documentation — Swagger UI"
      />
    </div>
  );
}
