"use client";

import { useEffect, useRef } from "react";

import { useCopilot } from "@/hooks/useCopilot";

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1" aria-label="Assistant is composing a reply">
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:0ms]" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:300ms]" />
    </span>
  );
}

export function CopilotMessages() {
  const { messages, status } = useCopilot();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, status]);

  return (
    <ul className="flex flex-col gap-3 px-4 py-4">
      {messages.map((message) => (
        <li
          key={message.id}
          className={
            message.role === "user"
              ? "max-w-[85%] self-end whitespace-pre-wrap rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-primary-foreground [overflow-wrap:anywhere]"
              : "max-w-[85%] self-start whitespace-pre-wrap rounded-2xl rounded-bl-sm bg-muted px-3 py-2 text-sm text-foreground [overflow-wrap:anywhere]"
          }
        >
          {message.content}
        </li>
      ))}
      {status === "loading" ? (
        <li className="max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-muted px-3 py-2 text-sm text-foreground">
          <TypingDots />
        </li>
      ) : null}
      {status === "error" ? (
        <li
          role="alert"
          className="max-w-[85%] self-start rounded-2xl rounded-bl-sm border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          Couldn&apos;t reach the copilot service. Try again.
        </li>
      ) : null}
      <div ref={endRef} />
    </ul>
  );
}
