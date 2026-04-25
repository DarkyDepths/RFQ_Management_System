"use client";

import { useEffect, useState } from "react";

import { apiConfig } from "@/config/api";
import { getRfqReminders } from "@/connectors/manager/reminders";
import type { ReminderModel } from "@/models/manager/rfq";

interface ReminderState {
  error: string | null;
  loading: boolean;
  reminders: ReminderModel[];
}

export function useRfqReminders(rfqId: string) {
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<ReminderState>({
    error: null,
    loading: true,
    reminders: [],
  });

  useEffect(() => {
    let active = true;

    if (apiConfig.useMockData) {
      setState({
        error:
          "Reminder service stays live-only in this phase. Switch to live mode for RFQ reminder truth.",
        loading: false,
        reminders: [],
      });
      return () => {
        active = false;
      };
    }

    setState((current) => ({
      ...current,
      error: null,
      loading: true,
    }));

    async function load() {
      try {
        const reminders = await getRfqReminders(rfqId);

        if (!active) {
          return;
        }

        setState({
          error: null,
          loading: false,
          reminders,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          error:
            error instanceof Error
              ? error.message
              : "Reminders could not be loaded.",
          loading: false,
          reminders: [],
        });
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [reloadKey, rfqId]);

  return {
    ...state,
    refresh: () => setReloadKey((value) => value + 1),
  };
}
