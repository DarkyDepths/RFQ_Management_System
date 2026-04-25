"use client";

import { useEffect, useState } from "react";

import { apiConfig } from "@/config/api";
import {
  getReminderRules,
  getReminderStats,
  listReminders,
} from "@/connectors/manager/reminders";
import type {
  ReminderModel,
  ReminderRuleModel,
  ReminderStatsModel,
} from "@/models/manager/rfq";

interface ReminderCenterState {
  error: string | null;
  loading: boolean;
  reminders: ReminderModel[];
  rules: ReminderRuleModel[];
  stats: ReminderStatsModel | null;
}

export function useReminderCenter() {
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<ReminderCenterState>({
    error: null,
    loading: true,
    reminders: [],
    rules: [],
    stats: null,
  });

  useEffect(() => {
    let active = true;

    if (apiConfig.useMockData) {
      setState({
        error:
          "Reminder service stays live-only in this phase. Switch to live mode for Reminder Center operations.",
        loading: false,
        reminders: [],
        rules: [],
        stats: null,
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
        const [reminders, stats, rules] = await Promise.all([
          listReminders(),
          getReminderStats(),
          getReminderRules(),
        ]);

        if (!active) {
          return;
        }

        setState({
          error: null,
          loading: false,
          reminders,
          rules,
          stats,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          error:
            error instanceof Error
              ? error.message
              : "Reminder Center could not be loaded.",
          loading: false,
          reminders: [],
          rules: [],
          stats: null,
        });
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [reloadKey]);

  return {
    ...state,
    refresh: () => setReloadKey((value) => value + 1),
  };
}
