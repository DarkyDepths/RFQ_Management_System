"use client";

import {
  createContext,
  useContext,
  useEffect,
  useReducer,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { MOCK_REPLY_DELAY_MS, generateMockReply } from "@/lib/copilot-mock";
import type { CopilotMessage, CopilotMode, CopilotStatus } from "@/types/copilot";

const STORAGE_KEY = "copilot:state:v1";

export const DEFAULT_DRAWER_WIDTH = 420;
export const MIN_DRAWER_WIDTH = 360;
export const MAX_DRAWER_WIDTH = 720;

interface CopilotState {
  open: boolean;
  mode: CopilotMode;
  threadId: string | null;
  messages: CopilotMessage[];
  status: CopilotStatus;
  input: string;
}

interface PersistedCopilotState {
  mode: CopilotMode;
  threadId: string | null;
  messages: CopilotMessage[];
}

type CopilotAction =
  | { type: "OPEN"; mode: CopilotMode }
  | { type: "CLOSE" }
  | { type: "NEW_CHAT" }
  | { type: "SET_INPUT"; value: string }
  | { type: "SEND_USER_MESSAGE"; message: CopilotMessage }
  | { type: "RECEIVE_ASSISTANT"; message: CopilotMessage }
  | { type: "HYDRATE"; payload: PersistedCopilotState };

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
      // Mode change (or first open in a new mode) discards the prior conversation.
      // Multi-thread caching is intentionally deferred to the backend (Batch 3+).
      if (!modesEqual(state.mode, action.mode)) {
        return { ...INITIAL_STATE, open: true, mode: action.mode };
      }
      return { ...state, open: true };
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
    case "SEND_USER_MESSAGE":
      return {
        ...state,
        messages: [...state.messages, action.message],
        threadId: state.threadId ?? crypto.randomUUID(),
        status: "loading",
        input: "",
      };
    case "RECEIVE_ASSISTANT":
      return {
        ...state,
        messages: [...state.messages, action.message],
        status: "idle",
      };
    case "HYDRATE":
      return {
        ...state,
        mode: action.payload.mode,
        threadId: action.payload.threadId,
        messages: action.payload.messages,
      };
    default:
      return state;
  }
}

function readPersisted(): PersistedCopilotState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedCopilotState;
    if (!parsed || typeof parsed !== "object") return null;
    if (!parsed.mode || (parsed.mode.kind !== "general" && parsed.mode.kind !== "rfq_bound")) {
      return null;
    }
    if (!Array.isArray(parsed.messages)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writePersisted(state: CopilotState): void {
  if (typeof window === "undefined") return;
  try {
    const payload: PersistedCopilotState = {
      mode: state.mode,
      threadId: state.threadId,
      messages: state.messages,
    };
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // sessionStorage can fail in private browsing or when quota is hit; silently ignore.
  }
}

interface CopilotContextValue extends CopilotState {
  openCopilot: (mode: CopilotMode) => void;
  closeCopilot: () => void;
  newChat: () => void;
  setInput: (value: string) => void;
  sendUserMessage: (content: string) => void;
  drawerWidth: number;
  setDrawerWidth: (next: number) => void;
  isResizing: boolean;
  setResizing: (next: boolean) => void;
}

const CopilotContext = createContext<CopilotContextValue | null>(null);

export function CopilotProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const [drawerWidth, setDrawerWidthState] = useState(DEFAULT_DRAWER_WIDTH);
  const [isResizing, setResizing] = useState(false);
  const pendingReplyRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hydratedRef = useRef(false);

  const setDrawerWidth = (next: number) => {
    const clamped = Math.min(MAX_DRAWER_WIDTH, Math.max(MIN_DRAWER_WIDTH, next));
    setDrawerWidthState(clamped);
  };

  // Hydrate from sessionStorage after mount to avoid SSR/CSR divergence.
  useEffect(() => {
    const persisted = readPersisted();
    if (persisted) {
      dispatch({ type: "HYDRATE", payload: persisted });
    }
    hydratedRef.current = true;
  }, []);

  // Persist mode/threadId/messages on change. Drawer open/closed and input are deliberately not persisted.
  useEffect(() => {
    if (!hydratedRef.current) return;
    writePersisted(state);
  }, [state.mode, state.threadId, state.messages]);

  // Cancel any in-flight mock reply on unmount.
  useEffect(() => {
    return () => {
      if (pendingReplyRef.current) clearTimeout(pendingReplyRef.current);
    };
  }, []);

  const cancelPendingReply = () => {
    if (pendingReplyRef.current) {
      clearTimeout(pendingReplyRef.current);
      pendingReplyRef.current = null;
    }
  };

  const openCopilot = (mode: CopilotMode) => {
    if (!modesEqual(state.mode, mode)) {
      cancelPendingReply();
    }
    dispatch({ type: "OPEN", mode });
  };

  const closeCopilot = () => dispatch({ type: "CLOSE" });

  const newChat = () => {
    cancelPendingReply();
    dispatch({ type: "NEW_CHAT" });
  };

  const setInput = (value: string) => dispatch({ type: "SET_INPUT", value });

  const sendUserMessage = (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;
    if (state.status === "loading") return;

    cancelPendingReply();

    const userMessage: CopilotMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };
    dispatch({ type: "SEND_USER_MESSAGE", message: userMessage });

    const modeAtSend = state.mode;
    pendingReplyRef.current = setTimeout(() => {
      const reply = generateMockReply(modeAtSend);
      dispatch({ type: "RECEIVE_ASSISTANT", message: reply });
      pendingReplyRef.current = null;
    }, MOCK_REPLY_DELAY_MS);
  };

  const value: CopilotContextValue = {
    ...state,
    openCopilot,
    closeCopilot,
    newChat,
    setInput,
    sendUserMessage,
    drawerWidth,
    setDrawerWidth,
    isResizing,
    setResizing,
  };

  return <CopilotContext.Provider value={value}>{children}</CopilotContext.Provider>;
}

export function useCopilotContext() {
  return useContext(CopilotContext);
}
