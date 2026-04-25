"use client";

import { useEffect, useState } from "react";

import { getStageWorkspace } from "@/connectors/manager/stages";
import type { StageWorkspaceModel } from "@/models/manager/stage";

interface StageWorkspaceState {
  error: string | null;
  loading: boolean;
  workspace: StageWorkspaceModel | null;
}

export function useStageWorkspace(
  rfqId: string,
  stageId?: string | null,
) {
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<StageWorkspaceState>({
    error: null,
    loading: Boolean(stageId),
    workspace: null,
  });

  useEffect(() => {
    let active = true;

    if (!stageId) {
      setState({
        error: null,
        loading: false,
        workspace: null,
      });
      return () => {
        active = false;
      };
    }

    setState((current) => ({
      error: null,
      loading: true,
      workspace: current.workspace?.id === stageId ? current.workspace : null,
    }));

    async function load() {
      try {
        const workspace = await getStageWorkspace(rfqId, stageId);

        if (!active) {
          return;
        }

        setState({
          error: workspace ? null : "No current-stage workspace is available.",
          loading: false,
          workspace,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          error:
            error instanceof Error
              ? error.message
              : "Stage workspace could not be loaded.",
          loading: false,
          workspace: null,
        });
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [reloadKey, rfqId, stageId]);

  return {
    ...state,
    refresh: () => setReloadKey((value) => value + 1),
  };
}
