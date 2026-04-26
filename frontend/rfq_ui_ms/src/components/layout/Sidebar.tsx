"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart,
  Files,
  FolderKanban,
  LayoutDashboard,
  PlusSquare,
  Radar,
} from "lucide-react";

import { CopilotTrigger } from "@/components/copilot/CopilotTrigger";
import { ConnectionIndicator } from "@/components/layout/ConnectionIndicator";
import { primaryNavigation, type NavigationIcon } from "@/config/navigation";
import { useAppShell } from "@/context/app-shell-context";
import { useRole } from "@/context/role-context";
import { cn } from "@/lib/utils";

const iconMap: Record<NavigationIcon, typeof LayoutDashboard> = {
  "layout-dashboard": LayoutDashboard,
  "bar-chart": BarChart,
  files: Files,
  "plus-square": PlusSquare,
  radar: Radar,
  "folder-kanban": FolderKanban,
};

export function Sidebar() {
  const pathname = usePathname();
  const { role } = useRole();
  const { sidebarCollapsed } = useAppShell();

  const navItems = primaryNavigation.filter(
    (item) => !item.roles || item.roles.includes(role),
  );

  return (
    <aside
      className={cn(
        "border-b border-border/70 bg-card/80 backdrop-blur-xl",
        "lg:sticky lg:top-0 lg:z-20 lg:flex lg:h-[100dvh] lg:flex-col",
        "lg:border-b-0 lg:border-r lg:bg-transparent lg:backdrop-blur-0",
        sidebarCollapsed ? "lg:w-[80px]" : "lg:w-[260px]",
      )}
    >
      {/* ─── Brand Zone ─── */}
      <div
        className={cn(
          "flex items-center gap-3 border-b border-border/60 px-4 py-4 lg:px-5 lg:py-5",
          sidebarCollapsed && "lg:justify-center lg:px-3",
        )}
      >
        <div className="relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-steel-500/15 to-gold-500/10 ring-1 ring-border">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.png"
            alt="Al Bassam Group"
            className="h-9 w-9 object-contain"
          />
        </div>
        {!sidebarCollapsed ? (
          <div className="min-w-0">
            <div className="text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-gold-600 dark:text-gold-300">
              Al Bassam Group
            </div>
            <div className="mt-0.5 truncate text-sm font-medium leading-tight text-foreground">
              GHI Estimation
            </div>
          </div>
        ) : null}
      </div>

      {/* ─── Navigation ─── */}
      <nav
        className={cn(
          "hide-scrollbar flex gap-1 overflow-x-auto px-3 py-3",
          "lg:flex-1 lg:flex-col lg:overflow-x-visible lg:overflow-y-auto lg:py-4",
          sidebarCollapsed && "lg:items-center",
        )}
      >
        <CopilotTrigger />

        {!sidebarCollapsed ? (
          <div className="hidden px-3 pt-4 pb-2 lg:block">
            <span className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground/70">
              Workspace
            </span>
          </div>
        ) : (
          <div className="hidden lg:my-3 lg:block lg:h-px lg:w-8 lg:bg-border/60" />
        )}

        {navItems.map((item) => {
          const isActive =
            item.match === "exact"
              ? pathname === item.href
              : pathname.startsWith(item.href);
          const Icon = iconMap[item.icon];

          return (
            <Link
              key={`${item.href}-${item.title}`}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium",
                "transition-all duration-200 ease-out-expo",
                "active:translate-y-[1px]",
                sidebarCollapsed && "lg:justify-center lg:px-0 lg:w-11 lg:h-11",
                isActive
                  ? "bg-primary/10 text-foreground dark:bg-primary/15"
                  : "text-muted-foreground hover:bg-muted/60 hover:text-foreground dark:hover:bg-white/[0.04]",
              )}
              href={item.href}
            >
              {isActive ? (
                <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-primary lg:block" />
              ) : null}
              <div
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground group-hover:text-foreground",
                )}
              >
                <Icon className="h-4 w-4" strokeWidth={1.75} />
              </div>
              {!sidebarCollapsed ? (
                <span className="truncate">{item.title}</span>
              ) : null}
            </Link>
          );
        })}
      </nav>

      {/* ─── Connection Status ─── */}
      <div className="hidden border-t border-border/60 p-3 lg:block">
        <ConnectionIndicator compact={sidebarCollapsed} />
      </div>
    </aside>
  );
}
