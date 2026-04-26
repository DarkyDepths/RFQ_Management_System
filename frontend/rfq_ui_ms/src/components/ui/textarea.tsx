import * as React from "react";

import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          [
            "flex min-h-[88px] w-full rounded-xl border border-input bg-background/60",
            "px-3.5 py-2.5 text-sm leading-relaxed",
            "shadow-[inset_0_1px_0_hsl(0_0%_100%/0.04)]",
            "placeholder:text-muted-foreground/70",
            "transition-all duration-200 resize-y",
            "focus-visible:outline-none focus-visible:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary/20",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "dark:bg-white/[0.02] dark:focus-visible:bg-white/[0.04]",
          ].join(" "),
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Textarea.displayName = "Textarea";

export { Textarea };
