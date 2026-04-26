"use client";

import { motion } from "framer-motion";
import { RefreshCw, Wifi, WifiOff, Database } from "lucide-react";

import { useConnection } from "@/context/connection-context";
import { cn } from "@/lib/utils";

function StatusDot({
  status,
}: {
  status: "connected" | "disconnected" | "checking";
}) {
  return (
    <span className="relative inline-flex h-2 w-2">
      {status === "connected" ? (
        <span className="absolute inset-0 animate-pulseRing rounded-full bg-emerald-400/40" />
      ) : null}
      <span
        className={cn(
          "relative inline-block h-2 w-2 rounded-full",
          status === "connected" && "bg-emerald-400",
          status === "disconnected" && "bg-rose-400",
          status === "checking" && "animate-pulse bg-amber-400",
        )}
      />
    </span>
  );
}

export function ConnectionIndicator({ compact = false }: { compact?: boolean }) {
  const { mode, managerStatus, intelligenceStatus, refresh } = useConnection();

  if (mode === "demo") {
    return (
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        initial={{ opacity: 0, y: 4 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className={cn(
          "rounded-2xl border border-amber-500/25 bg-amber-500/[0.06] px-3 py-2.5",
          "dark:border-amber-400/20 dark:bg-amber-400/[0.05]",
          compact && "flex items-center justify-center p-2",
        )}
      >
        {compact ? (
          <Database className="h-4 w-4 text-amber-500 dark:text-amber-300" strokeWidth={1.75} />
        ) : (
          <>
            <div className="flex items-center gap-2">
              <Database className="h-3.5 w-3.5 text-amber-500 dark:text-amber-300" strokeWidth={1.75} />
              <span className="text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-amber-700 dark:text-amber-200">
                Demo Mode
              </span>
            </div>
            <p className="mt-1.5 text-[0.7rem] leading-relaxed text-muted-foreground">
              Mock data active. Set{" "}
              <code className="font-mono text-[0.65rem] text-amber-700/90 dark:text-amber-300/90">
                NEXT_PUBLIC_USE_MOCK_DATA=true
              </code>
              .
            </p>
          </>
        )}
      </motion.div>
    );
  }

  const allConnected =
    managerStatus === "connected" && intelligenceStatus === "connected";

  return (
    <div
      className={cn(
        "rounded-2xl border px-3 py-2.5",
        allConnected
          ? "border-emerald-500/25 bg-emerald-500/[0.06] dark:bg-emerald-400/[0.05]"
          : "border-rose-500/25 bg-rose-500/[0.06] dark:bg-rose-400/[0.05]",
        compact && "flex items-center justify-center p-2",
      )}
    >
      {compact ? (
        allConnected ? (
          <Wifi className="h-4 w-4 text-emerald-500 dark:text-emerald-300" strokeWidth={1.75} />
        ) : (
          <WifiOff className="h-4 w-4 text-rose-500 dark:text-rose-300" strokeWidth={1.75} />
        )
      ) : (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {allConnected ? (
                <Wifi className="h-3.5 w-3.5 text-emerald-500 dark:text-emerald-300" strokeWidth={1.75} />
              ) : (
                <WifiOff className="h-3.5 w-3.5 text-rose-500 dark:text-rose-300" strokeWidth={1.75} />
              )}
              <span
                className={cn(
                  "text-[0.62rem] font-semibold uppercase tracking-[0.22em]",
                  allConnected
                    ? "text-emerald-700 dark:text-emerald-200"
                    : "text-rose-700 dark:text-rose-200",
                )}
              >
                {allConnected ? "Connected" : "Disconnected"}
              </span>
            </div>
            <button
              className="rounded-lg p-1 text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
              onClick={refresh}
              type="button"
              aria-label="Refresh connection"
            >
              <RefreshCw className="h-3 w-3" strokeWidth={1.75} />
            </button>
          </div>

          <div className="mt-2.5 space-y-1.5">
            <div className="flex items-center justify-between text-[0.68rem]">
              <span className="text-muted-foreground">Manager API</span>
              <StatusDot status={managerStatus} />
            </div>
            <div className="flex items-center justify-between text-[0.68rem]">
              <span className="text-muted-foreground">Intelligence API</span>
              <StatusDot status={intelligenceStatus} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
