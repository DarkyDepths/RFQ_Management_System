export type LeadershipNoteIntent =
  | "status_clarification"
  | "blocker_resolution"
  | "loss_rationale"
  | "leadership_attention";

export type LeadershipNoteState =
  | "open"
  | "acknowledged"
  | "replied"
  | "closed";

export type LeadershipNoteActorRole = "executive" | "manager";
export type LeadershipNoteEntryKind = "message" | "status_change";

export interface LeadershipNoteEntryResponse {
  actorName: string;
  actorRole: LeadershipNoteActorRole;
  createdAt: string;
  id: string;
  kind: LeadershipNoteEntryKind;
  message?: string;
  state?: LeadershipNoteState;
}

export interface LeadershipNoteThreadResponse {
  createdAt: string;
  createdBy: string;
  entries: LeadershipNoteEntryResponse[];
  id: string;
  intent: LeadershipNoteIntent;
  rfqId: string;
  state: LeadershipNoteState;
  updatedAt: string;
}

export interface LeadershipNoteEntryModel {
  actorName: string;
  actorRole: LeadershipNoteActorRole;
  createdAtValue: string;
  createdLabel: string;
  id: string;
  kind: LeadershipNoteEntryKind;
  message?: string;
  state?: LeadershipNoteState;
}

export interface LeadershipNoteThreadModel {
  createdAtValue: string;
  createdBy: string;
  createdLabel: string;
  entries: LeadershipNoteEntryModel[];
  hasManagerReply: boolean;
  id: string;
  intent: LeadershipNoteIntent;
  intentLabel: string;
  latestExecutiveMessage?: string;
  latestManagerResponse?: string;
  latestManagerResponseLabel?: string;
  rfqId: string;
  state: LeadershipNoteState;
  stateLabel: string;
  stateTone: "steel" | "gold" | "emerald" | "rose" | "pending";
  updatedAtValue: string;
  updatedLabel: string;
  waitingOnManager: boolean;
}

export interface CreateLeadershipNoteInput {
  intent: LeadershipNoteIntent;
  message: string;
}

export interface ReplyLeadershipNoteInput {
  message: string;
}
