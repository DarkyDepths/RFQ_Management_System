import type { RfqCardModel } from "@/models/manager/rfq";
import { isOverdueRfq, isTerminalRfq } from "@/lib/executive-insights";
import { getRfqBlockedSignal } from "@/utils/blocker-signal";

/**
 * Generic series point used by SummaryChart.
 * x is a numeric position; y is the measured value; xLabel/yLabel are display strings.
 */
export interface SeriesPoint {
  x: number;
  y: number;
  xLabel: string;
  yLabel: string;
  meta?: Record<string, string | number>;
}

export interface ChartSeries {
  id: string;
  label: string;
  color: string;
  points: SeriesPoint[];
}

const DAY_MS = 24 * 60 * 60 * 1000;

const PRIORITY_WEIGHT: Record<RfqCardModel["priority"], number> = {
  critical: 3,
  high: 2,
  normal: 1,
};

/* ─────────────────────────────────────────────────────────────
   EXECUTIVE — Portfolio Risk × Progress
   --------------------------------------------------------------
   Bucket all visible RFQs by lifecycle progress (0-100).
   For each bucket, count "healthy" vs "at risk".
   Risk score per RFQ:
       R(rfq) = 3*blocked + 2*overdue + 1*intel_failed + 1*priority_critical
   An RFQ is at-risk iff R(rfq) >= 1.
   ───────────────────────────────────────────────────────────── */

export interface ExecutivePulseSeries {
  series: ChartSeries[];
  xLabels: string[];
  totals: { healthy: number; atRisk: number; total: number };
}

const PULSE_BUCKETS = [
  { min: 0, max: 25, label: "Discovery" },
  { min: 25, max: 50, label: "Evaluation" },
  { min: 50, max: 75, label: "Estimation" },
  { min: 75, max: 100, label: "Submission" },
  { min: 100, max: 101, label: "Closed" },
];

function computeRiskScore(rfq: RfqCardModel) {
  let score = 0;
  if (getRfqBlockedSignal(rfq).isBlocked) score += 3;
  if (isOverdueRfq(rfq)) score += 2;
  if (rfq.intelligenceState === "failed") score += 1;
  if (rfq.priority === "critical") score += 1;
  return score;
}

export function buildExecutivePulseSeries(
  rfqs: RfqCardModel[],
): ExecutivePulseSeries {
  const healthyByBucket = new Array(PULSE_BUCKETS.length).fill(0);
  const atRiskByBucket = new Array(PULSE_BUCKETS.length).fill(0);
  let healthy = 0;
  let atRisk = 0;

  for (const rfq of rfqs) {
    const progress = Math.max(0, Math.min(100, rfq.rfqProgress ?? 0));
    const idx = PULSE_BUCKETS.findIndex(
      (b) => progress >= b.min && progress < b.max,
    );
    const bucketIdx = idx === -1 ? PULSE_BUCKETS.length - 1 : idx;

    const score = computeRiskScore(rfq);
    if (score >= 1) {
      atRiskByBucket[bucketIdx] += 1;
      atRisk += 1;
    } else {
      healthyByBucket[bucketIdx] += 1;
      healthy += 1;
    }
  }

  const xLabels = PULSE_BUCKETS.map((b) => b.label);

  return {
    series: [
      {
        id: "healthy",
        label: "Healthy",
        color: "hsl(152 56% 48%)",
        points: healthyByBucket.map((count, i) => ({
          x: i,
          y: count,
          xLabel: xLabels[i],
          yLabel: `${count} RFQ${count === 1 ? "" : "s"}`,
        })),
      },
      {
        id: "at-risk",
        label: "At Risk",
        color: "hsl(354 65% 58%)",
        points: atRiskByBucket.map((count, i) => ({
          x: i,
          y: count,
          xLabel: xLabels[i],
          yLabel: `${count} RFQ${count === 1 ? "" : "s"}`,
        })),
      },
    ],
    xLabels,
    totals: { healthy, atRisk, total: healthy + atRisk },
  };
}

