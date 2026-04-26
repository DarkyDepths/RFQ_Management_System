"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles } from "lucide-react";

import { useAppShell } from "@/context/app-shell-context";
import { cn } from "@/lib/utils";

export function CopilotTrigger() {
  const { sidebarCollapsed } = useAppShell();
  const pathname = usePathname();
  const isActive = pathname?.startsWith("/copilot") ?? false;

  return (
    <Link
      href="/copilot"
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium",
        "transition-all duration-200 ease-out-expo active:translate-y-[1px]",
        "border bg-gradient-to-br shadow-[0_1px_0_hsl(0_0%_100%/0.06)_inset]",
        isActive
          ? "border-primary/35 from-primary/[0.14] via-primary/[0.07] to-transparent text-foreground"
          : "border-primary/20 from-primary/[0.08] via-primary/[0.04] to-transparent text-foreground hover:border-primary/30 hover:from-primary/[0.12]",
        "dark:from-primary/[0.10] dark:via-primary/[0.05]",
        sidebarCollapsed && "lg:justify-center lg:px-0 lg:w-11 lg:h-11",
      )}
    >
      <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
        <Sparkles className="h-4 w-4" strokeWidth={1.75} />
        <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-primary animate-breathe" />
      </div>
      {!sidebarCollapsed ? (
        <div className="flex flex-1 items-center justify-between">
          <span className="truncate font-medium">RFQ Copilot</span>
          {isActive ? (
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
          ) : null}
        </div>
      ) : null}
    </Link>
  );
}
