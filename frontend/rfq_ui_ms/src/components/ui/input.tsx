import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          [
            "flex h-10 w-full rounded-xl border border-input bg-background/60",
            "px-3.5 py-2 text-sm leading-tight",
            "shadow-[inset_0_1px_0_hsl(0_0%_100%/0.04)]",
            "placeholder:text-muted-foreground/70",
            "transition-all duration-200",
            "file:border-0 file:bg-transparent file:text-sm file:font-medium",
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
Input.displayName = "Input";

export { Input };
