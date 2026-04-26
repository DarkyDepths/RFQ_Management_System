"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";
import type { ChartSeries, SeriesPoint } from "@/lib/chart-aggregations";

interface SummaryChartProps {
  series: ChartSeries[];
  xLabels: string[];
  height?: number;
  variant?: "area" | "line" | "bars";
  yFormatter?: (value: number) => string;
  className?: string;
  emptyHint?: string;
}

/**
 * Build a smooth SVG path from points using Catmull-Rom → Bezier conversion.
 */
function smoothPath(points: Array<{ x: number; y: number }>) {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  const k = 0.5;
  let d = `M ${points[0].x} ${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(points.length - 1, i + 2)];
    const c1x = p1.x + ((p2.x - p0.x) / 6) * k;
    const c1y = p1.y + ((p2.y - p0.y) / 6) * k;
    const c2x = p2.x - ((p3.x - p1.x) / 6) * k;
    const c2y = p2.y - ((p3.y - p1.y) / 6) * k;
    d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p2.x} ${p2.y}`;
  }
  return d;
}

const PADDING = { top: 24, right: 18, bottom: 36, left: 48 };
const MIN_W = 360;

export function SummaryChart({
  series,
  xLabels,
  height = 260,
  variant = "area",
  yFormatter,
  className,
  emptyHint = "Awaiting source data.",
}: SummaryChartProps) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [hover, setHover] = useState<{ x: number; y: number } | null>(null);
  const [W, setW] = useState(720);
  const containerRef = useRef<HTMLDivElement>(null);

  // Measure container width so SVG renders at native scale (no text distortion).
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => {
      const w = el.getBoundingClientRect().width;
      if (w > 0) setW(Math.max(MIN_W, Math.round(w)));
    };
    update();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const visibleSeries = useMemo(
    () => series.filter((s) => !hidden.has(s.id)),
    [series, hidden],
  );

  const { yMax, gridLines } = useMemo(() => {
    let max = 0;
    for (const s of visibleSeries) {
      for (const p of s.points) if (p.y > max) max = p.y;
    }
    if (max === 0) max = 1;
    const magnitude = Math.pow(10, Math.floor(Math.log10(max)));
    const niceMax =
      max <= magnitude
        ? magnitude
        : max <= 2 * magnitude
          ? 2 * magnitude
          : max <= 5 * magnitude
            ? 5 * magnitude
            : 10 * magnitude;
    const lines = [0, 0.25, 0.5, 0.75, 1].map((t) => niceMax * t);
    return { yMax: niceMax, gridLines: lines };
  }, [visibleSeries]);

  const xCount = xLabels.length;
  const H = height;
  const innerW = Math.max(1, W - PADDING.left - PADDING.right);
  const innerH = Math.max(1, H - PADDING.top - PADDING.bottom);
  const slot = innerW / Math.max(1, xCount);

  // SLOT-CENTER positioning — works for both lines and bars.
  const xPos = (i: number) => PADDING.left + slot * (i + 0.5);
  const yPos = (v: number) =>
    PADDING.top + innerH - (Math.max(0, v) / yMax) * innerH;

  const formatY = yFormatter ?? ((v: number) => `${Math.round(v)}`);
  const isEmpty =
    visibleSeries.length === 0 ||
    visibleSeries.every((s) => s.points.every((p) => p.y === 0));

  const toggleSeries = (id: string) => {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (next.size >= series.length) next.delete(id);
      return next;
    });
  };

  const handlePointer = (event: React.PointerEvent<SVGSVGElement>) => {
    const svg = event.currentTarget;
    const rect = svg.getBoundingClientRect();
    if (rect.width === 0 || xCount === 0) return;
    const localX = event.clientX - rect.left;
    const xInSlots = (localX - PADDING.left) / slot;
    const idx = Math.max(0, Math.min(xCount - 1, Math.floor(xInSlots)));
    setHover({ x: idx, y: event.clientY - rect.top });
  };

  const hoverIdx = hover?.x ?? null;
  const tooltipPoints =
    hoverIdx !== null
      ? visibleSeries.map((s) => ({
          series: s,
          point: s.points[hoverIdx],
        }))
      : [];

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      {/* Legend */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {series.map((s) => {
          const isHidden = hidden.has(s.id);
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => toggleSeries(s.id)}
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all duration-200 ease-out-expo",
                "active:translate-y-[1px]",
                isHidden
                  ? "border-border/50 bg-transparent text-muted-foreground/60"
                  : "border-border bg-card text-foreground hover:border-foreground/15 dark:bg-white/[0.03]",
              )}
              aria-pressed={!isHidden}
            >
              <span
                aria-hidden
                className={cn(
                  "h-2 w-2 rounded-full transition-opacity",
                  isHidden && "opacity-40",
                )}
                style={{ background: s.color }}
              />
              <span className={cn(isHidden && "line-through opacity-60")}>
                {s.label}
              </span>
            </button>
          );
        })}
      </div>

      <div className="relative">
        <svg
          width={W}
          height={H}
          viewBox={`0 0 ${W} ${H}`}
          onPointerMove={handlePointer}
          onPointerLeave={() => setHover(null)}
          className="block touch-none select-none"
          role="img"
          aria-label="Summary chart"
        >
          <defs>
            {visibleSeries.map((s) => (
              <linearGradient
                key={`grad-${s.id}`}
                id={`grad-${s.id}-${W}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor={s.color} stopOpacity="0.32" />
                <stop offset="100%" stopColor={s.color} stopOpacity="0" />
              </linearGradient>
            ))}
            <linearGradient id={`bar-shine-${W}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="white" stopOpacity="0.12" />
              <stop offset="60%" stopColor="white" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Y grid + labels */}
          {gridLines.map((value, i) => {
            const y = yPos(value);
            return (
              <g key={`grid-${i}`}>
                <line
                  x1={PADDING.left}
                  x2={W - PADDING.right}
                  y1={y}
                  y2={y}
                  stroke="hsl(var(--border))"
                  strokeOpacity={i === 0 ? 0.85 : 0.32}
                  strokeDasharray={i === 0 ? "0" : "3 5"}
                />
                <text
                  x={PADDING.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-muted-foreground"
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 10.5,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {formatY(value)}
                </text>
              </g>
            );
          })}

          {/* X labels */}
          {xLabels.map((label, i) => (
            <text
              key={`xl-${i}`}
              x={xPos(i)}
              y={H - 12}
              textAnchor="middle"
              className="fill-muted-foreground"
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 11,
                letterSpacing: "0.04em",
              }}
            >
              {label}
            </text>
          ))}

          {/* Hover crosshair */}
          {hoverIdx !== null ? (
            <line
              x1={xPos(hoverIdx)}
              x2={xPos(hoverIdx)}
              y1={PADDING.top}
              y2={H - PADDING.bottom}
              stroke="hsl(var(--foreground))"
              strokeOpacity={0.16}
              strokeDasharray="3 5"
            />
          ) : null}

          {/* Series rendering */}
          {!isEmpty && variant === "bars"
            ? renderBars({
                visibleSeries,
                xPos,
                yPos,
                slot,
                innerH,
                paddingTop: PADDING.top,
                hoverIdx,
                W,
                formatY,
              })
            : null}

          {!isEmpty && variant !== "bars"
            ? visibleSeries.map((s) => {
                const pts = s.points.map((p) => ({
                  x: xPos(p.x),
                  y: yPos(p.y),
                }));
                const linePath = smoothPath(pts);
                const areaPath =
                  variant === "area"
                    ? `${linePath} L ${pts[pts.length - 1].x} ${PADDING.top + innerH} L ${pts[0].x} ${PADDING.top + innerH} Z`
                    : null;
                return (
                  <g key={`series-${s.id}`}>
                    {areaPath ? (
                      <motion.path
                        d={areaPath}
                        fill={`url(#grad-${s.id}-${W})`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{
                          duration: 0.6,
                          ease: [0.16, 1, 0.3, 1],
                        }}
                      />
                    ) : null}
                    <motion.path
                      d={linePath}
                      fill="none"
                      stroke={s.color}
                      strokeWidth={2.25}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{
                        duration: 0.9,
                        ease: [0.16, 1, 0.3, 1],
                      }}
                    />
                    {pts.map((p, i) => {
                      const isHover = hoverIdx === i;
                      return (
                        <g key={`dot-${s.id}-${i}`}>
                          {isHover ? (
                            <circle
                              cx={p.x}
                              cy={p.y}
                              r={10}
                              fill={s.color}
                              fillOpacity={0.18}
                            />
                          ) : null}
                          <circle
                            cx={p.x}
                            cy={p.y}
                            r={isHover ? 4.5 : 2.6}
                            fill="hsl(var(--background))"
                            stroke={s.color}
                            strokeWidth={2}
                            style={{ transition: "r 160ms ease-out" }}
                          />
                        </g>
                      );
                    })}
                  </g>
                );
              })
            : null}
        </svg>

        {/* Tooltip (HTML overlay — never distorted) */}
        {hoverIdx !== null && tooltipPoints.length > 0 && !isEmpty ? (
          <Tooltip
            xLabel={xLabels[hoverIdx] || ""}
            points={tooltipPoints}
            xPx={xPos(hoverIdx)}
            chartWidth={W}
          />
        ) : null}

        {/* Empty overlay */}
        {isEmpty ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="rounded-full border border-border bg-muted/60 px-3 py-1 text-[0.7rem] font-medium text-muted-foreground dark:bg-white/[0.04]">
              {emptyHint}
            </span>
          </div>
        ) : null}
      </div>
    </div>
  );
}

