
import { useMemo, useRef, useState } from "react";
import {
  Activity, Bell, Check, ChevronDown, ChevronLeft, ChevronRight,
  CircleHelp, ClipboardCheck, Clock3, Database, FileText, Filter,
  FolderKanban, LayoutDashboard, Menu, MoreHorizontal, RadioTower,
  ScanLine, Search, Settings, ShieldCheck, Waves, X, ZoomIn, ZoomOut,
  Maximize2, Upload, Image as ImageIcon, ArrowUpRight, SlidersHorizontal,
} from "lucide-react";
import "./App.css";

type Section =
  | "overview"
  | "projects"
  | "analysis"
  | "jobs"
  | "reviews"
  | "reports"
  | "settings";

type Job = {
  id: string;
  source: string;
  survey: string;
  status: "Completed" | "Processing" | "Queued" | "Failed";
  frames: number;
  detections: number;
  model: string;
  updated: string;
};

const nav: { id: Section; label: string; icon: typeof Activity }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "analysis", label: "Sonar Analysis", icon: ScanLine },
  { id: "jobs", label: "Processing Jobs", icon: Database },
  { id: "reviews", label: "Review Queue", icon: ClipboardCheck },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings },
];

const previewJobs: Job[] = [
  { id: "DS-2048", source: "Survey Alpha", survey: "Eastern Shelf · Transect 04", status: "Completed", frames: 248, detections: 36, model: "DeepSight Detector v1", updated: "Today, 10:42" },
  { id: "DS-2047", source: "Survey Alpha", survey: "Eastern Shelf · Transect 03", status: "Processing", frames: 192, detections: 21, model: "DeepSight Detector v1", updated: "Today, 10:18" },
  { id: "DS-2046", source: "Survey Beta", survey: "Coastal Grid · Sector B", status: "Queued", frames: 0, detections: 0, model: "DeepSight Detector v1", updated: "Today, 09:56" },
  { id: "DS-2045", source: "Survey Gamma", survey: "Northern Route · Pass 02", status: "Failed", frames: 86, detections: 9, model: "DeepSight Detector v1", updated: "Yesterday, 17:31" },
];

const previewDetections = [
  { id: "DET-036", label: "Debris candidate", score: "0.94", frame: 184, x: 58, y: 34 },
  { id: "DET-035", label: "Unclassified object", score: "0.87", frame: 171, x: 27, y: 59 },
  { id: "DET-034", label: "Debris candidate", score: "0.81", frame: 149, x: 71, y: 67 },
  { id: "DET-033", label: "Possible structure", score: "0.76", frame: 121, x: 43, y: 24 },
];

const titles: Record<Section, { title: string; subtitle: string }> = {
  overview: { title: "Mission Overview", subtitle: "Operational status and recent marine survey activity." },
  projects: { title: "Projects", subtitle: "Survey collections, sources and associated processing activity." },
  analysis: { title: "Sonar Analysis", subtitle: "Inspect sonar frames, model detections and supporting evidence." },
  jobs: { title: "Processing Jobs", subtitle: "Track ingestion and processing activity across survey data." },
  reviews: { title: "Review Queue", subtitle: "Human verification of model-generated findings." },
  reports: { title: "Reports", subtitle: "Review processing summaries and available report outputs." },
  settings: { title: "Settings", subtitle: "Workspace configuration and application information." },
};

function Status({ value }: { value: Job["status"] }) {
  return <span className={`status status--${value.toLowerCase()}`}><i />{value}</span>;
}

