"use client";

import { Moon, Sun } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { useTheme } from "@/context/theme-context";

export function ThemeToggle() {
  const { resolved, toggle } = useTheme();

  return (
    <button
      aria-label={`Switch to ${resolved === "dark" ? "light" : "dark"} mode`}
      className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-card/60 text-muted-foreground transition-all duration-200 hover:bg-muted/60 hover:text-foreground active:translate-y-[1px] dark:bg-white/[0.03] dark:hover:bg-white/[0.06]"
      onClick={toggle}
      type="button"
    >
      <AnimatePresence mode="wait" initial={false}>
        {resolved === "dark" ? (
          <motion.div
            key="sun"
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: 90, scale: 0.6 }}
            initial={{ opacity: 0, rotate: -90, scale: 0.6 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
          >
            <Sun className="h-4 w-4" strokeWidth={1.75} />
          </motion.div>
        ) : (
          <motion.div
            key="moon"
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: 90, scale: 0.6 }}
            initial={{ opacity: 0, rotate: -90, scale: 0.6 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
          >
            <Moon className="h-4 w-4" strokeWidth={1.75} />
          </motion.div>
        )}
      </AnimatePresence>
    </button>
  );
}
