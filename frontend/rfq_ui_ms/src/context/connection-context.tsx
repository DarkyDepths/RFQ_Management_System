"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { apiConfig } from "@/config/api";

type ServiceStatus = "connected" | "disconnected" | "checking";
type ConnectionMode = "demo" | "live";

interface ConnectionContextValue {
  mode: ConnectionMode;
  managerStatus: ServiceStatus;
  intelligenceStatus: ServiceStatus;
  lastCheckedAt: Date | null;
  refresh: () => void;
}

const ConnectionContext = createContext<ConnectionContextValue | null>(null);

const HEALTH_CHECK_INTERVAL_MS = 30_000;

async function checkHealth(baseUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl}/health`, {
      method: "GET",
      cache: "no-store",
      signal: AbortSignal.timeout(5_000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export function ConnectionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const mode: ConnectionMode = apiConfig.useMockData ? "demo" : "live";

  const [managerStatus, setManagerStatus] = useState<ServiceStatus>(
    mode === "demo" ? "connected" : "checking",
  );
  const [intelligenceStatus, setIntelligenceStatus] = useState<ServiceStatus>(
    mode === "demo" ? "connected" : "checking",
  );
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  const runHealthChecks = async () => {
    if (mode === "demo") return;

    setManagerStatus("checking");
    setIntelligenceStatus("checking");

    const [managerOk, intelligenceOk] = await Promise.all([
      checkHealth(apiConfig.managerBaseUrl),
      checkHealth(apiConfig.intelligenceBaseUrl),
    ]);

    setManagerStatus(managerOk ? "connected" : "disconnected");
    setIntelligenceStatus(intelligenceOk ? "connected" : "disconnected");
    setLastCheckedAt(new Date());
  };

  useEffect(() => {
    if (mode === "demo") return;

    runHealthChecks();

    const interval = setInterval(runHealthChecks, HEALTH_CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  return (
    <ConnectionContext.Provider
      value={{
        mode,
        managerStatus,
        intelligenceStatus,
        lastCheckedAt,
        refresh: runHealthChecks,
      }}
    >
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection() {
  const context = useContext(ConnectionContext);
  if (!context) {
    throw new Error("useConnection must be used inside ConnectionProvider");
  }
  return context;
}