function App() {
  const [section, setSection] = useState<Section>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState(previewJobs[0].id);
  const [selectedDetection, setSelectedDetection] = useState(0);
  const [analysisTab, setAnalysisTab] = useState("Evidence");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("All statuses");
  const [reviewed, setReviewed] = useState<string[]>([]);
  const [fileName, setFileName] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [zoom, setZoom] = useState(100);
  const fileRef = useRef<HTMLInputElement>(null);

  const currentJob = previewJobs.find((job) => job.id === selectedJob) ?? previewJobs[0];
  const detection = previewDetections[selectedDetection];

  const filteredJobs = useMemo(() => previewJobs.filter((job) => {
    const matchesQuery = `${job.id} ${job.source} ${job.survey} ${job.status}`.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = statusFilter === "All statuses" || job.status === statusFilter;
    return matchesQuery && matchesStatus;
  }), [query, statusFilter]);

  const openAnalysis = (id: string) => {
    setSelectedJob(id);
    setSection("analysis");
  };

  const changeSection = (id: Section) => {
    setSection(id);
    setSidebarOpen(false);
    setQuery("");
  };

  const handleFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setShowUpload(true);
    }
  };

  const title = titles[section];

  return (
    <div className="ds-app">
      {sidebarOpen && <button className="ds-backdrop" aria-label="Close menu" onClick={() => setSidebarOpen(false)} />}
      <aside className={`ds-sidebar ${sidebarOpen ? "ds-sidebar--open" : ""}`}>
        <div className="ds-brand">
          <div className="ds-brand__mark"><Waves size={22} /></div>
          <div><strong>DEEPSIGHT</strong><span>MARINE INTELLIGENCE</span></div>
          <button className="ds-icon-button ds-mobile-close" onClick={() => setSidebarOpen(false)} aria-label="Close menu"><X size={18} /></button>
        </div>

        <div className="ds-side-label"><span>WORKSPACE</span><span>01 / 07</span></div>
        <nav className="ds-nav" aria-label="Workspace navigation">
          {nav.map((item, index) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={`ds-nav-item ${section === item.id ? "is-active" : ""}`} onClick={() => changeSection(item.id)} aria-current={section === item.id ? "page" : undefined}>
                <Icon size={18} strokeWidth={1.8} />
                <span>{item.label}</span>
                <small>{String(index + 1).padStart(2, "0")}</small>
              </button>
            );
          })}
        </nav>

        <div className="ds-sidebar-bottom">
          <div className="ds-workspace-card">
            <span className="ds-workspace-icon"><RadioTower size={17} /></span>
            <div><strong>Marine Survey</strong><small>Analysis workspace</small></div>
            <MoreHorizontal size={16} />
          </div>
          <div className="ds-side-footer"><span className="ds-online-dot" /> FRONTEND PREVIEW <span className="ds-version">MVP</span></div>
        </div>
      </aside>

      <div className="ds-main">
        <header className="ds-topbar">
          <div className="ds-topbar-left">
            <button className="ds-icon-button ds-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open menu"><Menu size={19} /></button>
            <div className="ds-breadcrumb"><span>DeepSight</span><ChevronRight size={14} /><strong>{title.title}</strong></div>
          </div>
          <div className="ds-top-actions">
            <span className="ds-preview-pill"><i /> UI PREVIEW</span>
            <button className="ds-icon-button" aria-label="Help"><CircleHelp size={18} /></button>
            <button className="ds-icon-button" aria-label="Notifications"><Bell size={18} /></button>
            <div className="ds-avatar">DS</div>
          </div>
        </header>

        <main className="ds-content">
          <div className="ds-page-heading">
            <div><div className="ds-eyebrow">MARINE INTELLIGENCE <span>/</span> {section.replace("-", " ").toUpperCase()}</div><h1>{title.title}</h1><p>{title.subtitle}</p></div>
            <div className="ds-heading-actions">
              <button className="ds-button ds-button--secondary" onClick={() => setShowUpload(true)}><Upload size={15} /> Import data</button>
              <button className="ds-button ds-button--primary" onClick={() => changeSection("analysis")}><ScanLine size={15} /> Open analysis</button>
            </div>
          </div>

          {section === "overview" && <>
            <div className="ds-banner">
              <div className="ds-banner-icon"><Waves size={22} /></div>
              <div className="ds-banner-copy"><strong>Marine survey intelligence workspace</strong><span>Review sonar imagery, inspect detections and track processing activity in one place.</span></div>
              <span className="ds-banner-tag">DESIGN PREVIEW</span>
            </div>
            <div className="ds-metric-grid">
              <Metric icon={<Database size={17}/>} label="Total jobs" value="24" note="Illustrative preview" tone="cyan" />
              <Metric icon={<Activity size={17}/>} label="Processing" value="03" note="Illustrative preview" tone="blue" />
              <Metric icon={<ClipboardCheck size={17}/>} label="Pending review" value="18" note="Illustrative preview" tone="amber" />
              <Metric icon={<ScanLine size={17}/>} label="Detections" value="1,284" note="Illustrative preview" tone="green" />
            </div>
            <div className="ds-overview-grid">
              <section className="ds-panel ds-recent-panel">
                <PanelHeading eyebrow="PIPELINE ACTIVITY" title="Recent processing jobs" action="View all" onAction={() => changeSection("jobs")} />
                <JobTable jobs={previewJobs.slice(0, 3)} onOpen={openAnalysis} compact />
              </section>
              <section className="ds-panel ds-activity-panel">
                <PanelHeading eyebrow="WORKSPACE" title="Quick access" />
                <button className="ds-quick-link" onClick={() => changeSection("projects")}><span className="ds-quick-icon"><FolderKanban size={17}/></span><span><strong>Browse projects</strong><small>Explore survey collections</small></span><ArrowUpRight size={16}/></button>
                <button className="ds-quick-link" onClick={() => changeSection("analysis")}><span className="ds-quick-icon"><ScanLine size={17}/></span><span><strong>Sonar analysis</strong><small>Inspect frames and detections</small></span><ArrowUpRight size={16}/></button>
                <button className="ds-quick-link" onClick={() => changeSection("reviews")}><span className="ds-quick-icon"><ClipboardCheck size={17}/></span><span><strong>Review queue</strong><small>Verify model findings</small></span><ArrowUpRight size={16}/></button>
                <div className="ds-note"><ShieldCheck size={15}/><span>Sample figures are for interface preview only. Live values will come from the API.</span></div>
              </section>
            </div>
          </>}

          {section === "projects" && <section className="ds-panel">
            <PanelHeading eyebrow="SURVEY COLLECTIONS" title="Projects" action="Import data" onAction={() => setShowUpload(true)} />
            <div className="ds-project-grid">
              {["Survey Alpha", "Survey Beta", "Survey Gamma"].map((name, i) => {
                const related = previewJobs.filter((job) => job.source === name);
                return <article className="ds-project-card" key={name}>
                  <div className="ds-project-card-top"><span className="ds-project-icon"><Waves size={19}/></span><button className="ds-icon-button" aria-label={`More options for ${name}`}><MoreHorizontal size={17}/></button></div>
                  <span className="ds-project-type">MARINE SURVEY · PREVIEW</span><h3>{name}</h3><p>{["Eastern Shelf survey collection","Coastal grid survey collection","Northern route survey collection"][i]}</p>
                  <div className="ds-project-stats"><div><strong>{related.length || 1}</strong><small>Jobs</small></div><div><strong>{related.reduce((sum, job) => sum + job.frames, 0) || "—"}</strong><small>Frames</small></div><div><strong>{related.reduce((sum, job) => sum + job.detections, 0) || "—"}</strong><small>Findings</small></div></div>
                  <button className="ds-text-action" onClick={() => openAnalysis((related[0] ?? previewJobs[i]).id)}>Open project <ArrowUpRight size={14}/></button>
                </article>;
              })}
            </div>
          </section>}

          {section === "analysis" && <div className="ds-analysis">
            <section className="ds-panel ds-analysis-nav">
              <PanelHeading eyebrow="DETECTION NAVIGATOR" title="Findings" />
              <div className="ds-job-select"><label>PROCESSING JOB</label><select value={selectedJob} onChange={(e) => setSelectedJob(e.target.value)}>{previewJobs.map((job) => <option key={job.id} value={job.id}>{job.id} · {job.source}</option>)}</select><ChevronDown size={14}/></div>
              <div className="ds-detection-summary"><span>DETECTIONS</span><strong>{previewDetections.length} <small>preview items</small></strong></div>
              <div className="ds-detection-list">{previewDetections.map((item, i) => <button key={item.id} className={`ds-detection-item ${i === selectedDetection ? "is-selected" : ""}`} onClick={() => setSelectedDetection(i)}><span className="ds-detection-thumb"><ScanLine size={16}/></span><span className="ds-detection-copy"><strong>{item.label}</strong><small>{item.id} · Frame {item.frame}</small></span><span className="ds-detection-score">{item.score}</span></button>)}</div>
              <div className="ds-nav-foot"><span className="ds-online-dot"/> Preview detections only</div>
            </section>
            <section className="ds-panel ds-viewer-panel">
              <div className="ds-viewer-heading"><div><span className="ds-eyebrow">FRAME VIEWER</span><h2>{currentJob.id} <span>/</span> Frame {detection.frame}</h2></div><div className="ds-viewer-tools"><button className="ds-icon-button" onClick={() => setZoom(Math.max(50, zoom - 10))} aria-label="Zoom out"><ZoomOut size={16}/></button><span>{zoom}%</span><button className="ds-icon-button" onClick={() => setZoom(Math.min(200, zoom + 10))} aria-label="Zoom in"><ZoomIn size={16}/></button><button className="ds-icon-button" onClick={() => setZoom(100)} aria-label="Reset zoom"><Maximize2 size={15}/></button></div></div>
              <div className="ds-sonar-canvas"><div className="ds-sonar-image" style={{ transform: `scale(${zoom / 100})` }}><div className="ds-sonar-grain"/><div className="ds-sonar-band ds-sonar-band--one"/><div className="ds-sonar-band ds-sonar-band--two"/><div className="ds-sonar-shadow"/><div className="ds-target-box" style={{ left: `${detection.x}%`, top: `${detection.y}%` }}><span>{detection.id}</span></div><div className="ds-canvas-label">ILLUSTRATIVE SONAR VIEW</div></div><div className="ds-canvas-crosshair">+</div></div>
              <div className="ds-frame-controls"><button className="ds-button ds-button--secondary ds-button--small" onClick={() => setSelectedDetection((selectedDetection + previewDetections.length - 1) % previewDetections.length)}><ChevronLeft size={14}/> Previous</button><span>Frame {detection.frame} <i/> {currentJob.frames || "—"} frames</span><button className="ds-button ds-button--secondary ds-button--small" onClick={() => setSelectedDetection((selectedDetection + 1) % previewDetections.length)}>Next <ChevronRight size={14}/></button></div>
            </section>
            <section className="ds-panel ds-inspector">
              <PanelHeading eyebrow="DETECTION INSPECTOR" title="Finding details"/>
              <div className="ds-inspector-class"><span className="ds-inspector-symbol"><ScanLine size={18}/></span><div><strong>{detection.label}</strong><small>{detection.id}</small></div></div>
              <div className="ds-score-block"><div><span>MODEL SCORE</span><strong>{detection.score}</strong></div><div className="ds-score-track"><i style={{width: `${Number(detection.score) * 100}%`}}/></div><small>Model score, not a calibrated probability</small></div>
              <div className="ds-inspector-tabs">{["Evidence", "Metadata", "Review"].map((tab) => <button className={analysisTab === tab ? "is-active" : ""} onClick={() => setAnalysisTab(tab)} key={tab}>{tab}</button>)}</div>
              {analysisTab === "Evidence" && <div className="ds-inspector-content"><Info label="Frame index" value={String(detection.frame)}/><Info label="Evidence status" value="Preview only"/><Info label="Detection class" value={detection.label}/><div className="ds-inspector-disclaimer">Evidence values and overlays shown here are illustrative placeholders, not model output.</div></div>}
              {analysisTab === "Metadata" && <div className="ds-inspector-content"><Info label="Job" value={currentJob.id}/><Info label="Source" value={currentJob.source}/><Info label="Survey" value={currentJob.survey}/><Info label="Model" value={currentJob.model}/></div>}
              {analysisTab === "Review" && <div className="ds-inspector-content"><p className="ds-review-help">Review actions are shown as interface controls in this preview. They are not submitted to a backend.</p><button className="ds-button ds-button--primary ds-full-button" onClick={() => setReviewed((items) => [...new Set([...items, detection.id])])}><Check size={15}/> Mark reviewed locally</button>{reviewed.includes(detection.id) && <span className="ds-local-confirm">Marked reviewed in this browser session</span>}</div>}
            </section>
          </div>}

          {section === "jobs" && <section className="ds-panel">
            <PanelHeading eyebrow="PIPELINE MONITOR" title="Processing jobs" action="Import data" onAction={() => setShowUpload(true)}/>
            <div className="ds-table-toolbar"><div className="ds-search"><Search size={16}/><input placeholder="Search jobs, sources..." value={query} onChange={(e) => setQuery(e.target.value)}/>{query && <button onClick={() => setQuery("")} aria-label="Clear search"><X size={14}/></button>}</div><div className="ds-filter"><Filter size={15}/><select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option>All statuses</option><option>Completed</option><option>Processing</option><option>Queued</option><option>Failed</option></select></div></div>
            <JobTable jobs={filteredJobs} onOpen={openAnalysis}/>
            <div className="ds-table-footer">Showing {filteredJobs.length} of {previewJobs.length} illustrative records <span>Pagination will connect to the API.</span></div>
          </section>}

          {section === "reviews" && <section className="ds-panel">
            <PanelHeading eyebrow="HUMAN-IN-THE-LOOP" title="Review queue"/>
            <div className="ds-review-toolbar"><span>{previewDetections.filter((d) => !reviewed.includes(d.id)).length} items awaiting local review</span><span className="ds-preview-pill"><i/> PREVIEW DATA</span></div>
            <div className="ds-review-list">{previewDetections.map((item, i) => <article className="ds-review-row" key={item.id}><div className="ds-review-thumb"><ScanLine size={20}/><span>F{item.frame}</span></div><div className="ds-review-main"><strong>{item.label}</strong><small>{item.id} · Job {currentJob.id} · Frame {item.frame}</small><div className="ds-review-score">Model score <b>{item.score}</b></div></div>{reviewed.includes(item.id) ? <span className="ds-reviewed"><Check size={14}/> Reviewed locally</span> : <div className="ds-review-actions"><button className="ds-button ds-button--secondary ds-button--small" onClick={() => {setSelectedDetection(i);setSection("analysis");setAnalysisTab("Evidence");}}>Inspect</button><button className="ds-button ds-button--primary ds-button--small" onClick={() => setReviewed((items) => [...items, item.id])}>Mark reviewed</button></div>}</article>)}</div>
            <p className="ds-footnote">Local preview actions only. Final accept/reject decisions will be connected to the review API.</p>
          </section>}

          {section === "reports" && <section className="ds-panel">
            <PanelHeading eyebrow="REPORT CENTRE" title="Job reports"/>
            <div className="ds-report-intro"><div className="ds-report-icon"><FileText size={22}/></div><div><strong>Processing summaries</strong><p>Open a job to inspect report information. Export actions will be enabled when connected to the report API.</p></div></div>
            <div className="ds-report-list">{previewJobs.map((job) => <div className="ds-report-row" key={job.id}><span className="ds-report-file"><FileText size={18}/></span><div className="ds-report-copy"><strong>{job.id} · Processing report</strong><small>{job.source} · {job.updated}</small></div><Status value={job.status}/><button className="ds-icon-button" aria-label={`Inspect ${job.id}`} onClick={() => openAnalysis(job.id)}><ArrowUpRight size={16}/></button></div>)}</div>
            <p className="ds-footnote">Report entries are illustrative. No report file is generated or downloaded in this frontend preview.</p>
          </section>}

          {section === "settings" && <section className="ds-panel ds-settings-panel">
            <PanelHeading eyebrow="PREFERENCES" title="Workspace settings"/>
            <div className="ds-settings-section"><div><strong>Workspace identity</strong><p>Basic information about this application preview.</p></div><Info label="Application" value="DeepSight"/><Info label="Workspace type" value="Marine sonar intelligence"/><Info label="Interface" value="Frontend prototype"/></div>
            <div className="ds-settings-section"><div><strong>Integration status</strong><p>Backend-dependent features are pending API integration.</p></div><Info label="API connection" value="Not connected in this preview"/><Info label="Data persistence" value="Not enabled"/><Info label="Review submission" value="Not enabled"/></div>
            <div className="ds-settings-note"><SlidersHorizontal size={17}/><span>These settings are informational. Editable preferences will be added when their persistence and configuration requirements are defined.</span></div>
          </section>}
        </main>
      </div>

      {showUpload && <div className="ds-modal-backdrop" role="presentation" onMouseDown={(e) => {if (e.target === e.currentTarget) setShowUpload(false);}}><section className="ds-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title"><div className="ds-modal-heading"><div><span className="ds-eyebrow">DATA INGESTION</span><h2 id="upload-title">Import sonar data</h2></div><button className="ds-icon-button" onClick={() => setShowUpload(false)} aria-label="Close dialog"><X size={18}/></button></div><button className="ds-upload-zone" onClick={() => fileRef.current?.click()}><span className="ds-upload-icon"><Upload size={22}/></span><strong>{fileName || "Choose sonar imagery"}</strong><small>Choose a file from your device. This preview does not upload it to a server.</small><span className="ds-button ds-button--secondary ds-button--small"><ImageIcon size={14}/> Browse files</span></button><input ref={fileRef} type="file" accept="image/*,.tif,.tiff" hidden onChange={handleFile}/><div className="ds-modal-actions"><button className="ds-button ds-button--secondary" onClick={() => setShowUpload(false)}>Cancel</button><button className="ds-button ds-button--primary" disabled={!fileName} onClick={() => setShowUpload(false)}>Done</button></div></section></div>}
    </div>
  );
}

