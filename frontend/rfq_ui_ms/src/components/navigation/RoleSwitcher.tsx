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
  icon: typeof Shield;
}> = [
  { value: "executive", label: "Executive", icon: Briefcase },
  { value: "manager", label: "Est. Manager", icon: Shield },
  { value: "estimator", label: "Estimator", icon: Wrench },
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
    <div className="flex rounded-xl border border-border bg-muted/50 p-0.5 dark:bg-white/[0.03]">
      {roles.map((option) => {
        const isActive = role === option.value;
        const Icon = option.icon;

        return (
          <button
            key={option.value}
            className={cn(
              "relative flex items-center gap-1.5 rounded-[10px] px-3 py-1.5 text-sm font-medium transition-colors",
              !isActive && "text-muted-foreground hover:text-foreground",
            )}
            onClick={() => handleRoleChange(option.value)}
            type="button"
          >
            {isActive ? (
              <motion.div
                className="absolute inset-0 rounded-[10px] bg-card shadow-sm dark:bg-white/[0.08]"
                layoutId="role-switch-pill"
                transition={{ type: "spring", stiffness: 300, damping: 28 }}
              />
            ) : null}
            <div className="relative flex items-center gap-1.5">
              <Icon className="h-3.5 w-3.5" />
              <span>{option.label}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
