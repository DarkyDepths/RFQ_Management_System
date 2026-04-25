"use client";

import { createContext, useContext, useReducer, type ReactNode } from "react";

import type { CopilotMessage, CopilotMode, CopilotStatus } from "@/types/copilot";

interface CopilotState {
  open: boolean;
  mode: CopilotMode;
  threadId: string | null;
  messages: CopilotMessage[];
  status: CopilotStatus;
  input: string;
}

type CopilotAction =
  | { type: "OPEN"; mode: CopilotMode }
  | { type: "CLOSE" }
  | { type: "NEW_CHAT" }
  | { type: "SET_INPUT"; value: string };

const DEFAULT_MODE: CopilotMode = { kind: "general" };

const INITIAL_STATE: CopilotState = {
  open: false,
  mode: DEFAULT_MODE,
  threadId: null,
  messages: [],
  status: "idle",
  input: "",
};

function modesEqual(a: CopilotMode, b: CopilotMode): boolean {
  if (a.kind !== b.kind) return false;
  if (a.kind === "rfq_bound" && b.kind === "rfq_bound") {
    return a.rfqId === b.rfqId;
  }
  return true;
}

function reducer(state: CopilotState, action: CopilotAction): CopilotState {
  switch (action.type) {
    case "OPEN":
      if (state.open && modesEqual(state.mode, action.mode)) {
        return state;
      }
      return {
        ...INITIAL_STATE,
        open: true,
        mode: action.mode,
      };
    case "CLOSE":
      return { ...state, open: false };
    case "NEW_CHAT":
      return {
        ...INITIAL_STATE,
        open: state.open,
        mode: state.mode,
      };
    case "SET_INPUT":
      return { ...state, input: action.value };
    default:
      return state;
  }
}

interface CopilotContextValue extends CopilotState {
  openCopilot: (mode: CopilotMode) => void;
  closeCopilot: () => void;
  newChat: () => void;
  setInput: (value: string) => void;
}

const CopilotContext = createContext<CopilotContextValue | null>(null);

export function CopilotProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  const value: CopilotContextValue = {
    ...state,
    openCopilot: (mode) => dispatch({ type: "OPEN", mode }),
    closeCopilot: () => dispatch({ type: "CLOSE" }),
    newChat: () => dispatch({ type: "NEW_CHAT" }),
    setInput: (value) => dispatch({ type: "SET_INPUT", value }),
  };

  return <CopilotContext.Provider value={value}>{children}</CopilotContext.Provider>;
}

export function useCopilotContext() {
  return useContext(CopilotContext);
}
