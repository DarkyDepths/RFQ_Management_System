import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  [
    "relative inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "rounded-xl text-sm font-medium tracking-tight",
    "transition-all duration-200 ease-out-expo",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-50",
    "active:translate-y-[1px]",
  ].join(" "),
  {
    variants: {
      variant: {
        default: [
          "bg-primary text-primary-foreground",
          "shadow-[0_1px_0_hsl(0_0%_100%/0.18)_inset,0_8px_20px_-8px_hsl(var(--primary)/0.45)]",
          "hover:brightness-110",
        ].join(" "),
        secondary: [
          "border border-border bg-card text-foreground",
          "hover:bg-muted hover:border-foreground/15",
          "dark:bg-white/[0.03] dark:hover:bg-white/[0.06]",
        ].join(" "),
        ghost: [
          "text-muted-foreground",
          "hover:bg-muted/70 hover:text-foreground",
          "dark:hover:bg-white/[0.05]",
        ].join(" "),
        outline: [
          "border border-border bg-transparent text-foreground",
          "hover:bg-muted/60 hover:border-foreground/20",
          "dark:hover:bg-white/[0.04]",
        ].join(" "),
        destructive: [
          "bg-destructive text-destructive-foreground",
          "shadow-[0_1px_0_hsl(0_0%_100%/0.15)_inset,0_8px_20px_-8px_hsl(var(--destructive)/0.45)]",
          "hover:brightness-110",
        ].join(" "),
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-8 rounded-lg px-3 text-xs",
        lg: "h-11 rounded-xl px-6",
        icon: "h-9 w-9 rounded-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
