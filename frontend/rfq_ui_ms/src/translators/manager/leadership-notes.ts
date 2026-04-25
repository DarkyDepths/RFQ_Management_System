import type {
  LeadershipNoteEntryModel,
  LeadershipNoteEntryResponse,
  LeadershipNoteThreadModel,
  LeadershipNoteThreadResponse,
} from "@/models/manager/leadership-note";
import { formatDate } from "@/utils/format";
import {
  leadershipNoteIntentMeta,
  leadershipNoteStateMeta,
} from "@/utils/leadership-notes";

function translateLeadershipNoteEntry(
  entry: LeadershipNoteEntryResponse,
): LeadershipNoteEntryModel {
  return {
    actorName: entry.actorName,
    actorRole: entry.actorRole,
    createdAtValue: entry.createdAt,
    createdLabel: formatDate(entry.createdAt),
    id: entry.id,
    kind: entry.kind,
    message: entry.message,
    state: entry.state,
  };
}

export function translateLeadershipNoteThread(
  thread: LeadershipNoteThreadResponse,
): LeadershipNoteThreadModel {
  const entries = thread.entries.map(translateLeadershipNoteEntry);
  const latestManagerReply = [...entries]
    .reverse()
    .find((entry) => entry.kind === "message" && entry.actorRole === "manager");
  const latestExecutiveMessage = [...entries]
    .reverse()
    .find((entry) => entry.kind === "message" && entry.actorRole === "executive");
  const stateMeta = leadershipNoteStateMeta[thread.state];

  return {
    createdAtValue: thread.createdAt,
    createdBy: thread.createdBy,
    createdLabel: formatDate(thread.createdAt),
    entries,
    hasManagerReply: Boolean(latestManagerReply?.message),
    id: thread.id,
    intent: thread.intent,
    intentLabel: leadershipNoteIntentMeta[thread.intent].label,
    latestExecutiveMessage: latestExecutiveMessage?.message,
    latestManagerResponse: latestManagerReply?.message,
    latestManagerResponseLabel: latestManagerReply?.createdLabel,
    rfqId: thread.rfqId,
    state: thread.state,
    stateLabel: stateMeta.label,
    stateTone: stateMeta.tone,
    updatedAtValue: thread.updatedAt,
    updatedLabel: formatDate(thread.updatedAt),
    waitingOnManager: thread.state === "open" || thread.state === "acknowledged",
  };
}
