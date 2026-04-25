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
      ? "hsl(152, 56%, 40%)"
      : value >= 50
        ? "hsl(213, 60%, 52%)"
        : value >= 25
          ? "hsl(36, 70%, 50%)"
          : "hsl(0, 55%, 55%)");

  useEffect(() => {
    const timer = window.setTimeout(() => setAnimatedValue(value), 120);
    return () => window.clearTimeout(timer);
  }, [value]);

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="-rotate-90"
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          width={size}
        >
          <circle
            className="text-border"
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
              transition: "stroke-dashoffset 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)",
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono text-2xl font-semibold text-foreground">
            {value}
          </span>
          <span className="font-mono text-[0.65rem] text-muted-foreground">%</span>
        </div>
      </div>
      {label ? (
        <div className="text-center">
          <div className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            {label}
          </div>
          {sublabel ? (
            <div className="mt-0.5 text-xs text-muted-foreground">
              {sublabel}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
