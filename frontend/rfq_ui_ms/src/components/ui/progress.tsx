import { cn } from "@/lib/utils";

export function Progress({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div
      className={cn(
        "relative h-1.5 w-full overflow-hidden rounded-full bg-muted/70 dark:bg-white/[0.05]",
        className,
      )}
    >
      <div
        className="h-full rounded-full bg-primary transition-[width] duration-700 ease-out-expo"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
