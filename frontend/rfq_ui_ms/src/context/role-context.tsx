"use client";

import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useState,
} from "react";

import { appConfig } from "@/config/app";
import type { AppRole } from "@/models/ui/role";

interface RoleContextValue {
  role: AppRole;
  setRole: (nextRole: AppRole) => void;
}

const STORAGE_KEY = "rfq-ui-ms-role";

const RoleContext = createContext<RoleContextValue | null>(null);

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<AppRole>(appConfig.defaultRole);

  useEffect(() => {
    const storedRole = window.localStorage.getItem(STORAGE_KEY);
    if (storedRole === "executive" || storedRole === "manager" || storedRole === "estimator") {
      setRoleState(storedRole);
    }
  }, []);

  const setRole = (nextRole: AppRole) => {
    startTransition(() => {
      setRoleState(nextRole);
    });
    window.localStorage.setItem(STORAGE_KEY, nextRole);
  };

  return (
    <RoleContext.Provider
      value={{
        role,
        setRole,
      }}
    >
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error("useRole must be used inside RoleProvider");
  }

  return context;
}
