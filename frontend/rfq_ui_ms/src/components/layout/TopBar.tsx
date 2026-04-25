"use client";

import { PanelLeft } from "lucide-react";

import { BreadcrumbTrail } from "@/components/navigation/BreadcrumbTrail";
import { RoleSwitcher } from "@/components/navigation/RoleSwitcher";
import { ThemeToggle } from "@/components/navigation/ThemeToggle";
import { Button } from "@/components/ui/button";
import { useAppShell } from "@/context/app-shell-context";

export function TopBar() {
  const { toggleSidebar } = useAppShell();

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="flex items-center justify-between gap-4 px-4 py-3 lg:px-10">
        <div className="flex items-center gap-3">
          <Button
            className="hidden lg:inline-flex"
            onClick={toggleSidebar}
            size="icon"
            variant="ghost"
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
          <BreadcrumbTrail />
        </div>

        <div className="flex items-center gap-2">
          <RoleSwitcher />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
