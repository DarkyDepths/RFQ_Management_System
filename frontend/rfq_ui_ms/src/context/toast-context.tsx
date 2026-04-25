"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

type ToastTone = "success" | "error" | "info";

interface ToastInput {
  description?: string;
  title: string;
  tone?: ToastTone;
}

interface ToastRecord extends ToastInput {
  id: number;
  tone: ToastTone;
}

interface ToastContextValue {
  pushToast: (toast: ToastInput) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

function toastToneMeta(tone: ToastTone) {
  if (tone === "success") {
    return {
      icon: CheckCircle2,
      iconClassName: "text-emerald-600 dark:text-emerald-300",
      panelClassName: "border-emerald-500/25 bg-emerald-500/10",
    };
  }

  if (tone === "error") {
    return {
      icon: AlertCircle,
      iconClassName: "text-rose-600 dark:text-rose-300",
      panelClassName: "border-rose-500/25 bg-rose-500/10",
    };
  }

  return {
    icon: Info,
    iconClassName: "text-steel-600 dark:text-steel-300",
    panelClassName: "border-steel-500/25 bg-steel-500/10",
  };
}

export function ToastProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const nextIdRef = useRef(1);

  const dismissToast = useCallback((toastId: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== toastId));
  }, []);

  const pushToast = useCallback(
    ({ description, title, tone = "info" }: ToastInput) => {
      const toastId = nextIdRef.current++;

      setToasts((current) => [
        ...current,
        {
          description,
          id: toastId,
          title,
          tone,
        },
      ]);

      window.setTimeout(() => {
        dismissToast(toastId);
      }, 4200);
    },
    [dismissToast],
  );

  const value = useMemo<ToastContextValue>(
    () => ({
      pushToast,
    }),
    [pushToast],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}

      <div className="pointer-events-none fixed right-4 top-4 z-[120] flex w-full max-w-sm flex-col gap-3">
        <AnimatePresence>
          {toasts.map((toast) => {
            const meta = toastToneMeta(toast.tone);
            const Icon = meta.icon;

            return (
              <motion.div
                key={toast.id}
                animate={{ opacity: 1, x: 0, y: 0 }}
                className={`pointer-events-auto rounded-2xl border p-4 shadow-lg backdrop-blur ${meta.panelClassName}`}
                exit={{ opacity: 0, x: 24, y: -8 }}
                initial={{ opacity: 0, x: 24, y: -8 }}
                transition={{ duration: 0.2 }}
              >
                <div className="flex items-start gap-3">
                  <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${meta.iconClassName}`} />
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-foreground">{toast.title}</div>
                    {toast.description ? (
                      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                        {toast.description}
                      </p>
                    ) : null}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside ToastProvider");
  }

  return context;
}