function Metric({ icon, label, value, note, tone }: { icon: React.ReactNode; label: string; value: string; note: string; tone: string }) {
  return <article className={`ds-metric ds-metric--${tone}`}><div className="ds-metric-top"><span>{label}</span><i>{icon}</i></div><strong>{value}</strong><small>{note}</small></article>;
}

function PanelHeading({ eyebrow, title, action, onAction }: { eyebrow: string; title: string; action?: string; onAction?: () => void }) {
  return <div className="ds-panel-heading"><div><span className="ds-eyebrow">{eyebrow}</span><h2>{title}</h2></div>{action && <button className="ds-text-action" onClick={onAction}>{action}<ArrowUpRight size={14}/></button>}</div>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="ds-info"><span>{label}</span><strong>{value}</strong></div>;
}

function JobTable({ jobs, onOpen, compact = false }: { jobs: Job[]; onOpen: (id: string) => void; compact?: boolean }) {
  return <div className="ds-table-wrap"><table className={`ds-table ${compact ? "ds-table--compact" : ""}`}><thead><tr><th>JOB ID</th><th>STATUS</th><th>SOURCE / SURVEY</th><th>FRAMES</th><th>DETECTIONS</th><th>UPDATED</th><th/></tr></thead><tbody>{jobs.length ? jobs.map((job) => <tr key={job.id} onClick={() => onOpen(job.id)} tabIndex={0} onKeyDown={(e) => {if (e.key === "Enter") onOpen(job.id);}}><td><strong className="ds-job-id">{job.id}</strong></td><td><Status value={job.status}/></td><td><span className="ds-table-source">{job.source}</span><small className="ds-table-sub">{job.survey}</small></td><td>{job.frames.toLocaleString()}</td><td>{job.detections.toLocaleString()}</td><td>{job.updated}</td><td><ChevronRight size={15}/></td></tr>) : <tr><td colSpan={7} className="ds-no-results">No matching jobs in this preview.</td></tr>}</tbody></table></div>;
}

export default App;