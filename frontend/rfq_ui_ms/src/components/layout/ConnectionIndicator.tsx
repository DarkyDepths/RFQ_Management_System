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
    <span
      className={cn(
        "inline-block h-2 w-2 rounded-full",
        status === "connected" && "bg-emerald-400",
        status === "disconnected" && "bg-rose-400",
        status === "checking" && "animate-pulse bg-amber-400",
      )}
    />
  );
}

export function ConnectionIndicator({ compact = false }: { compact?: boolean }) {
  const { mode, managerStatus, intelligenceStatus, refresh } = useConnection();

  if (mode === "demo") {
    return (
      <motion.div
        animate={{ opacity: 1 }}
        className={cn(
          "rounded-xl border border-amber-500/25 bg-amber-500/8 px-3 py-2.5",
          compact && "flex items-center justify-center p-2",
        )}
        initial={{ opacity: 0 }}
        transition={{ delay: 0.3 }}
      >
        {compact ? (
          <Database className="h-4 w-4 text-amber-400" />
        ) : (
          <>
            <div className="flex items-center gap-2">
              <Database className="h-3.5 w-3.5 text-amber-400" />
              <span className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-amber-300">
                Demo Mode
              </span>
            </div>
            <p className="mt-1.5 text-[0.7rem] leading-relaxed text-muted-foreground">
              Running on mock data. Set{" "}
              <code className="font-mono text-[0.65rem] text-amber-300/80">
                NEXT_PUBLIC_USE_MOCK_DATA=true
              </code>{" "}
              to keep demo mode active.
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
        "rounded-xl border px-3 py-2.5",
        allConnected
          ? "border-emerald-500/25 bg-emerald-500/8"
          : "border-rose-500/25 bg-rose-500/8",
        compact && "flex items-center justify-center p-2",
      )}
    >
      {compact ? (
        allConnected ? (
          <Wifi className="h-4 w-4 text-emerald-400" />
        ) : (
          <WifiOff className="h-4 w-4 text-rose-400" />
        )
      ) : (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {allConnected ? (
                <Wifi className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <WifiOff className="h-3.5 w-3.5 text-rose-400" />
              )}
              <span
                className={cn(
                  "text-[0.68rem] font-semibold uppercase tracking-[0.2em]",
                  allConnected ? "text-emerald-300" : "text-rose-300",
                )}
              >
                {allConnected ? "Connected" : "Disconnected"}
              </span>
            </div>
            <button
              className="rounded-lg p-1 text-muted-foreground transition-colors hover:text-foreground"
              onClick={refresh}
              type="button"
            >
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>

          <div className="mt-2 space-y-1.5">
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
