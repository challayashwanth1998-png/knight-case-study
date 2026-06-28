"use client";

export default function SwaggerPage() {
  const backendUrl = typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : "http://localhost:8000";

  return (
    <div style={{ height: "calc(100vh - 60px)", padding: 0 }}>
      <iframe
        src={`${backendUrl}/docs`}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
        }}
        title="API Documentation — Swagger UI"
      />
    </div>
  );
}
