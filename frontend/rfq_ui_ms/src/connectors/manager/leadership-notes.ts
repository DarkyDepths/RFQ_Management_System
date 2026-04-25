import { apiConfig } from "@/config/api";
import {
  acknowledgeDemoLeadershipNote,
  closeDemoLeadershipNote,
  createDemoLeadershipNote,
  listDemoLeadershipNoteThreads,
  replyDemoLeadershipNote,
} from "@/demo/manager/leadership-notes";
import type {
  CreateLeadershipNoteInput,
  LeadershipNoteThreadModel,
  ReplyLeadershipNoteInput,
} from "@/models/manager/leadership-note";
import { translateLeadershipNoteThread } from "@/translators/manager/leadership-notes";
import { sleep } from "@/utils/async";

export const leadershipNotesUnavailableMessage =
  "Leadership Notes are not connected outside demo mode yet.";

function assertDemoSupport() {
  if (!apiConfig.useMockData) {
    throw new Error(leadershipNotesUnavailableMessage);
  }
}

export async function listLeadershipNotes(
  rfqId?: string,
): Promise<LeadershipNoteThreadModel[]> {
  assertDemoSupport();
  await sleep(Math.round(apiConfig.demoLatencyMs * 0.55));

  return listDemoLeadershipNoteThreads(rfqId).map(translateLeadershipNoteThread);
}

export async function createLeadershipNote(
  rfqId: string,
  input: CreateLeadershipNoteInput,
  actorName: string,
): Promise<LeadershipNoteThreadModel> {
  assertDemoSupport();
  await sleep(Math.round(apiConfig.demoLatencyMs * 0.45));

  return translateLeadershipNoteThread(
    createDemoLeadershipNote(rfqId, input, actorName),
  );
}

export async function acknowledgeLeadershipNote(
  rfqId: string,
  threadId: string,
  actorName: string,
): Promise<LeadershipNoteThreadModel> {
  assertDemoSupport();
  await sleep(Math.round(apiConfig.demoLatencyMs * 0.4));

  return translateLeadershipNoteThread(
    acknowledgeDemoLeadershipNote(rfqId, threadId, actorName),
  );
}

export async function replyLeadershipNote(
  rfqId: string,
  threadId: string,
  input: ReplyLeadershipNoteInput,
  actorName: string,
): Promise<LeadershipNoteThreadModel> {
  assertDemoSupport();
  await sleep(Math.round(apiConfig.demoLatencyMs * 0.45));

  return translateLeadershipNoteThread(
    replyDemoLeadershipNote(rfqId, threadId, input, actorName),
  );
}

export async function closeLeadershipNote(
  rfqId: string,
  threadId: string,
  actorName: string,
): Promise<LeadershipNoteThreadModel> {
  assertDemoSupport();
  await sleep(Math.round(apiConfig.demoLatencyMs * 0.35));

  return translateLeadershipNoteThread(
    closeDemoLeadershipNote(rfqId, threadId, actorName),
  );
}
