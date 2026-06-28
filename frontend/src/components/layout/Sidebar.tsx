"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { section: "Operations" },
  { href: "/", icon: "📊", label: "Dashboard" },
  { href: "/submit", icon: "📤", label: "New Submission" },
  { href: "/submissions", icon: "📋", label: "Underwriter View" },
  { section: "Intelligence" },
  { href: "/analytics", icon: "📈", label: "Analytics" },
  { href: "/compare", icon: "🔀", label: "Compare" },
  { href: "/logs", icon: "📋", label: "System Logs" },
  { href: "/health", icon: "🏥", label: "System Health" },
  { section: "Reference" },
  { href: "/rules", icon: "⚖️", label: "Rules Engine" },
  { href: "/guidelines", icon: "📖", label: "Guidelines" },
  { href: "/swagger", icon: "📡", label: "API Docs" },
  { section: "Settings" },
  { href: "/settings/rules", icon: "⚙️", label: "Rules Config" },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside className="app-sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-logo" style={{ background: "var(--accent-cool)", fontSize: 20 }}>♞</div>
        <div>
          <div className="sidebar-name">Knight Insurance</div>
          <div className="sidebar-subtitle">Underwriting Platform</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item, i) => {
          if ("section" in item && item.section) {
            return (
              <div key={i} className="sidebar-section-label">
                {item.section}
              </div>
            );
          }
          const nav = item as { href: string; icon: string; label: string };
          return (
            <Link
              key={nav.href}
              href={nav.href}
              className={`sidebar-link ${isActive(nav.href) ? "active" : ""}`}
            >
              <span className="sidebar-link-icon">{nav.icon}</span>
              {nav.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div style={{ fontSize: 10 }}>
          Knight Specialty Insurance Co.
        </div>
      </div>
    </aside>
  );
}
