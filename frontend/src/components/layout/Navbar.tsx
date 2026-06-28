"use client";

export default function Navbar() {
  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        padding: "0 32px",
        height: 56,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "#FAFAF8",
        borderBottom: "1px solid #E8E5DE",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 30,
            height: 30,
            borderRadius: 8,
            background: "#3E6B5A",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 14,
            fontWeight: 700,
            color: "white",
          }}
        >
          K
        </div>
        <span style={{ fontSize: 15, fontWeight: 600, color: "#1A1A1A" }}>
          Knight Insurance
        </span>
        <span
          style={{
            fontSize: 11,
            color: "#9A9A8E",
            padding: "2px 8px",
            background: "#F0EDE6",
            borderRadius: 4,
            fontWeight: 500,
          }}
        >
          Underwriting
        </span>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: 12,
          color: "#9A9A8E",
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#2D8659",
            display: "inline-block",
          }}
        />
        System Online
      </div>
    </nav>
  );
}
