import type {
  ManagerStageStatusResponse,
  ManagerStageTemplateResponse,
} from "@/models/manager/stage";

export const standardWorkflowStages: ManagerStageTemplateResponse[] = [
  {
    id: "intake",
    label: "Intake",
    order: 1,
    plannedDurationDays: 1,
    summary: "Scope registration and RFQ intake alignment.",
    ownerRole: "shared",
  },
  {
    id: "qualification",
    label: "Qualification",
    order: 2,
    plannedDurationDays: 1,
    summary: "Commercial fit and risk qualification.",
    ownerRole: "manager",
  },
  {
    id: "pricing",
    label: "Pricing",
    order: 3,
    plannedDurationDays: 2,
    summary: "Workbook pricing preparation and supplier checks.",
    ownerRole: "estimator",
  },
  {
    id: "review",
    label: "Review",
    order: 4,
    plannedDurationDays: 2,
    summary: "Cross-functional review and intelligence validation.",
    ownerRole: "shared",
  },
  {
    id: "submission",
    label: "Submission",
    order: 5,
    plannedDurationDays: 2,
    summary: "Final package submission and delivery confirmation.",
    ownerRole: "manager",
  },
  {
    id: "award",
    label: "Award",
    order: 6,
    plannedDurationDays: 1,
    summary: "Outcome tracking and closing brief.",
    ownerRole: "manager",
  },
];

export const rapidWorkflowStages: ManagerStageTemplateResponse[] = [
  {
    id: "intake",
    label: "Intake",
    order: 1,
    plannedDurationDays: 1,
    summary: "Rapid response registration.",
    ownerRole: "shared",
  },
  {
    id: "scope-scan",
    label: "Scope Scan",
    order: 2,
    plannedDurationDays: 1,
    summary: "Fast package parsing and feasibility scan.",
    ownerRole: "estimator",
  },
  {
    id: "pricing",
    label: "Pricing",
    order: 3,
    plannedDurationDays: 1,
    summary: "Commercial workbook response drafting.",
    ownerRole: "estimator",
  },
  {
    id: "approval",
    label: "Approval",
    order: 4,
    plannedDurationDays: 1,
    summary: "Internal approval checkpoint.",
    ownerRole: "manager",
  },
  {
    id: "submission",
    label: "Submission",
    order: 5,
    plannedDurationDays: 0,
    summary: "Rapid submission window execution.",
    ownerRole: "manager",
  },
];

export const strategicWorkflowStages: ManagerStageTemplateResponse[] = [
  {
    id: "intake",
    label: "Intake",
    order: 1,
    plannedDurationDays: 1,
    summary: "Strategic intake and sponsor alignment.",
    ownerRole: "shared",
  },
  {
    id: "qualification",
    label: "Qualification",
    order: 2,
    plannedDurationDays: 2,
    summary: "Fit scoring and initial commercial gate.",
    ownerRole: "manager",
  },
  {
    id: "package-analysis",
    label: "Package Analysis",
    order: 3,
    plannedDurationDays: 2,
    summary: "Deep package parsing and artifact preparation.",
    ownerRole: "estimator",
  },
  {
    id: "pricing",
    label: "Pricing",
    order: 4,
    plannedDurationDays: 3,
    summary: "Workbook construction and vendor checks.",
    ownerRole: "estimator",
  },
  {
    id: "technical-review",
    label: "Technical Review",
    order: 5,
    plannedDurationDays: 3,
    summary: "Engineering and intelligence review loop.",
    ownerRole: "shared",
  },
  {
    id: "submission",
    label: "Submission",
    order: 6,
    plannedDurationDays: 2,
    summary: "Submission preparation and risk finalization.",
    ownerRole: "manager",
  },
  {
    id: "award",
    label: "Award",
    order: 7,
    plannedDurationDays: 1,
    summary: "Award capture and closeout intelligence.",
    ownerRole: "manager",
  },
];

