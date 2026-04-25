import { cn } from "@/lib/utils";

export function SkeletonCard({
  className,
  lines = 3,
}: {
  className?: string;
  lines?: number;
}) {
  return (
    <div className={cn("surface-panel p-5", className)}>
      <div className="shimmer-line h-4 w-28 rounded-full" />
      <div className="mt-4 space-y-3">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={`skeleton-line-${index}`}
            className={cn(
              "shimmer-line h-3 rounded-full",
              index === lines - 1 ? "w-2/3" : "w-full",
            )}
          />
        ))}
      </div>
    </div>
  );
}
