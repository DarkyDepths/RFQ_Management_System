import type {
  CreateLeadershipNoteInput,
  LeadershipNoteActorRole,
  LeadershipNoteEntryResponse,
  LeadershipNoteState,
  LeadershipNoteThreadResponse,
  ReplyLeadershipNoteInput,
} from "@/models/manager/leadership-note";

const leadershipThreadsByRfq: Record<string, LeadershipNoteThreadResponse[]> = {
  "RFQ-2026-0126": [
    {
      createdAt: "2026-03-31T09:15:00Z",
      createdBy: "Executive Leadership",
      entries: [
        {
          actorName: "Executive Leadership",
          actorRole: "executive",
          createdAt: "2026-03-31T09:15:00Z",
          id: "lead-126-1-entry-1",
          kind: "message",
          message:
            "Submission is blocked. Provide the blocker resolution plan, owner, and whether leadership escalation is needed before deadline risk deepens.",
        },
      ],
      id: "lead-126-1",
      intent: "blocker_resolution",
      rfqId: "RFQ-2026-0126",
      state: "open",
      updatedAt: "2026-03-31T09:15:00Z",
    },
  ],
  "RFQ-2026-0142": [
    {
      createdAt: "2026-03-29T09:20:00Z",
      createdBy: "Executive Leadership",
      entries: [
        {
          actorName: "Executive Leadership",
          actorRole: "executive",
          createdAt: "2026-03-29T09:20:00Z",
          id: "lead-142-1-entry-1",
          kind: "message",
          message:
            "Provide a short status clarification on committee readiness and whether any blocker remains material for executive watch.",
        },
        {
          actorName: "Estimation Manager",
          actorRole: "manager",
          createdAt: "2026-03-29T10:05:00Z",
          id: "lead-142-1-entry-2",
          kind: "status_change",
          state: "acknowledged",
        },
        {
          actorName: "Estimation Manager",
          actorRole: "manager",
          createdAt: "2026-03-30T07:55:00Z",
          id: "lead-142-1-entry-3",
          kind: "message",
          message:
            "Committee package is ready pending one low-severity cabinet finish clarification. No executive escalation is required at this point.",
        },
        {
          actorName: "Estimation Manager",
          actorRole: "manager",
          createdAt: "2026-03-30T08:20:00Z",
          id: "lead-142-1-entry-4",
          kind: "status_change",
          state: "closed",
        },
      ],
      id: "lead-142-1",
      intent: "status_clarification",
      rfqId: "RFQ-2026-0142",
      state: "closed",
      updatedAt: "2026-03-30T08:20:00Z",
    },
  ],
  "RFQ-2026-0151": [
    {
      createdAt: "2026-03-30T13:10:00Z",
      createdBy: "Executive Leadership",
      entries: [
        {
          actorName: "Executive Leadership",
          actorRole: "executive",
          createdAt: "2026-03-30T13:10:00Z",
          id: "lead-151-1-entry-1",
          kind: "message",
          message:
            "This RFQ is showing scope drift. Confirm whether the calibration station gap threatens schedule or margin and whether leadership should intervene.",
        },
        {
          actorName: "Estimation Manager",
          actorRole: "manager",
          createdAt: "2026-03-30T13:42:00Z",
          id: "lead-151-1-entry-2",
          kind: "status_change",
          state: "acknowledged",
        },
        {
          actorName: "Estimation Manager",
          actorRole: "manager",
          createdAt: "2026-03-30T16:45:00Z",
          id: "lead-151-1-entry-3",
          kind: "message",
          message:
            "No leadership intervention needed yet. The gap is real but contained; engineering clarification is underway and schedule posture remains recoverable.",
        },
      ],
      id: "lead-151-1",
      intent: "leadership_attention",
      rfqId: "RFQ-2026-0151",
      state: "replied",
      updatedAt: "2026-03-30T16:45:00Z",
    },
  ],
};

function cloneEntry(entry: LeadershipNoteEntryResponse): LeadershipNoteEntryResponse {
  return {
    actorName: entry.actorName,
    actorRole: entry.actorRole,
    createdAt: entry.createdAt,
    id: entry.id,
    kind: entry.kind,
    message: entry.message,
    state: entry.state,
  };
}

function cloneThread(thread: LeadershipNoteThreadResponse): LeadershipNoteThreadResponse {
  return {
    createdAt: thread.createdAt,
    createdBy: thread.createdBy,
    entries: thread.entries.map(cloneEntry),
    id: thread.id,
    intent: thread.intent,
    rfqId: thread.rfqId,
    state: thread.state,
    updatedAt: thread.updatedAt,
  };
}

