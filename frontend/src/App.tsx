
import { useEffect, useState } from "react";
import {
  Activity,
  Database,
  Waves,
  ClipboardCheck,
  X,
  RadioTower,
} from "lucide-react";

import "./App.css";
import GovernmentHeader from "./components/GovernmentHeader";
import Dashboard from "./components/Dashboard";

const navigation = [
  {
    label: "Mission Overview",
    description: "Operational summary",
    icon: Activity,
    href: "#overview",
  },
  {
    label: "Sonar Ingestion",
    description: "Upload and validate data",
    icon: Waves,
    href: "#ingestion",
  },
  {
    label: "Ingestion Jobs",
    description: "Monitor processing",
    icon: Database,
    href: "#jobs",
  },
  {
    label: "Human Review",
    description: "Verify model findings",
    icon: ClipboardCheck,
    href: "#review",
  },
];

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeHref, setActiveHref] = useState("#overview");

  const closeSidebar = () => setSidebarOpen(false);

  useEffect(() => {
    const updateFromHash = () => {
      const hash = window.location.hash;
      if (navigation.some((item) => item.href === hash)) {
        setActiveHref(hash);
      }
    };

    updateFromHash();
    window.addEventListener("hashchange", updateFromHash);

    const sections = navigation
      .map((item) => document.querySelector(item.href))
      .filter((section): section is Element => section !== null);

    if (!("IntersectionObserver" in window) || sections.length === 0) {
      return () => {
        window.removeEventListener("hashchange", updateFromHash);
      };
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleSections = entries
          .filter((entry) => entry.isIntersecting)
          .sort(
            (a, b) =>
              a.boundingClientRect.top - b.boundingClientRect.top,
          );

        if (visibleSections.length > 0) {
          setActiveHref(`#${visibleSections[0].target.id}`);
        }
      },
      {
        rootMargin: "-18% 0px -62% 0px",
        threshold: 0,
      },
    );

    sections.forEach((section) => observer.observe(section));

    return () => {
      window.removeEventListener("hashchange", updateFromHash);
      observer.disconnect();
    };
  }, []);

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close navigation"
          onClick={closeSidebar}
        />
      )}

      <aside
        className={`app-sidebar ${sidebarOpen ? "is-open" : ""}`}
        aria-label="DeepSight workspace"
      >
        <div className="sidebar-brand">
          <div className="sidebar-brand__mark" aria-hidden="true">
            <RadioTower size={22} strokeWidth={1.8} />
          </div>

          <div className="sidebar-brand__copy">
            <span className="sidebar-brand__name">DeepSight</span>
            <span className="sidebar-brand__subtitle">
              MARINE INTELLIGENCE
            </span>
          </div>

          <button
            className="sidebar-close"
            type="button"
            aria-label="Close navigation"
            onClick={closeSidebar}
          >
            <X size={19} />
          </button>
        </div>

        <div className="sidebar-divider" />

        <div className="sidebar-section-label">
          <span>WORKSPACE</span>
          <span className="sidebar-section-label__meta">01 — 04</span>
        </div>

        <nav className="sidebar-navigation" aria-label="Main navigation">
          {navigation.map((item, index) => {
            const Icon = item.icon;
            const isActive = activeHref === item.href;

            return (
              <a
                className={`sidebar-nav-link ${isActive ? "is-current" : ""}`}
                href={item.href}
                key={item.href}
                aria-current={isActive ? "location" : undefined}
                onClick={() => {
                  setActiveHref(item.href);
                  closeSidebar();
                }}
              >
                <span className="sidebar-nav-link__icon" aria-hidden="true">
                  <Icon size={18} strokeWidth={1.8} />
                </span>

                <span className="sidebar-nav-link__copy">
                  <span className="sidebar-nav-link__label">
                    {item.label}
                  </span>
                  <span className="sidebar-nav-link__description">
                    {item.description}
                  </span>
                </span>

                <span className="sidebar-nav-link__index" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </a>
            );
          })}
        </nav>

        <div className="sidebar-spacer" />

        <div className="sidebar-workspace-note">
          <div className="sidebar-workspace-note__icon" aria-hidden="true">
            <Waves size={15} />
          </div>
          <div className="sidebar-workspace-note__copy">
            <span className="sidebar-workspace-note__title">
              Sonar Data Workspace
            </span>
            <span className="sidebar-workspace-note__caption">
              Marine survey intelligence
            </span>
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="sidebar-footer__indicator" aria-hidden="true" />
          <span className="sidebar-footer__text">
            DEEPSIGHT · OPERATIONS
          </span>
          <span className="sidebar-footer__version">MVP</span>
        </div>
      </aside>

      <div className="app-main">
        <GovernmentHeader onMenuClick={() => setSidebarOpen(true)} />

        <main className="app-content">
          <Dashboard />
        </main>
      </div>
    </div>
  );
}

export default App;