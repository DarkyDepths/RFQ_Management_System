import { cn } from "@/lib/utils";

export function SkeletonCard({
  className,
  lines = 3,
}: {
  className?: string;
  lines?: number;
}) {
  return (
    <div className={cn("surface-panel p-6", className)}>
      <div className="flex items-center gap-3">
        <div className="shimmer-line h-8 w-8 rounded-xl" />
        <div className="shimmer-line h-3.5 w-32 rounded-full" />
      </div>
      <div className="mt-6 space-y-2.5">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={`skeleton-line-${index}`}
            className={cn(
              "shimmer-line h-2.5 rounded-full",
              index === 0 && "w-full",
              index === 1 && "w-[88%]",
              index >= 2 && index === lines - 1 ? "w-2/3" : "",
              index > 1 && index !== lines - 1 ? "w-[78%]" : "",
            )}
          />
        ))}
      </div>
    </div>
  );
}
