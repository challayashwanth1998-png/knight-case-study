"use client";

import { useEffect, useState } from "react";

export default function SwaggerPage() {
  const [backendUrl, setBackendUrl] = useState("");

  useEffect(() => {
    const url = `${window.location.protocol}//${window.location.hostname}:8000`;
    setBackendUrl(url);
    // Auto-redirect to backend docs
    window.location.href = `${url}/docs`;
  }, []);

  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", minHeight: "60vh", gap: 16,
    }}>
      <div className="spinner" style={{ width: 28, height: 28 }} />
      <div style={{ fontSize: 14, color: "#64748B" }}>
        Redirecting to API Documentation...
      </div>
      {backendUrl && (
        <a
          href={`${backendUrl}/docs`}
          style={{ fontSize: 13, color: "#3B82F6" }}
        >
          Click here if not redirected →
        </a>
      )}
    </div>
  );
}
