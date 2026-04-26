"use client";

import {
  createContext,
  useContext,
  useReducer,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  createNewThread,
  openThread,
  sendTurn,
} from "@/connectors/copilot/threads";
import type { CopilotMessage, CopilotMode, CopilotStatus } from "@/types/copilot";

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

type CopilotAction =
  | { type: "OPEN"; mode: CopilotMode; needsFetch: boolean }
  | { type: "CLOSE" }
  | { type: "NEW_CHAT" }
  | { type: "SET_INPUT"; value: string }
  | { type: "SEND_USER_MESSAGE"; message: CopilotMessage }
  | { type: "RECEIVE_ASSISTANT"; message: CopilotMessage }
  | { type: "SET_THREAD_ID"; threadId: string }
  | {
      type: "BACKEND_OPEN_OK";
      threadId: string;
      messages: CopilotMessage[];
    }
  | { type: "BACKEND_ERROR" };

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
    case "OPEN": {
      // Already open in this exact mode — no-op.
      if (state.open && modesEqual(state.mode, action.mode)) {
        return state;
      }
      // Mode change discards any prior in-memory conversation. Multi-thread
      // caching is the backend ThreadController's job.
      if (!modesEqual(state.mode, action.mode)) {
        return {
          ...INITIAL_STATE,
          open: true,
          mode: action.mode,
          status: action.needsFetch ? "loading" : "idle",
        };
      }
      // Same mode reopen from closed.
      return {
        ...state,
        open: true,
        status: action.needsFetch ? "loading" : state.status,
      };
    }
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
        status: "loading",
        input: "",
      };
    case "RECEIVE_ASSISTANT":
      return {
        ...state,
        messages: [...state.messages, action.message],
        status: "idle",
      };
    case "SET_THREAD_ID":
      return { ...state, threadId: action.threadId };
    case "BACKEND_OPEN_OK":
      return {
        ...state,
        threadId: action.threadId,
        messages: action.messages,
        status: "idle",
      };
    case "BACKEND_ERROR":
      return { ...state, status: "error" };
    default:
      return state;
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

  // Stale-response guard: every async op gets a token; older tokens drop their
  // result. Prevents an in-flight /threads/open response from a previous mode
  // overwriting state after the user has switched mode mid-fetch.
  const fetchTokenRef = useRef(0);

  const setDrawerWidth = (next: number) => {
    const clamped = Math.min(MAX_DRAWER_WIDTH, Math.max(MIN_DRAWER_WIDTH, next));
    setDrawerWidthState(clamped);
  };

  const openCopilot = (mode: CopilotMode) => {
    if (state.open && modesEqual(state.mode, mode)) return;

    const isModeChange = !modesEqual(state.mode, mode);
    const needsFetch = isModeChange || state.threadId === null;

    dispatch({ type: "OPEN", mode, needsFetch });

    if (!needsFetch) return;

    const token = ++fetchTokenRef.current;
    void (async () => {
      try {
        const result = await openThread(mode);
        if (token !== fetchTokenRef.current) return;
        dispatch({
          type: "BACKEND_OPEN_OK",
          threadId: result.threadId,
          messages: result.messages,
        });
      } catch {
        if (token !== fetchTokenRef.current) return;
        dispatch({ type: "BACKEND_ERROR" });
      }
    })();
  };

  const closeCopilot = () => dispatch({ type: "CLOSE" });

  const newChat = () => {
    if (state.status === "loading") return;
    // Cancel any in-flight responses by bumping the token. Local state clears
    // immediately; the next sendUserMessage will create a fresh thread on
    // demand via /threads/new.
    fetchTokenRef.current++;
    dispatch({ type: "NEW_CHAT" });
  };

  const setInput = (value: string) => dispatch({ type: "SET_INPUT", value });

  const sendUserMessage = (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;
    if (state.status === "loading") return;

    const userMessage: CopilotMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };
    dispatch({ type: "SEND_USER_MESSAGE", message: userMessage });

    const modeAtSend = state.mode;
    let threadId = state.threadId;
    const token = ++fetchTokenRef.current;

    void (async () => {
      try {
        if (threadId === null) {
          const newResult = await createNewThread(modeAtSend);
          if (token !== fetchTokenRef.current) return;
          threadId = newResult.threadId;
          dispatch({ type: "SET_THREAD_ID", threadId });
        }

        const turnResult = await sendTurn(threadId, trimmed);
        if (token !== fetchTokenRef.current) return;
        dispatch({
          type: "RECEIVE_ASSISTANT",
          message: turnResult.assistantMessage,
        });
      } catch {
        if (token !== fetchTokenRef.current) return;
        dispatch({ type: "BACKEND_ERROR" });
      }
    })();
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
