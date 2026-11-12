
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

import {
  BrowserRouter,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import Dashboard, {
  type WorkspaceSection,
} from "./components/Dashboard";

import "./App.css";

const nav: {
  id: WorkspaceSection;
  label: string;
  icon: typeof LayoutDashboard;
  path: string;
}[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard, path: "/" },
  { id: "projects", label: "Projects", icon: FolderKanban, path: "/projects" },
  { id: "sonar-analysis", label: "Sonar Analysis", icon: ScanLine, path: "/analysis" },
  { id: "processing-jobs", label: "Processing Jobs", icon: Database, path: "/jobs" },
  { id: "review-queue", label: "Review Queue", icon: ClipboardCheck, path: "/reviews" },
  { id: "reports", label: "Reports", icon: FileText, path: "/reports" },
  { id: "settings", label: "Settings", icon: Settings, path: "/settings" },
];

const titles: Record<WorkspaceSection, string> = {
  overview: "Mission Overview",
  projects: "Projects",
  "sonar-analysis": "Sonar Analysis",
  "processing-jobs": "Processing Jobs",
  "review-queue": "Review Queue",
  reports: "Reports",
  settings: "Settings",
};

const pathToSection: Record<string, WorkspaceSection> = {
  "/": "overview",
  "/projects": "projects",
  "/analysis": "sonar-analysis",
  "/jobs": "processing-jobs",
  "/reviews": "review-queue",
  "/reports": "reports",
  "/settings": "settings",
};

function Workspace() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const section = pathToSection[location.pathname] ?? "overview";
  const title = titles[section];

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="ds-app">
      {sidebarOpen && (
        <button
          type="button"
          className="ds-backdrop"
          aria-label="Close menu"
          onClick={closeSidebar}
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
            type="button"
            className="ds-icon-button ds-mobile-close"
            onClick={closeSidebar}
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
              <NavLink
                key={item.id}
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  `ds-nav-item ${isActive ? "is-active" : ""}`
                }
                onClick={closeSidebar}
              >
                <Icon size={18} strokeWidth={1.8} />
                <span>{item.label}</span>
                <small>{String(index + 1).padStart(2, "0")}</small>
              </NavLink>
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
              type="button"
              className="ds-icon-button ds-menu-button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={19} />
            </button>

            <div className="ds-breadcrumb">
              <span>DeepSight</span>
              <ChevronRight size={14} />
              <strong>{title}</strong>
            </div>
          </div>

          <div className="ds-top-actions">
            <span className="ds-preview-pill">
              <i />
              API WORKSPACE
            </span>

            <button
              type="button"
              className="ds-icon-button"
              aria-label="Help"
            >
              <CircleHelp size={18} />
            </button>

            <button
              type="button"
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Workspace />} />
        <Route path="/projects" element={<Workspace />} />
        <Route path="/analysis" element={<Workspace />} />
        <Route path="/jobs" element={<Workspace />} />
        <Route path="/reviews" element={<Workspace />} />
        <Route path="/reports" element={<Workspace />} />
        <Route path="/settings" element={<Workspace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
