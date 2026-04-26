"use client";

import { Sparkles } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import { useCopilot } from "@/hooks/useCopilot";

interface CopilotFloatingButtonProps {
  rfqId: string;
  rfqLabel: string;
}

export function CopilotFloatingButton({
  rfqId,
  rfqLabel,
}: CopilotFloatingButtonProps) {
  const { open, mode, openCopilot } = useCopilot();

  // Hide the FAB whenever the rfq-bound drawer is open — the drawer is the
  // active surface for the conversation, so the trigger has no role until the
  // user closes it.
  const isHidden = open && mode.kind === "rfq_bound";

  return (
    <AnimatePresence>
      {!isHidden ? (
        <motion.button
          key="copilot-fab"
          type="button"
          onClick={() => openCopilot({ kind: "rfq_bound", rfqId, rfqLabel })}
          aria-label="Open RFQ Copilot"
          initial={{ opacity: 0, scale: 0.7, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.7, y: 8 }}
          transition={{ type: "spring", stiffness: 240, damping: 22 }}
          whileHover={{ scale: 1.06 }}
          whileTap={{ scale: 0.94 }}
          className="fixed bottom-8 right-8 z-20 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-[0_12px_28px_-8px_hsl(var(--primary)/0.55),0_1px_0_hsl(0_0%_100%/0.18)_inset] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          <Sparkles className="h-5 w-5" strokeWidth={1.75} />
        </motion.button>
      ) : null}
    </AnimatePresence>
  );
}
