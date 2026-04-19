import type { ReactNode } from "react";

import type { AppSection } from "../app/App";

type AppLayoutProps = {
  activeSection: AppSection;
  children: ReactNode;
  onNavigate: (section: AppSection) => void;
};

const navigationItems: Array<{ id: AppSection; label: string }> = [
  { id: "dashboard", label: "Dashboard" },
  { id: "projects", label: "Projects" },
  { id: "tasks", label: "Tasks" },
  { id: "processes", label: "Processes" },
  { id: "documents", label: "Documents" },
  { id: "templates", label: "Templates" }
];

export function AppLayout({ activeSection, children, onNavigate }: AppLayoutProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">P</div>
          <div>
            <div className="brand-name">Procera</div>
            <div className="brand-subtitle">Business Operations</div>
          </div>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          {navigationItems.map((item) => (
            <button
              className={`nav-item ${activeSection === item.id ? "active" : ""}`}
              key={item.id}
              onClick={() => onNavigate(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-content">{children}</main>
    </div>
  );
}
