"use client";

import { usePathname } from "next/navigation";

const PAGE_TITLES: Record<string, { title: string; description: string }> = {
  "/": { title: "Dashboard", description: "Submission overview and analytics" },
  "/submit": { title: "New Submission", description: "Upload insurance documents" },
  "/submissions": { title: "All Submissions", description: "Browse and filter submissions" },
  "/rules": { title: "Rules Engine", description: "Knight underwriting business rules" },
  "/guidelines": { title: "Guidelines", description: "Knight Specialty Insurance program guide" },
};

export default function TopBar() {
  const pathname = usePathname();
  const isSubmissionDetail = pathname.startsWith("/submissions/") && pathname !== "/submissions";

  const page = isSubmissionDetail
    ? { title: "Submission Detail", description: "Analysis workbench" }
    : PAGE_TITLES[pathname] || { title: "Knight Insurance", description: "" };

  // Build breadcrumbs
  const crumbs: { label: string; href?: string }[] = [{ label: "Home", href: "/" }];
  if (pathname !== "/") {
    if (isSubmissionDetail) {
      crumbs.push({ label: "Submissions", href: "/submissions" });
      crumbs.push({ label: pathname.split("/").pop()?.slice(0, 8) || "Detail" });
    } else {
      crumbs.push({ label: page.title });
    }
  }

  return (
    <div className="app-topbar">
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--base)" }}>
          {crumbs.map((c, i) => (
            <span key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              {i > 0 && <span style={{ color: "var(--base-light)" }}>/</span>}
              {c.href ? (
                <a href={c.href} style={{ color: "var(--base)", textDecoration: "none" }}>
                  {c.label}
                </a>
              ) : (
                <span style={{ color: "var(--ink)", fontWeight: 500 }}>{c.label}</span>
              )}
            </span>
          ))}
        </div>
        <div style={{ fontSize: 16, fontWeight: 700, color: "var(--ink)", marginTop: 1 }}>
          {page.title}
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12, color: "var(--base)" }}>
      </div>
    </div>
  );
}
