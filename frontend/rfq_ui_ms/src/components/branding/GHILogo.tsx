import Image from "next/image";

import { cn } from "@/lib/utils";

export function GHILogo({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3",
        className,
      )}
    >
      <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-amber-50 to-amber-100 ring-1 ring-gold-500/20 dark:from-[#2A2218] dark:to-[#1E1A14] dark:ring-gold-500/30">
        <Image
          alt="Al Bassam Group logo"
          className="object-contain p-0.5"
          height={38}
          priority
          sizes="48px"
          src="/brand/albassam-logo.png"
          width={38}
        />
      </div>
      {!compact ? (
        <div className="min-w-0">
          <div className="text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-gold-600 dark:text-gold-300">
            Al Bassam Group
          </div>
          <div className="text-sm font-medium text-foreground">
            GHI Platform
          </div>
        </div>
      ) : null}
    </div>
  );
}
