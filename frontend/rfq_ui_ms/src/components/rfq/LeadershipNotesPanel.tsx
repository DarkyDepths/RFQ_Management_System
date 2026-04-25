"use client";

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCheck, MessageSquareQuote, Send, ShieldAlert } from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { RolePermissions } from "@/config/role-permissions";
import { useLeadershipNotes } from "@/hooks/use-leadership-notes";
import type {
  LeadershipNoteIntent,
  LeadershipNoteThreadModel,
} from "@/models/manager/leadership-note";
import type { AppRole } from "@/models/ui/role";
import {
  leadershipNoteIntentMeta,
  leadershipNoteStateMeta,
} from "@/utils/leadership-notes";

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function renderThreadEntry(thread: LeadershipNoteThreadModel) {
  return thread.entries.map((entry) => {
    if (entry.kind === "status_change" && entry.state) {
      return (
        <div
          key={entry.id}
          className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm font-medium text-foreground">
              {entry.actorName}
            </div>
            <div className="text-xs text-muted-foreground">{entry.createdLabel}</div>
          </div>
          <div className="mt-2 text-sm text-muted-foreground">
            Marked this thread as{" "}
            <span className="font-medium text-foreground">
              {leadershipNoteStateMeta[entry.state].label.toLowerCase()}
            </span>
            .
          </div>
        </div>
      );
    }

    return (
      <div
        key={entry.id}
        className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-sm font-medium text-foreground">{entry.actorName}</div>
            <div className="mt-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              {entry.actorRole === "executive" ? "Leadership note" : "Manager response"}
            </div>
          </div>
          <div className="text-xs text-muted-foreground">{entry.createdLabel}</div>
        </div>
        {entry.message ? (
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
            {entry.message}
          </p>
        ) : null}
      </div>
    );
  });
}

