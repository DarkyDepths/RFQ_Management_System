import type {
  WorkbookProfileResponse,
  WorkbookReviewResponse,
} from "@/models/intelligence/workbook";

export const workbookProfileResponses: Record<string, WorkbookProfileResponse> =
  {
    "RFQ-2026-0142": {
      rfqId: "RFQ-2026-0142",
      status: "complete",
      version: "v3.0",
      updatedAt: "2026-03-29T17:10:00Z",
      completion: 96,
      trackedSheets: [
        "Summary",
        "Pricing Matrix",
        "Vendor Tabs",
        "Delivery Plan",
      ],
      missingSections: [],
      owner: "Pricing Cell",
    },
    "RFQ-2026-0138": {
      rfqId: "RFQ-2026-0138",
      status: "not_uploaded",
      version: "n/a",
      completion: 0,
      trackedSheets: [],
      missingSections: ["Workbook not uploaded"],
      owner: "Awaiting estimator upload",
    },
    "RFQ-2026-0126": {
      rfqId: "RFQ-2026-0126",
      status: "failed",
      version: "v2.0",
      updatedAt: "2026-03-30T18:05:00Z",
      completion: 74,
      trackedSheets: ["Summary", "C7", "Materials"],
      missingSections: ["Corrected totals for section C7"],
      owner: "Pricing Cell",
    },
    "RFQ-2026-0119": {
      rfqId: "RFQ-2026-0119",
      status: "complete",
      version: "v4.0",
      updatedAt: "2026-03-11T17:20:00Z",
      completion: 100,
      trackedSheets: ["Summary", "Pricing", "Support Lots", "Award Notes"],
      missingSections: [],
      owner: "Capture Office",
    },
    "RFQ-2026-0151": {
      rfqId: "RFQ-2026-0151",
      status: "partial",
      version: "v1.2",
      updatedAt: "2026-03-30T10:18:00Z",
      completion: 68,
      trackedSheets: ["Summary", "Kit Pricing", "Options"],
      missingSections: ["Calibration station clarification"],
      owner: "Pricing Cell",
    },
  };

export const workbookReviewResponses: Record<string, WorkbookReviewResponse> = {
  "RFQ-2026-0142": {
    rfqId: "RFQ-2026-0142",
    status: "complete",
    version: "v3.0",
    updatedAt: "2026-03-29T17:18:00Z",
    readiness: 89,
    missingResponses: 0,
    flags: [
      {
        severity: "low",
        label: "Warranty clause wording",
        detail: "Minor wording alignment suggested before final issue.",
      },
    ],
  },
  "RFQ-2026-0138": {
    rfqId: "RFQ-2026-0138",
    status: "not_uploaded",
    version: "n/a",
    readiness: 0,
    missingResponses: 12,
    flags: [],
  },
  "RFQ-2026-0126": {
    rfqId: "RFQ-2026-0126",
    status: "failed",
    version: "v2.0",
    updatedAt: "2026-03-30T18:12:00Z",
    readiness: 41,
    missingResponses: 6,
    flags: [
      {
        severity: "high",
        label: "C7 total mismatch",
        detail: "Workbook totals diverge from annex matrix and fail validation.",
      },
      {
        severity: "medium",
        label: "Spare count variance",
        detail: "One spare quantity differs between workbook and annex C.",
      },
    ],
  },
  "RFQ-2026-0119": {
    rfqId: "RFQ-2026-0119",
    status: "complete",
    version: "v4.0",
    updatedAt: "2026-03-11T17:30:00Z",
    readiness: 95,
    missingResponses: 0,
    flags: [],
  },
  "RFQ-2026-0151": {
    rfqId: "RFQ-2026-0151",
    status: "partial",
    version: "v1.2",
    updatedAt: "2026-03-30T10:30:00Z",
    readiness: 64,
    missingResponses: 3,
    flags: [
      {
        severity: "medium",
        label: "Optional station ambiguity",
        detail: "Review cannot close until calibration station scope is clarified.",
      },
    ],
  },
};
