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
    <div className="surface-panel flex flex-col items-center justify-center px-8 py-12 text-center">
      <div className="rounded-2xl border border-border bg-muted/30 p-4 dark:bg-white/[0.03]">
        <Inbox className="h-7 w-7 text-gold-300" />
      </div>
      <h3 className="mt-5 text-display text-xl font-semibold">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
        {description}
      </p>
      {actionLabel && onAction ? (
        <Button className="mt-5" onClick={onAction} variant="outline">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