function getThreads(rfqId: string) {
  if (!leadershipThreadsByRfq[rfqId]) {
    leadershipThreadsByRfq[rfqId] = [];
  }

  return leadershipThreadsByRfq[rfqId];
}

function appendStatusChange(
  thread: LeadershipNoteThreadResponse,
  actorName: string,
  actorRole: LeadershipNoteActorRole,
  state: LeadershipNoteState,
  createdAt: string,
) {
  thread.entries.push({
    actorName,
    actorRole,
    createdAt,
    id: `${thread.id}-status-${thread.entries.length + 1}`,
    kind: "status_change",
    state,
  });
  thread.state = state;
  thread.updatedAt = createdAt;
}

function ensureSingleOpenThread(rfqId: string) {
  const openThread = getThreads(rfqId).find((thread) => thread.state !== "closed");

  if (openThread) {
    throw new Error(
      "A leadership note thread is already active for this RFQ. Close the current thread before opening a new one.",
    );
  }
}

function requireThread(
  rfqId: string,
  threadId: string,
) {
  const thread = getThreads(rfqId).find((candidate) => candidate.id === threadId);

  if (!thread) {
    throw new Error("Leadership note thread not found.");
  }

  return thread;
}

export function listDemoLeadershipNoteThreads(rfqId?: string): LeadershipNoteThreadResponse[] {
  const threads = rfqId
    ? getThreads(rfqId)
    : Object.values(leadershipThreadsByRfq).flatMap((items) => items);

  return threads
    .slice()
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
    .map(cloneThread);
}

export function createDemoLeadershipNote(
  rfqId: string,
  input: CreateLeadershipNoteInput,
  actorName: string,
): LeadershipNoteThreadResponse {
  ensureSingleOpenThread(rfqId);

  const createdAt = new Date().toISOString();
  const thread: LeadershipNoteThreadResponse = {
    createdAt,
    createdBy: actorName,
    entries: [
      {
        actorName,
        actorRole: "executive",
        createdAt,
        id: `lead-${rfqId.toLowerCase()}-${Date.now()}-entry-1`,
        kind: "message",
        message: input.message.trim(),
      },
    ],
    id: `lead-${rfqId.toLowerCase()}-${Date.now()}`,
    intent: input.intent,
    rfqId,
    state: "open",
    updatedAt: createdAt,
  };

  getThreads(rfqId).unshift(thread);
  return cloneThread(thread);
}

export function acknowledgeDemoLeadershipNote(
  rfqId: string,
  threadId: string,
  actorName: string,
): LeadershipNoteThreadResponse {
  const thread = requireThread(rfqId, threadId);

  if (thread.state === "closed") {
    throw new Error("Closed leadership note threads cannot be acknowledged.");
  }

  if (thread.state === "open") {
    appendStatusChange(thread, actorName, "manager", "acknowledged", new Date().toISOString());
  }

  return cloneThread(thread);
}

export function replyDemoLeadershipNote(
  rfqId: string,
  threadId: string,
  input: ReplyLeadershipNoteInput,
  actorName: string,
): LeadershipNoteThreadResponse {
  const thread = requireThread(rfqId, threadId);

  if (thread.state === "closed") {
    throw new Error("Closed leadership note threads cannot be replied to.");
  }

  const createdAt = new Date().toISOString();

  if (thread.state === "open") {
    appendStatusChange(thread, actorName, "manager", "acknowledged", createdAt);
  }

  thread.entries.push({
    actorName,
    actorRole: "manager",
    createdAt,
    id: `${thread.id}-reply-${thread.entries.length + 1}`,
    kind: "message",
    message: input.message.trim(),
  });
  thread.state = "replied";
  thread.updatedAt = createdAt;

  return cloneThread(thread);
}

export function closeDemoLeadershipNote(
  rfqId: string,
  threadId: string,
  actorName: string,
): LeadershipNoteThreadResponse {
  const thread = requireThread(rfqId, threadId);

  if (thread.state === "closed") {
    return cloneThread(thread);
  }

  const hasManagerReply = thread.entries.some(
    (entry) => entry.kind === "message" && entry.actorRole === "manager" && entry.message,
  );

  if (!hasManagerReply) {
    throw new Error(
      "Leadership note threads require at least one manager reply before they can be closed.",
    );
  }

  appendStatusChange(thread, actorName, "manager", "closed", new Date().toISOString());
  return cloneThread(thread);
}
