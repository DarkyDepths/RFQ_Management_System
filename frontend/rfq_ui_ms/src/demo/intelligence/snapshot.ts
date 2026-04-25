import type {
  IntelligencePortfolioResponse,
  SnapshotResponse,
} from "@/models/intelligence/snapshot";

export const intelligencePortfolioResponse: IntelligencePortfolioResponse = {
  completeCount: 2,
  partialCount: 2,
  failedCount: 1,
  readinessAverage: 71,
  narrative:
    "Operational flow and intelligence artifacts are aligned across the live queue, with one workbook path needing immediate correction.",
  featuredRfqId: "RFQ-2026-0142",
};

export const snapshotResponses: Record<string, SnapshotResponse> = {
  "RFQ-2026-0142": {
    rfqId: "RFQ-2026-0142",
    state: "complete",
    intake: {
      status: "complete",
      summary:
        "Package decomposed into 12 bid sections and 184 priced lines with supplier mapping preserved.",
      sectionsDetected: 12,
      lineItems: 184,
      processedAt: "2026-03-28T08:12:00Z",
      missing: [],
    },
    briefing: {
      status: "complete",
      summary:
        "Commercial posture is favorable with clear margin visibility and two contained clarification points.",
      generatedAt: "2026-03-29T10:40:00Z",
      strengths: [
        "Strong compliance on resilient power distribution scope.",
        "Lead-time buffer preserved on switchgear lot.",
      ],
      risks: [
        "Imported cabinet finish code requires client confirmation.",
        "One warranty carve-out still needs legal wording alignment.",
      ],
    },
    workbook: {
      status: "complete",
      uploadedAt: "2026-03-29T16:40:00Z",
      reviewStatus: "complete",
      pendingQuestions: [],
    },
    quality: {
      summary:
        "High-quality package alignment with only low-severity wording adjustments pending.",
      gaps: ["Mirror delivery milestone language with annex B.3 wording."],
    },
    readiness: {
      score: 87,
      confidence: 92,
      blockers: ["Await client response on cabinet finish code B-17."],
    },
    reviewFlags: [
      {
        severity: "low",
        label: "Warranty wording",
        detail: "Final legal wording should align with client template before submission.",
      },
    ],
  },
  "RFQ-2026-0138": {
    rfqId: "RFQ-2026-0138",
    state: "partial",
    intake: {
      status: "complete",
      summary:
        "Package understanding is ready with 8 structured sections and extracted equipment families.",
      sectionsDetected: 8,
      lineItems: 76,
      processedAt: "2026-03-28T09:18:00Z",
      missing: [],
    },
    briefing: {
      status: "partial",
      summary:
        "Initial briefing draft is available, but workbook-linked commercial confidence remains limited.",
      generatedAt: "2026-03-29T12:10:00Z",
      strengths: [
        "Cooling retrofit scope is well-bounded.",
        "Package addenda are already normalized.",
      ],
      risks: ["Workbook upload is still missing for rate alignment."],
    },
    workbook: {
      status: "not_uploaded",
      reviewStatus: "not_uploaded",
      pendingQuestions: [
        "Upload pricing workbook to unlock review.",
        "Confirm optional HVAC line item strategy.",
      ],
    },
    quality: {
      summary:
        "Intelligence is usable for intake and package understanding, but not yet decision-ready.",
      gaps: ["No workbook profile available yet."],
    },
    readiness: {
      score: 52,
      confidence: 71,
      blockers: ["Workbook not uploaded."],
    },
    reviewFlags: [
      {
        severity: "medium",
        label: "Workbook gap",
        detail: "Commercial workbook is required before readiness can move beyond partial.",
      },
    ],
  },
  "RFQ-2026-0126": {
    rfqId: "RFQ-2026-0126",
    state: "failed",
    intake: {
      status: "complete",
      summary:
        "Package understanding is stable and structured, but downstream workbook checks failed.",
      sectionsDetected: 10,
      lineItems: 128,
      processedAt: "2026-03-24T13:40:00Z",
      missing: [],
    },
    briefing: {
      status: "complete",
      summary:
        "Briefing is complete, but its recommendation remains gated by workbook inconsistencies.",
      generatedAt: "2026-03-30T08:10:00Z",
      strengths: ["Routing scope and site access windows remain favorable."],
      risks: [
        "Workbook totals diverge from annex matrix.",
        "Submission dispatch should remain held until review is repaired.",
      ],
    },
    workbook: {
      status: "failed",
      uploadedAt: "2026-03-30T18:05:00Z",
      reviewStatus: "failed",
      pendingQuestions: [
        "Repair section C7 totals.",
        "Confirm spare splice tray quantities against annex C.",
      ],
    },
    quality: {
      summary:
        "Processing failed at workbook review, producing blocking readiness degradation.",
      gaps: ["Workbook review must be rerun on a corrected file."],
    },
    readiness: {
      score: 39,
      confidence: 48,
      blockers: [
        "Workbook review failed with high-severity variance.",
        "Operational submission is paused.",
      ],
    },
    reviewFlags: [
      {
        severity: "high",
        label: "C7 total mismatch",
        detail: "Workbook C7 totals do not reconcile with annex pricing matrix.",
      },
      {
        severity: "medium",
        label: "Spare quantity variance",
        detail: "One spare bundle count differs between workbook and package annex.",
      },
    ],
  },
  "RFQ-2026-0119": {
    rfqId: "RFQ-2026-0119",
    state: "complete",
    intake: {
      status: "complete",
      summary:
        "Award package and commercial workbook remain fully aligned for audit and lessons learned.",
      sectionsDetected: 15,
      lineItems: 206,
      processedAt: "2026-03-10T08:40:00Z",
      missing: [],
    },
    briefing: {
      status: "complete",
      summary:
        "Award summary confirms strong technical alignment and disciplined workbook execution.",
      generatedAt: "2026-03-12T09:15:00Z",
      strengths: [
        "No commercial exceptions at award.",
        "Excellent traceability between package and workbook.",
      ],
      risks: [],
    },
    workbook: {
      status: "complete",
      uploadedAt: "2026-03-11T17:20:00Z",
      reviewStatus: "complete",
      pendingQuestions: [],
    },
    quality: {
      summary: "Archived intelligence is clean and reference-ready.",
      gaps: [],
    },
    readiness: {
      score: 94,
      confidence: 95,
      blockers: [],
    },
    reviewFlags: [],
  },
  "RFQ-2026-0151": {
    rfqId: "RFQ-2026-0151",
    state: "partial",
    intake: {
      status: "complete",
      summary:
        "Diagnostic kit package is parsed, but annex scope clarifications are still open.",
      sectionsDetected: 6,
      lineItems: 54,
      processedAt: "2026-03-27T15:40:00Z",
      missing: ["One optional calibration station clarification note."],
    },
    briefing: {
      status: "partial",
      summary:
        "Briefing is directionally useful, but workbook review is still processing.",
      generatedAt: "2026-03-30T14:00:00Z",
      strengths: ["Field support scope is clearly bounded."],
      risks: ["Calibration accessory coverage remains ambiguous."],
    },
    workbook: {
      status: "partial",
      uploadedAt: "2026-03-30T10:18:00Z",
      reviewStatus: "partial",
      pendingQuestions: ["Complete workbook review after annex clarification."],
    },
    quality: {
      summary:
        "Processing is active, but scope ambiguities keep the intelligence package in a warning state.",
      gaps: ["Calibration station quantity remains unclear."],
    },
    readiness: {
      score: 61,
      confidence: 67,
      blockers: ["Client-side engineering clarification pending."],
    },
    reviewFlags: [
      {
        severity: "medium",
        label: "Optional station ambiguity",
        detail: "Optional calibration station scope is referenced but not yet priced clearly.",
      },
    ],
  },
};
