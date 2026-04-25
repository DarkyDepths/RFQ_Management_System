"use client";

import { useEffect, useState } from "react";

import {
  acknowledgeLeadershipNote,
  closeLeadershipNote,
  createLeadershipNote,
  listLeadershipNotes,
  replyLeadershipNote,
} from "@/connectors/manager/leadership-notes";
import type {
  CreateLeadershipNoteInput,
  LeadershipNoteThreadModel,
  ReplyLeadershipNoteInput,
} from "@/models/manager/leadership-note";

interface LeadershipNotesState {
  error: string | null;
  loading: boolean;
  threads: LeadershipNoteThreadModel[];
}

export interface LeadershipNotesController extends LeadershipNotesState {
  acknowledgeThread: (threadId: string) => Promise<LeadershipNoteThreadModel>;
  closeThread: (threadId: string) => Promise<LeadershipNoteThreadModel>;
  createThread: (
    input: CreateLeadershipNoteInput,
  ) => Promise<LeadershipNoteThreadModel>;
  refresh: () => void;
  replyToThread: (
    threadId: string,
    input: ReplyLeadershipNoteInput,
  ) => Promise<LeadershipNoteThreadModel>;
}

export function useLeadershipNotes(
  rfqId: string,
  {
    actorName,
    enabled,
  }: {
    actorName: string;
    enabled: boolean;
  },
): LeadershipNotesController {
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<LeadershipNotesState>({
    error: null,
    loading: enabled,
    threads: [],
  });

  useEffect(() => {
    if (!enabled) {
      setState({
        error: null,
        loading: false,
        threads: [],
      });
      return;
    }

    let active = true;

    async function load() {
      setState((current) => ({
        ...current,
        error: null,
        loading: true,
      }));

      try {
        const threads = await listLeadershipNotes(rfqId);

        if (!active) {
          return;
        }

        setState({
          error: null,
          loading: false,
          threads,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          error:
            error instanceof Error
              ? error.message
              : "Leadership Notes could not be loaded.",
          loading: false,
          threads: [],
        });
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [enabled, reloadKey, rfqId]);

  async function runMutation<T>(
    action: () => Promise<T>,
  ) {
    const result = await action();
    setReloadKey((value) => value + 1);
    return result;
  }

  return {
    ...state,
    acknowledgeThread: (threadId) =>
      runMutation(() => acknowledgeLeadershipNote(rfqId, threadId, actorName)),
    closeThread: (threadId) =>
      runMutation(() => closeLeadershipNote(rfqId, threadId, actorName)),
    createThread: (input) =>
      runMutation(() => createLeadershipNote(rfqId, input, actorName)),
    refresh: () => setReloadKey((value) => value + 1),
    replyToThread: (threadId, input) =>
      runMutation(() => replyLeadershipNote(rfqId, threadId, input, actorName)),
  };
}
