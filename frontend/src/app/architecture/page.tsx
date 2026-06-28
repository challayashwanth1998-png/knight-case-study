"use client";

export default function ArchitecturePage() {
  return (
    <div className="page-container" style={{ padding: 0, height: "calc(100vh - 60px)" }}>
      <iframe
        src="/architecture.html"
        style={{
          width: "100%",
          height: "100%",
          border: "none",
          borderRadius: 8,
        }}
        title="System Architecture"
      />
    </div>
  );
}
