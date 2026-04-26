"use client";

import { motion } from "framer-motion";
import { Briefcase, Shield, Wrench } from "lucide-react";

import { useRouter } from "next/navigation";

import { useRole } from "@/context/role-context";
import type { AppRole } from "@/models/ui/role";
import { cn } from "@/lib/utils";

const roles: Array<{
  value: AppRole;
  label: string;
  shortLabel: string;
  icon: typeof Shield;
}> = [
  { value: "executive", label: "Executive", shortLabel: "Exec", icon: Briefcase },
  { value: "manager", label: "Est. Manager", shortLabel: "Mgr", icon: Shield },
  { value: "estimator", label: "Estimator", shortLabel: "Est", icon: Wrench },
];

export function RoleSwitcher() {
  const { role, setRole } = useRole();
  const router = useRouter();

  const handleRoleChange = (newRole: AppRole) => {
    setRole(newRole);
    if (newRole === "executive") {
      router.replace("/dashboard");
    } else {
      router.replace("/overview");
    }
  };

  return (
    <div className="flex rounded-xl border border-border bg-muted/40 p-1 dark:bg-white/[0.025]">
      {roles.map((option) => {
        const isActive = role === option.value;
        const Icon = option.icon;

        return (
          <button
            key={option.value}
            className={cn(
              "relative flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors",
              "active:translate-y-[1px]",
              !isActive && "text-muted-foreground hover:text-foreground",
              isActive && "text-foreground",
            )}
            onClick={() => handleRoleChange(option.value)}
            type="button"
          >
            {isActive ? (
              <motion.div
                className="absolute inset-0 rounded-lg bg-card shadow-[0_1px_0_hsl(0_0%_100%/0.06)_inset,0_4px_12px_-4px_hsl(220_30%_20%/0.12)] dark:bg-white/[0.08]"
                layoutId="role-switch-pill"
                transition={{ type: "spring", stiffness: 320, damping: 28 }}
              />
            ) : null}
            <div className="relative flex items-center gap-1.5">
              <Icon className="h-3.5 w-3.5" strokeWidth={1.75} />
              <span className="hidden sm:inline">{option.label}</span>
              <span className="sm:hidden">{option.shortLabel}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
