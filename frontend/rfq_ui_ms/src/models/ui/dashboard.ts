export interface BreadcrumbItem {
  label: string;
  href?: string;
  isCurrent?: boolean;
}

export interface KPIMetricModel {
  id: string;
  label: string;
  value: string;
  helper: string;
  trendLabel: string;
  trendDirection: "up" | "down" | "steady";
  tone: "steel" | "gold" | "emerald" | "amber";
}

export interface DashboardAnalyticsMetricModel {
  id: string;
  label: string;
  value: number | null;
  displayValue: string;
  helper: string;
  tone: "steel" | "gold" | "emerald" | "amber";
  isAvailable: boolean;
}

export interface DashboardClientAnalyticsModel {
  client: string;
  rfqCount: number;
  avgMarginValue: number | null;
  avgMarginLabel: string;
  isMarginAvailable: boolean;
}

export interface ManagerDashboardAnalyticsModel {
  metrics: DashboardAnalyticsMetricModel[];
  byClient: DashboardClientAnalyticsModel[];
}

export interface IntelligencePortfolioModel {
  completeCount: number;
  partialCount: number;
  failedCount: number;
  readinessAverage: number;
  narrative: string;
  featuredRfqId: string;
}
