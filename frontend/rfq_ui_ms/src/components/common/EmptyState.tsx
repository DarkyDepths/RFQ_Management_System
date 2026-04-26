import { Inbox } from "lucide-react";

import { Button } from "@/components/ui/button";

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="surface-panel flex flex-col items-center justify-center px-8 py-14 text-center">
      <div className="relative">
        <div className="absolute inset-0 -z-10 rounded-3xl bg-gradient-to-br from-primary/20 to-transparent blur-2xl" />
        <div className="rounded-2xl border border-border bg-muted/40 p-4 shadow-[inset_0_1px_0_hsl(0_0%_100%/0.06)] dark:bg-white/[0.03]">
          <Inbox className="h-6 w-6 text-muted-foreground" strokeWidth={1.5} />
        </div>
      </div>
      <h3 className="mt-6 text-display text-xl font-semibold tracking-tight text-foreground">
        {title}
      </h3>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
        {description}
      </p>
      {actionLabel && onAction ? (
        <Button className="mt-6" onClick={onAction} variant="secondary">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
