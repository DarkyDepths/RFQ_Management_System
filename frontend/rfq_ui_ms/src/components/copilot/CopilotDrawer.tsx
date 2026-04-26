"use client";

import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Loader2 } from "lucide-react";

import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";

import { CopilotComposer } from "./CopilotComposer";
import { CopilotEmptyState } from "./CopilotEmptyState";
import { CopilotHeader } from "./CopilotHeader";
import { CopilotHistoryPanel } from "./CopilotHistoryPanel";
import { CopilotMessages } from "./CopilotMessages";

export function CopilotDrawer() {
  const {
    open,
    mode,
    closeCopilot,
    messages,
    status,
    historyViewOpen,
    drawerWidth,
    setDrawerWidth,
    isResizing,
    setResizing,
  } = useCopilot();

  // The drawer only handles the RFQ-bound mode. The general copilot lives on
  // its own dedicated page (/copilot), so we never render the drawer for it.
  const drawerVisible = open && mode.kind === "rfq_bound";

  useEffect(() => {
    if (!drawerVisible) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeCopilot();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerVisible, closeCopilot]);

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

  const renderBody = () => {
    // History view takes over the body area, hiding the chat surface.
    if (historyViewOpen) {
      return <CopilotHistoryPanel />;
    }

    if (status === "loading" && messages.length === 0) {
      return (
        <div
          role="status"
          aria-label="Loading conversation"
          className="flex h-full items-center justify-center"
        >
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      );
    }
    if (status === "error" && messages.length === 0) {
      return (
        <div
          role="alert"
          className="flex h-full flex-col items-center justify-center gap-2 px-6 text-center"
        >
          <AlertCircle className="h-6 w-6 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Couldn&apos;t reach the copilot service. Close and reopen to try again.
          </p>
        </div>
      );
    }
    if (messages.length === 0) {
      return <CopilotEmptyState />;
    }
    return <CopilotMessages />;
  };

  return (
    <AnimatePresence>
      {drawerVisible ? (
        <motion.aside
          key="copilot-drawer"
          role="complementary"
          aria-label="RFQ Copilot"
          initial={{ x: "100%", opacity: 0.6 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0.6 }}
          transition={{ type: "spring", stiffness: 220, damping: 28 }}
          style={{ width: drawerWidth, maxWidth: "100vw" }}
          className="fixed right-0 top-0 z-30 flex h-[100dvh] w-full max-w-full flex-col border-l border-border/70 bg-card/95 shadow-[-32px_0_64px_-32px_hsl(0_0%_0%/0.5)] backdrop-blur-2xl lg:max-w-[80vw]"
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
          <div className="flex flex-1 flex-col overflow-hidden">
            {renderBody()}
          </div>
          {/* Composer is hidden when browsing history */}
          {!historyViewOpen && <CopilotComposer />}
        </motion.aside>
      ) : null}
    </AnimatePresence>
  );
}
