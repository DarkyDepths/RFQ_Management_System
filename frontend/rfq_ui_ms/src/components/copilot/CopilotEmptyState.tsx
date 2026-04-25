"use client";

import { Sparkles } from "lucide-react";

import { getSuggestedPrompts } from "@/config/copilot-prompts";
import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";

export function CopilotEmptyState() {
  const { mode, setInput } = useCopilot();
  const prompts = getSuggestedPrompts(mode);

  return (
    <div className="flex h-full flex-col items-center justify-center px-6 py-8 text-center">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Sparkles className="h-5 w-5" />
      </div>
      <h2 className="text-base font-semibold text-foreground">How can I help today?</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Try one of these prompts to get started.
      </p>
      <div className="mt-6 grid w-full gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt.id}
            type="button"
            onClick={() => setInput(prompt.prompt)}
            className={cn(
              "rounded-lg border border-border bg-background px-3 py-2 text-left text-sm text-foreground",
              "transition-colors hover:bg-accent/10 hover:text-accent-foreground",
            )}
          >
            {prompt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