/* ─────────────────────────────────────────────────────────────
   MANAGER — Pipeline Value Funnel
   --------------------------------------------------------------
   Group RFQs by lifecycle status and sum bid value (SAR).
   Status order: in_preparation → submitted → awarded vs lost vs cancelled.
   Conversion ratio: awarded_value / (awarded_value + lost_value).
   ───────────────────────────────────────────────────────────── */

const PIPELINE_STAGES = [
  "in_preparation",
  "under_review",
  "submitted",
  "awarded",
  "lost",
  "cancelled",
] as const;
type PipelineStage = (typeof PIPELINE_STAGES)[number];

const STAGE_LABEL: Record<PipelineStage, string> = {
  in_preparation: "In Prep",
  under_review: "Review",
  submitted: "Submitted",
  awarded: "Awarded",
  lost: "Lost",
  cancelled: "Cancelled",
};

const STAGE_COLOR: Record<PipelineStage, string> = {
  in_preparation: "hsl(215 70% 56%)",
  under_review: "hsl(215 60% 50%)",
  submitted: "hsl(36 70% 52%)",
  awarded: "hsl(152 56% 48%)",
  lost: "hsl(354 65% 58%)",
  cancelled: "hsl(220 8% 50%)",
};

export interface ManagerPipelineSeries {
  valueSeries: ChartSeries;
  countSeries: ChartSeries;
  xLabels: string[];
  totals: {
    pipelineValue: number;
    awardedValue: number;
    lostValue: number;
    winRate: number;
  };
  hasValueData: boolean;
}

function formatSar(value: number): string {
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return `${Math.round(value)}`;
}

export function buildManagerPipelineSeries(
  rfqs: RfqCardModel[],
): ManagerPipelineSeries {
  const valueByStage = new Map<PipelineStage, number>();
  const countByStage = new Map<PipelineStage, number>();

  for (const stage of PIPELINE_STAGES) {
    valueByStage.set(stage, 0);
    countByStage.set(stage, 0);
  }

  let hasValueData = false;
  for (const rfq of rfqs) {
    const stage = rfq.status as PipelineStage;
    if (!PIPELINE_STAGES.includes(stage)) continue;
    countByStage.set(stage, (countByStage.get(stage) ?? 0) + 1);
    if (typeof rfq.valueSar === "number" && Number.isFinite(rfq.valueSar)) {
      valueByStage.set(stage, (valueByStage.get(stage) ?? 0) + rfq.valueSar);
      hasValueData = true;
    }
  }

  const xLabels = PIPELINE_STAGES.map((s) => STAGE_LABEL[s]);

  const valuePoints: SeriesPoint[] = PIPELINE_STAGES.map((stage, i) => {
    const value = valueByStage.get(stage) ?? 0;
    return {
      x: i,
      y: value,
      xLabel: STAGE_LABEL[stage],
      yLabel: `SAR ${formatSar(value)}`,
      meta: {
        stage,
        count: countByStage.get(stage) ?? 0,
        color: STAGE_COLOR[stage],
      },
    };
  });

  const countPoints: SeriesPoint[] = PIPELINE_STAGES.map((stage, i) => {
    const count = countByStage.get(stage) ?? 0;
    return {
      x: i,
      y: count,
      xLabel: STAGE_LABEL[stage],
      yLabel: `${count} RFQ${count === 1 ? "" : "s"}`,
      meta: { stage, color: STAGE_COLOR[stage] },
    };
  });

  const awardedValue = valueByStage.get("awarded") ?? 0;
  const lostValue = valueByStage.get("lost") ?? 0;
  const pipelineValue = PIPELINE_STAGES.reduce(
    (sum, stage) => sum + (valueByStage.get(stage) ?? 0),
    0,
  );
  const winRate =
    awardedValue + lostValue > 0
      ? (awardedValue / (awardedValue + lostValue)) * 100
      : 0;

  return {
    valueSeries: {
      id: "pipeline-value",
      label: "Pipeline Value (SAR)",
      color: "hsl(215 70% 56%)",
      points: valuePoints,
    },
    countSeries: {
      id: "pipeline-count",
      label: "RFQ Count",
      color: "hsl(36 70% 52%)",
      points: countPoints,
    },
    xLabels,
    totals: {
      pipelineValue,
      awardedValue,
      lostValue,
      winRate,
    },
    hasValueData,
  };
}