interface BarsRenderProps {
  visibleSeries: ChartSeries[];
  xPos: (i: number) => number;
  yPos: (v: number) => number;
  slot: number;
  innerH: number;
  paddingTop: number;
  hoverIdx: number | null;
  W: number;
  formatY: (v: number) => string;
}

function renderBars({
  visibleSeries,
  xPos,
  yPos,
  slot,
  innerH,
  paddingTop,
  hoverIdx,
  W,
  formatY,
}: BarsRenderProps) {
  const groupCount = Math.max(1, visibleSeries.length);
  const groupGap = 4;
  const barW = Math.max(
    8,
    Math.min(56, (slot * 0.6 - groupGap * (groupCount - 1)) / groupCount),
  );

  return (
    <g>
      {visibleSeries.map((s, sIdx) => {
        const offsetIndex = sIdx - (groupCount - 1) / 2;
        return (
          <g key={`bars-${s.id}`}>
            {s.points.map((p, i) => {
              const cx = xPos(p.x);
              const x = cx + offsetIndex * (barW + groupGap) - barW / 2;
              const yTop = yPos(p.y);
              const baseline = paddingTop + innerH;
              const h = Math.max(0, baseline - yTop);
              const isHover = hoverIdx === i;
              const meta = (p.meta ?? {}) as { color?: string };
              const fill = meta.color ?? s.color;

              return (
                <g key={`bar-${s.id}-${i}`}>
                  {/* Glow on hover */}
                  {isHover && p.y > 0 ? (
                    <rect
                      x={x - 6}
                      y={yTop - 6}
                      width={barW + 12}
                      height={h + 12}
                      rx={10}
                      fill={fill}
                      fillOpacity={0.10}
                    />
                  ) : null}

                  {/* Bar body */}
                  <motion.rect
                    initial={{ height: 0, y: baseline }}
                    animate={{ height: h, y: yTop }}
                    transition={{
                      type: "spring",
                      stiffness: 130,
                      damping: 24,
                      delay: i * 0.04,
                    }}
                    x={x}
                    width={barW}
                    rx={6}
                    fill={fill}
                    fillOpacity={isHover ? 1 : 0.9}
                    style={{ transition: "fill-opacity 160ms ease-out" }}
                  />

                  {/* Inner highlight (subtle gloss) */}
                  {p.y > 0 ? (
                    <motion.rect
                      initial={{ height: 0, y: baseline }}
                      animate={{ height: h, y: yTop }}
                      transition={{
                        type: "spring",
                        stiffness: 130,
                        damping: 24,
                        delay: i * 0.04,
                      }}
                      x={x}
                      width={barW}
                      rx={6}
                      fill={`url(#bar-shine-${W})`}
                      pointerEvents="none"
                    />
                  ) : null}

                  {/* Empty-slot ghost: tiny pill at baseline */}
                  {p.y === 0 ? (
                    <rect
                      x={x}
                      y={baseline - 2}
                      width={barW}
                      height={2}
                      rx={1}
                      fill={fill}
                      fillOpacity={0.18}
                    />
                  ) : null}

                  {/* Value label above bar */}
                  {p.y > 0 ? (
                    <motion.text
                      initial={{ opacity: 0, y: yTop - 2 }}
                      animate={{ opacity: 1, y: yTop - 8 }}
                      transition={{ delay: i * 0.04 + 0.25, duration: 0.3 }}
                      x={cx + offsetIndex * (barW + groupGap)}
                      textAnchor="middle"
                      className="fill-foreground"
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontVariantNumeric: "tabular-nums",
                        fontSize: 10.5,
                        fontWeight: 600,
                        opacity: isHover ? 1 : 0.78,
                      }}
                    >
                      {formatY(p.y)}
                    </motion.text>
                  ) : null}
                </g>
              );
            })}
          </g>
        );
      })}
    </g>
  );
}

function Tooltip({
  xLabel,
  points,
  xPx,
  chartWidth,
}: {
  xLabel: string;
  points: Array<{ series: ChartSeries; point: SeriesPoint }>;
  xPx: number;
  chartWidth: number;
}) {
  const onLeftSide = xPx > chartWidth * 0.55;
  const offset = 14;
  const style: React.CSSProperties = onLeftSide
    ? { right: chartWidth - xPx + offset }
    : { left: xPx + offset };

  return (
    <motion.div
      key={xLabel}
      initial={{ opacity: 0, y: -2, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.14 }}
      className="pointer-events-none absolute top-10 z-10 min-w-[168px] rounded-xl border border-border bg-popover/95 p-3 shadow-[0_16px_40px_-16px_hsl(0_0%_0%/0.45)] backdrop-blur"
      style={style}
    >
      <div className="text-[0.62rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {xLabel}
      </div>
      <div className="mt-2 space-y-1.5">
        {points.map(({ series: s, point: p }) => (
          <div key={s.id} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span
                aria-hidden
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: s.color }}
              />
              <span>{s.label}</span>
            </div>
            <span className="font-mono tabular-nums text-xs font-semibold text-foreground">
              {p?.yLabel ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
