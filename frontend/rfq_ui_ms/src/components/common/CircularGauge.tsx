"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

interface CircularGaugeProps {
  value: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  className?: string;
  color?: string;
}

export function CircularGauge({
  value,
  size = 120,
  strokeWidth = 8,
  label,
  sublabel,
  className,
  color,
}: CircularGaugeProps) {
  const [animatedValue, setAnimatedValue] = useState(0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animatedValue / 100) * circumference;

  const resolvedColor =
    color ??
    (value >= 80
      ? "hsl(152 56% 42%)"
      : value >= 50
        ? "hsl(215 70% 52%)"
        : value >= 25
          ? "hsl(36 75% 50%)"
          : "hsl(354 60% 52%)");

  useEffect(() => {
    const timer = window.setTimeout(() => setAnimatedValue(value), 80);
    return () => window.clearTimeout(timer);
  }, [value]);

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="-rotate-90 drop-shadow-[0_4px_12px_hsl(var(--primary)/0.08)]"
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          width={size}
        >
          <circle
            className="text-border/60"
            cx={size / 2}
            cy={size / 2}
            fill="none"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            fill="none"
            r={radius}
            stroke={resolvedColor}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            strokeWidth={strokeWidth}
            style={{
              transition:
                "stroke-dashoffset 1.1s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono tabular-nums text-[1.5rem] font-semibold leading-none text-foreground">
            {value}
          </span>
          <span className="mt-0.5 font-mono text-[0.6rem] uppercase tracking-[0.2em] text-muted-foreground">
            %
          </span>
        </div>
      </div>
      {label ? (
        <div className="text-center">
          <div className="text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            {label}
          </div>
          {sublabel ? (
            <div className="mt-0.5 text-xs text-muted-foreground/80">
              {sublabel}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
