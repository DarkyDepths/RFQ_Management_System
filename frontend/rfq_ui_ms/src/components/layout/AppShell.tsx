"use client";

import type { CSSProperties } from "react";

import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { useCopilot } from "@/hooks/useCopilot";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { open, mode, drawerWidth } = useCopilot();
  const drawerActive = open && mode.kind === "rfq_bound";

  // CSS var ensures the push behavior is desktop-only — on mobile the drawer
  // overlays the content (controlled in the Tailwind class below).
  const padStyle = {
    "--copilot-pad": drawerActive ? `${drawerWidth}px` : "0px",
  } as CSSProperties;

  return (
    <div className="relative min-h-[100dvh] lg:flex">
      <Sidebar />
      <div
        style={padStyle}
        className="relative flex min-w-0 flex-1 flex-col transition-[padding] duration-300 ease-out lg:[padding-right:var(--copilot-pad)]"
      >
        <TopBar />
        <main className="relative flex-1 px-4 pb-16 pt-6 lg:px-10 lg:pt-10">
          <div className="mx-auto w-full max-w-[1400px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
