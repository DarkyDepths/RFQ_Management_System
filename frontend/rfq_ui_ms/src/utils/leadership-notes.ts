import type {
  LeadershipNoteIntent,
  LeadershipNoteState,
} from "@/models/manager/leadership-note";

export const leadershipNoteIntentMeta: Record<
  LeadershipNoteIntent,
  {
    helper: string;
    label: string;
  }
> = {
  blocker_resolution: {
    helper: "Ask for blocker resolution path and escalation posture.",
    label: "Blocker Resolution",
  },
  leadership_attention: {
    helper: "Flag RFQ leadership attention without changing workflow ownership.",
    label: "Leadership Attention",
  },
  loss_rationale: {
    helper: "Request the loss reason and the learning to carry forward.",
    label: "Loss Rationale",
  },
  status_clarification: {
    helper: "Ask for a concise strategic status readout and owner context.",
    label: "Status Clarification",
  },
};

export const leadershipNoteStateMeta: Record<
  LeadershipNoteState,
  {
    helper: string;
    label: string;
    tone: "steel" | "gold" | "emerald" | "rose" | "pending";
  }
> = {
  acknowledged: {
    helper: "Manager has acknowledged the request and accepted response ownership.",
    label: "Acknowledged",
    tone: "gold",
  },
  closed: {
    helper: "Thread closed with a recorded management response.",
    label: "Closed",
    tone: "emerald",
  },
  open: {
    helper: "Awaiting manager acknowledgment.",
    label: "Open",
    tone: "rose",
  },
  replied: {
    helper: "Manager replied; thread is ready for review or closure.",
    label: "Replied",
    tone: "steel",
  },
};
