import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  [
    "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5",
    "text-[0.66rem] font-semibold uppercase tracking-[0.12em]",
    "transition-colors duration-200",
    "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  ].join(" "),
  {
    variants: {
      variant: {
        default:
          "border-primary/15 bg-primary/10 text-primary dark:bg-primary/15",
        secondary:
          "border-border bg-secondary text-secondary-foreground",
        destructive:
          "border-destructive/15 bg-destructive/10 text-destructive dark:bg-destructive/15 dark:text-destructive-foreground",
        outline: "border-border bg-transparent text-foreground",
        steel:
          "border-steel-500/20 bg-steel-500/10 text-steel-700 dark:bg-steel-500/15 dark:text-steel-200",
        gold: "border-gold-500/20 bg-gold-500/10 text-gold-700 dark:bg-gold-500/12 dark:text-gold-200",
        emerald:
          "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/12 dark:text-emerald-200",
        rose: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:bg-rose-500/12 dark:text-rose-200",
        amber:
          "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:bg-amber-500/12 dark:text-amber-200",
        pending:
          "border-border bg-muted/60 text-muted-foreground dark:bg-white/[0.04]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