export const PIPELINE_STAGE_META = PIPELINE_STAGES.map((stage) => ({
  id: stage,
  label: STAGE_LABEL[stage],
  color: STAGE_COLOR[stage],
}));

/* ─────────────────────────────────────────────────────────────
   ESTIMATOR — 14-day Workload Density
   --------------------------------------------------------------
   For each of the next 14 days, compute weighted load:
       L(day) = Σ priority_weight(rfq) for rfqs due that day
   priority_weight: critical=3, high=2, normal=1
   Plus a "due today/overdue" bucket pinned to day 0.
   Skip terminal RFQs.
   ───────────────────────────────────────────────────────────── */

export interface EstimatorWorkloadSeries {
  series: ChartSeries[];
  xLabels: string[];
  totals: { critical: number; total: number; overdue: number };
}

export function buildEstimatorWorkloadSeries(
  rfqs: RfqCardModel[],
  windowDays: number = 14,
): EstimatorWorkloadSeries {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayMs = today.getTime();

  const criticalLoad = new Array(windowDays).fill(0);
  const otherLoad = new Array(windowDays).fill(0);
  let overdue = 0;
  let critical = 0;
  let total = 0;

  for (const rfq of rfqs) {
    if (isTerminalRfq(rfq)) continue;
    const due = Date.parse(rfq.dueDateValue);
    if (Number.isNaN(due)) continue;

    const dueDay = new Date(due);
    dueDay.setHours(0, 0, 0, 0);
    const dayDelta = Math.floor((dueDay.getTime() - todayMs) / DAY_MS);

    const weight = PRIORITY_WEIGHT[rfq.priority] ?? 1;
    total += 1;
    if (rfq.priority === "critical") critical += 1;

    if (dayDelta < 0) {
      // Overdue → pile onto day 0 with bumped weight
      overdue += 1;
      criticalLoad[0] += weight + 1;
      continue;
    }
    if (dayDelta >= windowDays) continue;

    if (rfq.priority === "critical") {
      criticalLoad[dayDelta] += weight;
    } else {
      otherLoad[dayDelta] += weight;
    }
  }

  const xLabels: string[] = [];
  for (let i = 0; i < windowDays; i++) {
    const d = new Date(todayMs + i * DAY_MS);
    if (i === 0) xLabels.push("Today");
    else if (i === 1) xLabels.push("Tmrw");
    else if (i % 2 === 0)
      xLabels.push(
        d.toLocaleDateString(undefined, { day: "numeric", month: "short" }),
      );
    else xLabels.push("");
  }

  return {
    series: [
      {
        id: "critical",
        label: "Critical / Overdue",
        color: "hsl(354 65% 58%)",
        points: criticalLoad.map((load, i) => ({
          x: i,
          y: load,
          xLabel: xLabels[i] || `+${i}d`,
          yLabel: `Load ${load.toFixed(0)}`,
        })),
      },
      {
        id: "standard",
        label: "Standard",
        color: "hsl(215 70% 56%)",
        points: otherLoad.map((load, i) => ({
          x: i,
          y: load,
          xLabel: xLabels[i] || `+${i}d`,
          yLabel: `Load ${load.toFixed(0)}`,
        })),
      },
    ],
    xLabels,
    totals: { critical, total, overdue },
  };
}