export const ghiLongWorkflowStages: ManagerStageTemplateResponse[] = [
  {
    id: "ghi-long-rfq-received",
    label: "RFQ received",
    order: 1,
    plannedDurationDays: 2,
    summary: "Capture intake scope, client context, and baseline pursuit framing.",
    ownerRole: "manager",
    isRequired: true,
  },
  {
    id: "ghi-long-go-no-go",
    label: "Go / No-Go",
    order: 2,
    plannedDurationDays: 2,
    summary: "Record the formal pursuit decision before deeper estimation work starts.",
    ownerRole: "manager",
    isRequired: true,
  },
  {
    id: "ghi-long-pre-bid-clarifications",
    label: "Pre-bid clarifications",
    order: 3,
    plannedDurationDays: 3,
    summary: "Resolve pre-bid scope gaps and client clarifications before design advances.",
    ownerRole: "estimator",
  },
  {
    id: "ghi-long-preliminary-design",
    label: "Preliminary design",
    order: 4,
    plannedDurationDays: 5,
    summary: "Develop the early technical approach and design assumptions.",
    ownerRole: "estimator",
  },
  {
    id: "ghi-long-boq-bom-preparation",
    label: "BOQ / BOM preparation",
    order: 5,
    plannedDurationDays: 5,
    summary: "Prepare the BOQ/BOM structure and capture scope completeness.",
    ownerRole: "estimator",
  },
  {
    id: "ghi-long-vendor-inquiry",
    label: "Vendor inquiry",
    order: 6,
    plannedDurationDays: 5,
    summary: "Collect vendor pricing and lead-time confirmations.",
    ownerRole: "estimator",
  },
  {
    id: "ghi-long-cost-estimation",
    label: "Cost estimation",
    order: 7,
    plannedDurationDays: 5,
    summary: "Build the estimation baseline with structured commercial inputs.",
    ownerRole: "estimator",
  },
  {
    id: "ghi-long-internal-approval",
    label: "Internal approval",
    order: 8,
    plannedDurationDays: 3,
    summary: "Secure internal approval reference before final submission.",
    ownerRole: "manager",
  },
  {
    id: "ghi-long-offer-submission",
    label: "Offer submission",
    order: 9,
    plannedDurationDays: 2,
    summary: "Finalize and submit the commercial offer package.",
    ownerRole: "manager",
  },
  {
    id: "ghi-long-post-bid-clarifications",
    label: "Post-bid clarifications",
    order: 10,
    plannedDurationDays: 5,
    summary: "Handle post-submission clarifications and client follow-up.",
    ownerRole: "manager",
  },
  {
    id: "ghi-long-award-lost",
    label: "Award / Lost",
    order: 11,
    plannedDurationDays: 1,
    summary: "Register the terminal business outcome and preserve closeout truth.",
    ownerRole: "manager",
    isRequired: true,
  },
];

export const ghiShortWorkflowStages: ManagerStageTemplateResponse[] = [
  {
    id: "ghi-short-rfq-received",
    label: "RFQ received",
    order: 1,
    plannedDurationDays: 2,
    summary: "Capture the incoming RFQ and establish its operational owner.",
    ownerRole: "manager",
    isRequired: true,
  },
  {
    id: "ghi-short-go-no-go",
    label: "Go / No-Go",
    order: 2,
    plannedDurationDays: 2,
    summary: "Mandatory pursuit decision before compressed execution continues.",
    ownerRole: "manager",
    isRequired: true,
  },
  {
    id: "ghi-short-cost-estimation",
    label: "Cost estimation",
    order: 3,
    plannedDurationDays: 5,
    summary: "Prepare the estimation baseline for the short workflow path.",
    ownerRole: "estimator",
    isRequired: true,
  },
  {
    id: "ghi-short-internal-approval",
    label: "Internal approval",
    order: 4,
    plannedDurationDays: 3,
    summary: "Obtain the internal sign-off reference for the short path.",
    ownerRole: "manager",
    isRequired: true,
  },
  {
    id: "ghi-short-offer-submission",
    label: "Offer submission",
    order: 5,
    plannedDurationDays: 2,
    summary: "Submit the final short-path commercial offer.",
    ownerRole: "manager",
    isRequired: true,
  },
  {
    id: "ghi-short-award-lost",
    label: "Award / Lost",
    order: 6,
    plannedDurationDays: 1,
    summary: "Register the terminal outcome for the short workflow.",
    ownerRole: "manager",
    isRequired: true,
  },
];

export function buildStageHistory(
  stages: ManagerStageTemplateResponse[],
  activeStageId: string,
  activeTimestamp?: string,
  blockedStageIds: string[] = [],
): ManagerStageStatusResponse[] {
  const activeOrder =
    stages.find((stage) => stage.id === activeStageId)?.order ?? stages.length;

  return stages.map((stage) => {
    if (blockedStageIds.includes(stage.id)) {
      return {
        ...stage,
        state: "blocked",
        timestamp: stage.id === activeStageId ? activeTimestamp : undefined,
      };
    }

    if (stage.id === activeStageId) {
      return {
        ...stage,
        state: "active",
        timestamp: activeTimestamp,
      };
    }

    return {
      ...stage,
      state: stage.order < activeOrder ? "completed" : "upcoming",
    };
  });
}
