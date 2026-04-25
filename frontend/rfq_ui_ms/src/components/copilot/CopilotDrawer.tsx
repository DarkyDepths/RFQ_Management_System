"use client";

import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";

import { CopilotComposer } from "./CopilotComposer";
import { CopilotEmptyState } from "./CopilotEmptyState";
import { CopilotHeader } from "./CopilotHeader";
import { CopilotMessages } from "./CopilotMessages";

export function CopilotDrawer() {
  const {
    open,
    closeCopilot,
    messages,
    drawerWidth,
    setDrawerWidth,
    isResizing,
    setResizing,
  } = useCopilot();

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeCopilot();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, closeCopilot]);

  // Lock cursor + disable text selection while resizing.
  useEffect(() => {
    if (!isResizing) return;
    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    return () => {
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
    };
  }, [isResizing]);

  const handleResizeStart = (event: React.MouseEvent) => {
    event.preventDefault();
    setResizing(true);
    const startX = event.clientX;
    const startWidth = drawerWidth;

    const onMove = (moveEvent: MouseEvent) => {
      // Drawer is right-anchored: dragging left widens, dragging right narrows.
      const delta = startX - moveEvent.clientX;
      setDrawerWidth(startWidth + delta);
    };

    const onUp = () => {
      setResizing(false);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  };

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
          style={{ width: drawerWidth }}
          className="fixed right-0 top-0 z-30 flex h-screen flex-col border-l border-border bg-card shadow-glow"
        >
          <button
            type="button"
            aria-label="Resize copilot panel"
            onMouseDown={handleResizeStart}
            className={cn(
              "absolute left-0 top-0 z-10 h-full w-1 cursor-col-resize bg-transparent transition-colors",
              "hover:bg-primary/40",
              isResizing && "bg-primary/40",
            )}
          />
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