export function LeadershipNotesPanel({
  actorName,
  permissions,
  rfqId,
  role,
}: {
  actorName: string;
  permissions: RolePermissions;
  rfqId: string;
  role: AppRole;
}) {
  const canCreate = permissions.canCreateLeadershipNotes;
  const canRead = permissions.canReadLeadershipNotes;
  const canAcknowledge = permissions.canAcknowledgeLeadershipNotes;
  const canReply = permissions.canReplyLeadershipNotes;
  const canClose = permissions.canCloseLeadershipNotes;
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [composerOpen, setComposerOpen] = useState(false);
  const [intent, setIntent] = useState<LeadershipNoteIntent>("status_clarification");
  const [noteBody, setNoteBody] = useState("");
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});
  const leadershipNotes = useLeadershipNotes(rfqId, {
    actorName,
    enabled: canRead,
  });

  const activeThread = useMemo(
    () => leadershipNotes.threads.find((thread) => thread.state !== "closed") ?? null,
    [leadershipNotes.threads],
  );

  useEffect(() => {
    if (canCreate && leadershipNotes.threads.length === 0) {
      setComposerOpen(true);
    }
  }, [canCreate, leadershipNotes.threads.length]);

  if (!canRead) {
    return null;
  }

  async function runAction(
    actionKey: string,
    task: () => Promise<unknown>,
    successMessage: string,
  ) {
    setBusyAction(actionKey);
    setFeedback("");
    setError("");

    try {
      await task();
      setFeedback(successMessage);
      return true;
    } catch (actionError) {
      setError(
        getErrorMessage(actionError, "The leadership note action could not be completed."),
      );
      return false;
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCreateThread() {
    if (!noteBody.trim()) {
      setError("Leadership note text is required.");
      return;
    }

    const ok = await runAction(
      "create-thread",
      () =>
        leadershipNotes.createThread({
          intent,
          message: noteBody.trim(),
        }),
      "Leadership note created and routed to the department manager.",
    );

    if (ok) {
      setComposerOpen(false);
      setIntent("status_clarification");
      setNoteBody("");
    }
  }

  async function handleReply(threadId: string) {
    const replyBody = replyDrafts[threadId]?.trim();

    if (!replyBody) {
      setError("A manager reply is required before sending.");
      return;
    }

    const ok = await runAction(
      `reply-${threadId}`,
      () =>
        leadershipNotes.replyToThread(threadId, {
          message: replyBody,
        }),
      "Leadership note updated with a manager response.",
    );

    if (ok) {
      setReplyDrafts((current) => ({
        ...current,
        [threadId]: "",
      }));
    }
  }

  return (
    <div className="surface-panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="section-kicker">
            <MessageSquareQuote className="h-3.5 w-3.5" />
            Leadership Notes
          </div>
          <h3 className="mt-3 text-lg font-semibold text-foreground">
            {role === "executive"
              ? "Top-down leadership intervention"
              : "Leadership communication thread"}
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {role === "executive"
              ? "Use this thread to ask for clarification, blocker resolution, loss rationale, or leadership attention without changing workflow ownership."
              : "Acknowledge, reply, and close leadership threads here. This stream stays separate from operational notes and does not mutate RFQ truth."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="steel">{leadershipNotes.threads.length} thread(s)</Badge>
          {activeThread ? (
            <Badge variant={activeThread.stateTone}>
              {activeThread.stateLabel}
            </Badge>
          ) : (
            <Badge variant="emerald">No open thread</Badge>
          )}
        </div>
      </div>

      {feedback ? (
        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/8 p-4 text-sm text-emerald-700 dark:text-emerald-300">
          {feedback}
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/8 p-4 text-sm text-rose-700 dark:text-rose-300">
          {error}
        </div>
      ) : null}

      {leadershipNotes.loading ? (
        <div className="mt-5 space-y-3">
          <div className="h-24 animate-pulse rounded-xl border border-border bg-muted/20 dark:bg-white/[0.02]" />
          <div className="h-24 animate-pulse rounded-xl border border-border bg-muted/20 dark:bg-white/[0.02]" />
        </div>
      ) : leadershipNotes.error ? (
        <div className="mt-5 rounded-xl border border-steel-500/20 bg-steel-500/10 p-4 text-sm text-steel-700 dark:text-steel-300">
          {leadershipNotes.error}
        </div>
      ) : (
        <div className="mt-5 space-y-5">
          {canCreate ? (
            activeThread ? (
              <div className="rounded-xl border border-gold-500/20 bg-gold-500/10 p-4 text-sm text-gold-700 dark:text-gold-200">
                One leadership note thread is already active for this RFQ. Create a new thread after the current one is closed.
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-foreground">
                      Open a leadership note
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Create a lightweight management thread without affecting lifecycle state, stage progression, reminders, or files.
                    </div>
                  </div>
                  {leadershipNotes.threads.length > 0 ? (
                    <Button
                      onClick={() => setComposerOpen((value) => !value)}
                      size="sm"
                      variant="secondary"
                    >
                      {composerOpen ? "Hide composer" : "New leadership note"}
                    </Button>
                  ) : null}
                </div>

                <AnimatePresence initial={false}>
                  {composerOpen || leadershipNotes.threads.length === 0 ? (
                    <motion.div
                      animate={{ height: "auto", opacity: 1 }}
                      className="overflow-hidden"
                      exit={{ height: 0, opacity: 0 }}
                      initial={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.18 }}
                    >
                      <div className="mt-4 space-y-4">
                        <div className="flex flex-wrap gap-2">
                          {(Object.entries(leadershipNoteIntentMeta) as Array<
                            [LeadershipNoteIntent, (typeof leadershipNoteIntentMeta)[LeadershipNoteIntent]]
                          >).map(([value, meta]) => (
                            <Button
                              key={value}
                              onClick={() => setIntent(value)}
                              size="sm"
                              type="button"
                              variant={intent === value ? "default" : "secondary"}
                            >
                              {meta.label}
                            </Button>
                          ))}
                        </div>

                        <div className="rounded-xl border border-border bg-card p-4 dark:bg-white/[0.02]">
                          <div className="text-sm font-medium text-foreground">
                            {leadershipNoteIntentMeta[intent].label}
                          </div>
                          <div className="mt-1 text-sm text-muted-foreground">
                            {leadershipNoteIntentMeta[intent].helper}
                          </div>
                        </div>

                        <Textarea
                          onChange={(event) => setNoteBody(event.target.value)}
                          placeholder="Write the leadership note for the department manager"
                          rows={4}
                          value={noteBody}
                        />

                        <div className="flex flex-wrap gap-2">
                          <Button
                            disabled={!noteBody.trim() || busyAction === "create-thread"}
                            onClick={() => void handleCreateThread()}
                            type="button"
                          >
                            <Send className="h-4 w-4" />
                            Send leadership note
                          </Button>
                          {leadershipNotes.threads.length > 0 ? (
                            <Button
                              onClick={() => setComposerOpen(false)}
                              size="sm"
                              type="button"
                              variant="secondary"
                            >
                              Cancel
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </div>
            )
          ) : null}

          {leadershipNotes.threads.length === 0 ? (
            <EmptyState
              description="No leadership communication threads have been opened for this RFQ yet."
              title="No leadership notes yet"
            />
          ) : (
            <div className="space-y-4">
              {leadershipNotes.threads.map((thread) => (
                <motion.div
                  key={thread.id}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-2xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]"
                  initial={{ opacity: 0, y: 12 }}
                  transition={{ duration: 0.18 }}
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={thread.stateTone}>{thread.stateLabel}</Badge>
                        <Badge variant="outline">{thread.intentLabel}</Badge>
                      </div>
                      <div className="mt-3 text-sm font-medium text-foreground">
                        Opened by {thread.createdBy}
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        Created {thread.createdLabel} · Updated {thread.updatedLabel}
                      </div>
                    </div>
                    <div className="max-w-sm text-sm text-muted-foreground">
                      {thread.waitingOnManager
                        ? leadershipNoteStateMeta[thread.state].helper
                        : thread.latestManagerResponse
                          ? `Latest manager response on ${thread.latestManagerResponseLabel}.`
                          : leadershipNoteStateMeta[thread.state].helper}
                    </div>
                  </div>

                  {thread.latestExecutiveMessage ? (
                    <div className="mt-4 rounded-xl border border-border bg-card p-4 dark:bg-white/[0.02]">
                      <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                        Executive request
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                        {thread.latestExecutiveMessage}
                      </p>
                    </div>
                  ) : null}

                  {thread.latestManagerResponse ? (
                    <div className="mt-4 rounded-xl border border-steel-500/20 bg-steel-500/10 p-4 text-sm text-steel-700 dark:text-steel-300">
                      <div className="font-medium text-foreground">Latest manager response</div>
                      <p className="mt-2 leading-relaxed">{thread.latestManagerResponse}</p>
                    </div>
                  ) : null}

                  {canAcknowledge && thread.state === "open" ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button
                        disabled={busyAction === `ack-${thread.id}`}
                        onClick={() =>
                          void runAction(
                            `ack-${thread.id}`,
                            () => leadershipNotes.acknowledgeThread(thread.id),
                            "Leadership note acknowledged.",
                          )
                        }
                        size="sm"
                        type="button"
                        variant="secondary"
                      >
                        <CheckCheck className="h-4 w-4" />
                        Acknowledge
                      </Button>
                    </div>
                  ) : null}

                  {canReply && thread.state !== "closed" ? (
                    <div className="mt-4 space-y-3 rounded-xl border border-border bg-card p-4 dark:bg-white/[0.02]">
                      <div className="text-sm font-medium text-foreground">
                        Manager reply
                      </div>
                      <Textarea
                        onChange={(event) =>
                          setReplyDrafts((current) => ({
                            ...current,
                            [thread.id]: event.target.value,
                          }))
                        }
                        placeholder="Reply to leadership without changing RFQ operational truth"
                        rows={3}
                        value={replyDrafts[thread.id] ?? ""}
                      />
                      <div className="flex flex-wrap gap-2">
                        <Button
                          disabled={!replyDrafts[thread.id]?.trim() || busyAction === `reply-${thread.id}`}
                          onClick={() => void handleReply(thread.id)}
                          size="sm"
                          type="button"
                        >
                          <Send className="h-4 w-4" />
                          Send reply
                        </Button>
                        {canClose ? (
                          <Button
                            disabled={!thread.hasManagerReply || busyAction === `close-${thread.id}`}
                            onClick={() =>
                              void runAction(
                                `close-${thread.id}`,
                                () => leadershipNotes.closeThread(thread.id),
                                "Leadership note thread closed.",
                              )
                            }
                            size="sm"
                            type="button"
                            variant="secondary"
                          >
                            Close thread
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  ) : null}

                  <div className="mt-4 space-y-3">
                    <div className="flex items-center gap-2 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Thread timeline
                    </div>
                    <div className="space-y-3">{renderThreadEntry(thread)}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
