"use client";

import { useCopilot } from "@/hooks/useCopilot";

export function CopilotMessages() {
  const { messages } = useCopilot();

  return (
    <ul className="flex flex-col gap-3 px-4 py-4">
      {messages.map((message) => (
        <li
          key={message.id}
          className={
            message.role === "user"
              ? "max-w-[85%] self-end rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-primary-foreground"
              : "max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-muted px-3 py-2 text-sm text-foreground"
          }
        >
          {message.content}
        </li>
      ))}
    </ul>
  );
}
