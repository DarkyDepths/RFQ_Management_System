"use client";

import { ArrowUp } from "lucide-react";
import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";

export function CopilotComposer() {
  const { input, setInput, open } = useCopilot();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) {
      textareaRef.current?.focus();
    }
  }, [open, input]);

  const canSend = input.trim().length > 0;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // no-op in Batch 1; Batch 2 wires the local mock send.
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      // no-op in Batch 1.
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-border bg-card px-3 py-3">
      <div className="flex items-end gap-2 rounded-xl border border-border bg-background px-3 py-2 focus-within:ring-2 focus-within:ring-primary/50">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the RFQ Copilot…"
          rows={1}
          className={cn(
            "flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground",
            "outline-none",
          )}
        />
        <Button
          type="submit"
          size="icon"
          variant="default"
          className="h-8 w-8 shrink-0 rounded-lg"
          disabled={!canSend}
          aria-label="Send"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
