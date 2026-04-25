import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-lg border px-2 py-0.5 text-[0.7rem] font-semibold uppercase tracking-wider transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground border-border",
        steel: "border-steel-500/20 bg-steel-500/10 text-steel-700 dark:text-steel-300",
        gold: "border-gold-500/20 bg-gold-500/10 text-gold-700 dark:text-gold-300",
        emerald: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
        rose: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-300",
        amber: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300",
        pending: "border-muted-foreground/20 bg-muted text-muted-foreground dark:bg-white/[0.04]",
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
