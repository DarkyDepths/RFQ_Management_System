"use client";

import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { useCopilot } from "@/hooks/useCopilot";

import { CopilotComposer } from "./CopilotComposer";
import { CopilotEmptyState } from "./CopilotEmptyState";
import { CopilotHeader } from "./CopilotHeader";
import { CopilotMessages } from "./CopilotMessages";

export function CopilotDrawer() {
  const { open, closeCopilot, messages } = useCopilot();

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeCopilot();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, closeCopilot]);

  return (
    <AnimatePresence>
      {open ? (
        <motion.aside
          key="copilot-drawer"
          role="dialog"
          aria-label="RFQ Copilot"
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className="fixed right-0 top-0 z-30 flex h-screen w-[420px] flex-col border-l border-border bg-card shadow-glow"
        >
          <CopilotHeader />
          <div className="flex-1 overflow-y-auto">
            {messages.length === 0 ? <CopilotEmptyState /> : <CopilotMessages />}
          </div>
          <CopilotComposer />
        </motion.aside>
      ) : null}
    </AnimatePresence>
  );
}
