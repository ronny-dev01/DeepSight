
import { useCallback, useEffect, useState } from "react";

export type WorkspaceSettings = {
  autoRefresh: boolean;
  refreshInterval: number;
  defaultConfidence: number;
  showBoundingBoxes: boolean;
  defaultSection:
    | "overview"
    | "projects"
    | "sonar-analysis"
    | "processing-jobs"
    | "review-queue"
    | "reports";
  compactReviewCards: boolean;
};

export const DEFAULT_WORKSPACE_SETTINGS: WorkspaceSettings = {
  autoRefresh: true,
  refreshInterval: 5,
  defaultConfidence: 0,
  showBoundingBoxes: true,
  defaultSection: "overview",
  compactReviewCards: false,
};

const STORAGE_KEY = "deepsight.workspace-settings";

export function readWorkspaceSettings(): WorkspaceSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return DEFAULT_WORKSPACE_SETTINGS;

    return {
      ...DEFAULT_WORKSPACE_SETTINGS,
      ...JSON.parse(stored),
    };
  } catch {
    return DEFAULT_WORKSPACE_SETTINGS;
  }
}

export function saveWorkspaceSettings(
  settings: WorkspaceSettings,
): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function useWorkspaceSettings() {
  const [settings, setSettings] =
    useState<WorkspaceSettings>(readWorkspaceSettings);

  useEffect(() => {
    saveWorkspaceSettings(settings);
  }, [settings]);

  const updateSettings = useCallback(
    (patch: Partial<WorkspaceSettings>) => {
      setSettings((current) => ({
        ...current,
        ...patch,
      }));
    },
    [],
  );

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_WORKSPACE_SETTINGS);
  }, []);

  return {
    settings,
    updateSettings,
    resetSettings,
  };
}
