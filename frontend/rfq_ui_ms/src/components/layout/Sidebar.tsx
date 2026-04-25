"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import {
  BarChart,
  Files,
  FolderKanban,
  LayoutDashboard,
  PlusSquare,
  Radar,
} from "lucide-react";

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
        "border-b border-border bg-card lg:sticky lg:top-0 lg:z-20 lg:flex lg:h-screen lg:flex-col lg:border-b-0 lg:border-r",
        sidebarCollapsed ? "lg:w-[72px]" : "lg:w-[264px]",
      )}
    >
      {/* ─── Brand Zone ─── */}
      <div
        className={cn(
          "flex items-center gap-3 border-b border-border px-4 py-4 lg:border-b lg:px-5 lg:py-5",
          sidebarCollapsed && "lg:justify-center lg:px-3",
        )}
      >
        <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-amber-50 to-amber-100 ring-1 ring-gold-500/20 dark:from-[#2A2218] dark:to-[#1E1A14] dark:ring-gold-500/30">
          <Image
            alt="Al Bassam Group"
            className="object-contain p-0.5"
            height={32}
            priority
            src="/brand/albassam-logo.png"
            width={32}
          />
        </div>
        {!sidebarCollapsed ? (
          <div className="min-w-0">
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-gold-600 dark:text-gold-300">
              Al Bassam Group
            </div>
            <div className="mt-0.5 text-sm font-medium leading-tight text-foreground">
              GHI Estimation Department
            </div>
          </div>
        ) : null}
      </div>

      {/* ─── Navigation ─── */}
      <nav
        className={cn(
          "hide-scrollbar flex gap-1.5 overflow-x-auto px-3 py-3 lg:flex-1 lg:flex-col lg:overflow-x-visible lg:overflow-y-auto lg:py-4",
          sidebarCollapsed && "lg:items-center",
        )}
      >
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
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
                sidebarCollapsed && "lg:justify-center lg:px-0",
                isActive
                  ? "bg-primary/10 text-primary dark:bg-primary/12"
                  : "text-muted-foreground hover:bg-muted/60 hover:text-foreground dark:hover:bg-white/[0.04]",
              )}
              href={item.href}
            >
              <div
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground group-hover:text-foreground",
                )}
              >
                <Icon className="h-4 w-4" />
              </div>
              {!sidebarCollapsed ? (
                <span className="truncate">{item.title}</span>
              ) : null}
              {isActive ? (
                <div className="absolute left-0 top-1/2 hidden h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-primary lg:block" />
              ) : null}
            </Link>
          );
        })}
      </nav>

      {/* ─── Connection Status ─── */}
      <div className="hidden border-t border-border p-3 lg:block">
        <ConnectionIndicator compact={sidebarCollapsed} />
      </div>
    </aside>
  );
}
