import { useState } from "react";
import {
  Bell,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  Database,
  FileText,
  FolderKanban,
  LayoutDashboard,
  Menu,
  MoreHorizontal,
  RadioTower,
  ScanLine,
  Settings,
  Waves,
  X,
} from "lucide-react";

import Dashboard, { type WorkspaceSection } from "./components/Dashboard";
import "./App.css";

const nav: {
  id: WorkspaceSection;
  label: string;
  icon: typeof LayoutDashboard;
}[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "sonar-analysis", label: "Sonar Analysis", icon: ScanLine },
  { id: "processing-jobs", label: "Processing Jobs", icon: Database },
  { id: "review-queue", label: "Review Queue", icon: ClipboardCheck },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings },
];

const titles: Record<
  WorkspaceSection,
  {
    title: string;
  }
> = {
  overview: { title: "Mission Overview" },
  projects: { title: "Projects" },
  "sonar-analysis": { title: "Sonar Analysis" },
  "processing-jobs": { title: "Processing Jobs" },
  "review-queue": { title: "Review Queue" },
  reports: { title: "Reports" },
  settings: { title: "Settings" },
};

export default function App() {
  const [section, setSection] = useState<WorkspaceSection>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const changeSection = (id: WorkspaceSection) => {
    setSection(id);
    setSidebarOpen(false);
  };

  const title = titles[section];

  return (
    <div className="ds-app">
      {sidebarOpen && (
        <button
          className="ds-backdrop"
          aria-label="Close menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`ds-sidebar ${
          sidebarOpen ? "ds-sidebar--open" : ""
        }`}
      >
        <div className="ds-brand">
          <div className="ds-brand__mark">
            <Waves size={22} />
          </div>

          <div>
            <strong>DEEPSIGHT</strong>
            <span>MARINE INTELLIGENCE</span>
          </div>

          <button
            className="ds-icon-button ds-mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <div className="ds-side-label">
          <span>WORKSPACE</span>
          <span>01 / 07</span>
        </div>

        <nav className="ds-nav" aria-label="Workspace navigation">
          {nav.map((item, index) => {
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                className={`ds-nav-item ${
                  section === item.id ? "is-active" : ""
                }`}
                onClick={() => changeSection(item.id)}
                aria-current={
                  section === item.id ? "page" : undefined
                }
              >
                <Icon size={18} strokeWidth={1.8} />
                <span>{item.label}</span>
                <small>{String(index + 1).padStart(2, "0")}</small>
              </button>
            );
          })}
        </nav>

        <div className="ds-sidebar-bottom">
          <div className="ds-workspace-card">
            <span className="ds-workspace-icon">
              <RadioTower size={17} />
            </span>

            <div>
              <strong>Marine Survey</strong>
              <small>Analysis workspace</small>
            </div>

            <MoreHorizontal size={16} />
          </div>

          <div className="ds-side-footer">
            <span className="ds-online-dot" />
            API WORKSPACE
            <span className="ds-version">MVP</span>
          </div>
        </div>
      </aside>

      <div className="ds-main">
        <header className="ds-topbar">
          <div className="ds-topbar-left">
            <button
              className="ds-icon-button ds-menu-button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={19} />
            </button>

            <div className="ds-breadcrumb">
              <span>DeepSight</span>
              <ChevronRight size={14} />
              <strong>{title.title}</strong>
            </div>
          </div>

          <div className="ds-top-actions">
            <span className="ds-preview-pill">
              <i />
              API WORKSPACE
            </span>

            <button
              className="ds-icon-button"
              aria-label="Help"
            >
              <CircleHelp size={18} />
            </button>

            <button
              className="ds-icon-button"
              aria-label="Notifications"
            >
              <Bell size={18} />
            </button>

            <div className="ds-avatar">DS</div>
          </div>
        </header>

        <main className="ds-content">
          <Dashboard activeSection={section} />
        </main>
      </div>
    </div>
  );
}
