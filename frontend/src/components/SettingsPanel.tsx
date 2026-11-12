
import {
  RotateCcw,
  SlidersHorizontal,
  ClipboardCheck,
  MonitorCog,
} from "lucide-react";

import type { WorkspaceSettings } from "../hooks/useWorkspaceSettings";
import "./SettingsPanel.css";

const sectionOptions = [
  { value: "overview", label: "Mission Overview" },
  { value: "projects", label: "Projects" },
  { value: "sonar-analysis", label: "Sonar Analysis" },
  { value: "processing-jobs", label: "Processing Jobs" },
  { value: "review-queue", label: "Review Queue" },
  { value: "reports", label: "Reports" },
] as const;

type SettingsPanelProps = {
  settings: WorkspaceSettings;
  updateSettings: (patch: Partial<WorkspaceSettings>) => void;
  resetSettings: () => void;
};

function SettingSwitch({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="ds-switch">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span />
    </label>
  );
}

export default function SettingsPanel({
  settings,
  updateSettings,
  resetSettings,
}: SettingsPanelProps) {
  return (
    <div className="ds-settings">
      <section className="ds-settings__section">
        <header className="ds-settings__section-header">
          <span className="ds-settings__icon">
            <MonitorCog size={18} />
          </span>
          <div>
            <h2>Workspace</h2>
            <p>Control how DeepSight opens and refreshes.</p>
          </div>
        </header>

        <div className="ds-settings__row">
          <div className="ds-settings__copy">
            <strong>Default landing page</strong>
            <span>Section opened when entering the workspace.</span>
          </div>
          <select
            value={settings.defaultSection}
            onChange={(event) =>
              updateSettings({
                defaultSection:
                  event.target.value as WorkspaceSettings["defaultSection"],
              })
            }
          >
            {sectionOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="ds-settings__row">
          <div className="ds-settings__copy">
            <strong>Automatic refresh</strong>
            <span>Refresh jobs and reviews automatically.</span>
          </div>
          <SettingSwitch
            checked={settings.autoRefresh}
            onChange={(autoRefresh) => updateSettings({ autoRefresh })}
          />
        </div>

        <div className="ds-settings__row">
          <div className="ds-settings__copy">
            <strong>Refresh interval</strong>
            <span>Frequency of background data requests.</span>
          </div>
          <select
            value={settings.refreshInterval}
            disabled={!settings.autoRefresh}
            onChange={(event) =>
              updateSettings({
                refreshInterval: Number(event.target.value),
              })
            }
          >
            <option value={5}>5 seconds</option>
            <option value={10}>10 seconds</option>
            <option value={15}>15 seconds</option>
            <option value={30}>30 seconds</option>
          </select>
        </div>
      </section>

      <section className="ds-settings__section">
        <header className="ds-settings__section-header">
          <span className="ds-settings__icon">
            <SlidersHorizontal size={18} />
          </span>
          <div>
            <h2>Analysis display</h2>
            <p>Configure how detection results are displayed.</p>
          </div>
        </header>

        <div className="ds-settings__row">
          <div className="ds-settings__copy">
            <strong>Minimum displayed confidence</strong>
            <span>
              Display preference only; does not change detector inference.
            </span>
          </div>
          <select
            value={settings.defaultConfidence}
            onChange={(event) =>
              updateSettings({
                defaultConfidence: Number(event.target.value),
              })
            }
          >
            <option value={0}>No filter (0%)</option>
            <option value={0.25}>25%</option>
            <option value={0.5}>50%</option>
            <option value={0.65}>65%</option>
            <option value={0.75}>75%</option>
            <option value={0.9}>90%</option>
          </select>
        </div>

        <div className="ds-settings__row">
          <div className="ds-settings__copy">
            <strong>Bounding-box overlay</strong>
            <span>Show detection boxes by default in analysis.</span>
          </div>
          <SettingSwitch
            checked={settings.showBoundingBoxes}
            onChange={(showBoundingBoxes) =>
              updateSettings({ showBoundingBoxes })
            }
          />
        </div>
      </section>

      <section className="ds-settings__section">
        <header className="ds-settings__section-header">
          <span className="ds-settings__icon">
            <ClipboardCheck size={18} />
          </span>
          <div>
            <h2>Human review</h2>
            <p>Choose your preferred review queue layout.</p>
          </div>
        </header>

        <div className="ds-settings__row">
          <div className="ds-settings__copy">
            <strong>Compact review cards</strong>
            <span>Use a denser review list when supported.</span>
          </div>
          <SettingSwitch
            checked={settings.compactReviewCards}
            onChange={(compactReviewCards) =>
              updateSettings({ compactReviewCards })
            }
          />
        </div>
      </section>

      <footer className="ds-settings__footer">
        <p>Preferences are saved locally in this browser.</p>
        <button
          type="button"
          className="ds-settings__reset"
          onClick={() => {
            if (window.confirm("Reset all DeepSight preferences?")) {
              resetSettings();
            }
          }}
        >
          <RotateCcw size={15} />
          Reset to defaults
        </button>
      </footer>
    </div>
  );
}
