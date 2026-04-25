import type { BriefingResponse } from "@/models/intelligence/briefing";

export const briefingResponses: Record<string, BriefingResponse> = {
  "RFQ-2026-0142": {
    rfqId: "RFQ-2026-0142",
    status: "complete",
    version: "v1.4",
    updatedAt: "2026-03-30T10:40:00Z",
    executiveSummary:
      "High-confidence package with mature workbook alignment, one supplier-finish clarification, and favorable commercial posture.",
    strategicSignals: [
      "Margin resilience improves if switchgear lot is locked this week.",
      "Competitor exposure appears strongest on warranty framing rather than technical scope.",
    ],
    openQuestions: [
      "Await client finish code confirmation for imported cabinet enclosure.",
    ],
    recommendation:
      "Proceed through committee review and hold submission package open for one clarification response only.",
  },
  "RFQ-2026-0138": {
    rfqId: "RFQ-2026-0138",
    status: "partial",
    version: "v0.8",
    updatedAt: "2026-03-29T12:10:00Z",
    executiveSummary:
      "Initial package understanding is clean, but confidence remains bounded until workbook pricing is uploaded.",
    strategicSignals: [
      "Retrofit scope is compact enough for a rapid turnaround response.",
      "Optional HVAC lines may alter pricing position materially.",
    ],
    openQuestions: [
      "Upload the workbook baseline.",
      "Confirm treatment of optional HVAC alternates.",
    ],
    recommendation:
      "Keep the package warm and finish workbook intake before internal approval.",
  },
  "RFQ-2026-0126": {
    rfqId: "RFQ-2026-0126",
    status: "complete",
    version: "v1.1",
    updatedAt: "2026-03-30T08:10:00Z",
    executiveSummary:
      "Technical scope remains viable, but workbook review has created a blocking commercial inconsistency that must be corrected before dispatch.",
    strategicSignals: [
      "Routing scope and site windows remain favorable.",
      "Workbook totals diverge on a high-visibility annex section.",
    ],
    openQuestions: [
      "Repair section C7 totals.",
      "Confirm spare tray quantity for the western segment.",
    ],
    recommendation:
      "Do not dispatch final submission until workbook review is rerun on corrected inputs.",
  },
  "RFQ-2026-0119": {
    rfqId: "RFQ-2026-0119",
    status: "complete",
    version: "v1.7",
    updatedAt: "2026-03-12T09:15:00Z",
    executiveSummary:
      "Awarded pursuit with complete artifact traceability and strong signal quality for reuse.",
    strategicSignals: [
      "Workbook discipline materially strengthened final negotiation posture.",
      "Engineering traceability reduced post-award clarification noise.",
    ],
    openQuestions: [],
    recommendation:
      "Reuse as benchmark artifact set for adjacent strategic programs.",
  },
  "RFQ-2026-0151": {
    rfqId: "RFQ-2026-0151",
    status: "partial",
    version: "v0.9",
    updatedAt: "2026-03-30T14:00:00Z",
    executiveSummary:
      "Package direction is good, but optional calibration station ambiguity keeps the briefing in a guarded state.",
    strategicSignals: [
      "Core kit scope is stable.",
      "Optional accessory treatment may shift competitiveness.",
    ],
    openQuestions: ["Resolve calibration station scope with client engineering."],
    recommendation:
      "Keep the opportunity active but do not finalize workbook positions until clarification lands.",
  },
};
