import type {
  CancelRfqInput,
  CreateRfqInput,
  ManagerRfqDetailResponse,
  ManagerRfqListItemResponse,
  ManagerRfqListResponse,
} from "@/models/manager/rfq";
import { managerWorkflowResponses } from "@/demo/manager/workflows";

import {
  buildStageHistory,
  rapidWorkflowStages,
  standardWorkflowStages,
  strategicWorkflowStages,
} from "@/demo/manager/stages";

const rfqRecords: ManagerRfqListItemResponse[] = [
  {
    id: "RFQ-2026-0142",
    title: "Integrated Border Surveillance Power Upgrade",
    client: "Albassam Security Systems",
    owner: "GHI Estimator",
    region: "Riyadh",
    valueSar: 18400000,
    dueDate: "2026-04-18",
    createdAt: "2026-03-03",
    updatedAt: "2026-03-30",
    workflowId: "workflow-strategic",
    workflowName: "Strategic Programs Review",
    status: "under_review",
    intelligenceState: "complete",
    priority: "critical",
    nextAction: "Finalize clarification matrix before committee round.",
    summaryLine:
      "Package, briefing, and workbook reviews are synchronized with only one low-severity clarification pending.",
    tags: ["Defense", "Critical Infrastructure", "High Margin"],
    stageHistory: buildStageHistory(
      strategicWorkflowStages,
      "technical-review",
      "2026-03-30T09:20:00Z",
    ),
  },
  {
    id: "RFQ-2026-0138",
    title: "Tactical Communications Shelter Retrofit",
    client: "GHI Field Systems",
    owner: "GHI Estimator",
    region: "Eastern Province",
    valueSar: 6200000,
    dueDate: "2026-04-09",
    createdAt: "2026-03-10",
    updatedAt: "2026-03-29",
    workflowId: "workflow-rapid",
    workflowName: "Rapid Turnaround Response",
    status: "in_preparation",
    intelligenceState: "partial",
    priority: "high",
    nextAction: "Upload pricing workbook to unlock commercial review.",
    summaryLine:
      "Package intake completed quickly, but the workbook path has not started yet.",
    tags: ["Fast Turn", "Workbook Missing"],
    stageHistory: buildStageHistory(
      rapidWorkflowStages,
      "pricing",
      "2026-03-29T14:10:00Z",
    ),
  },
  {
    id: "RFQ-2026-0126",
    title: "Critical Facility Fiber Backbone Expansion",
    client: "National Grid Control",
    owner: "GHI Estimator",
    region: "Dammam",
    valueSar: 9700000,
    dueDate: "2026-04-04",
    createdAt: "2026-02-26",
    updatedAt: "2026-03-31",
    workflowId: "workflow-standard",
    workflowName: "Standard Bid Lifecycle",
    status: "submitted",
    intelligenceState: "failed",
    priority: "high",
    nextAction:
      "Resolve workbook validation failures on section C7 before final revision.",
    summaryLine:
      "Operational submission is staged, but workbook review flagged blocking inconsistencies.",
    tags: ["Validation Alert", "Escalated"],
    stageHistory: buildStageHistory(
      standardWorkflowStages,
      "submission",
      "2026-03-31T07:40:00Z",
      ["submission"],
    ),
  },
  {
    id: "RFQ-2026-0119",
    title: "Air Defense Maintenance Support Lots",
    client: "Regional Air Command",
    owner: "GHI Estimator",
    region: "Jeddah",
    valueSar: 22500000,
    dueDate: "2026-03-17",
    createdAt: "2026-02-12",
    updatedAt: "2026-03-28",
    workflowId: "workflow-strategic",
    workflowName: "Strategic Programs Review",
    status: "awarded",
    outcomeReason:
      "Awarded after a strong technical score and a clean delivery-risk posture against the customer timeline.",
    intelligenceState: "complete",
    priority: "critical",
    nextAction:
      "Archive artifacts and convert signals into the next pursuit brief.",
    summaryLine:
      "Reference win with clean artifact trail and high-confidence workbook readiness.",
    tags: ["Awarded", "Reference Win"],
    stageHistory: buildStageHistory(
      strategicWorkflowStages,
      "award",
      "2026-03-28T10:55:00Z",
    ),
  },
  {
    id: "RFQ-2026-0151",
    title: "Protected Mobility Diagnostics Toolkit",
    client: "Desert Mobility Command",
    owner: "GHI Estimator",
    region: "Tabuk",
    valueSar: 4300000,
    dueDate: "2026-04-14",
    createdAt: "2026-03-19",
    updatedAt: "2026-03-30",
    workflowId: "workflow-standard",
    workflowName: "Standard Bid Lifecycle",
    status: "attention_required",
    intelligenceState: "partial",
    priority: "normal",
    nextAction:
      "Clarify calibration kit scope with client-side engineering.",
    summaryLine:
      "Readiness is advancing, but scope gaps remain open in the diagnostic annex.",
    tags: ["Scope Gap", "Pending Notes"],
    stageHistory: buildStageHistory(
      standardWorkflowStages,
      "review",
      "2026-03-30T12:05:00Z",
    ),
  },
  {
    id: "RFQ-2026-0107",
    title: "National Command Center AV Modernization",
    client: "Strategic Defense Authority",
    owner: "GHI Estimator",
    region: "Riyadh",
    valueSar: 11300000,
    dueDate: "2026-03-12",
    createdAt: "2026-02-05",
    updatedAt: "2026-03-20",
    workflowId: "workflow-strategic",
    workflowName: "Strategic Programs Review",
    status: "lost",
    outcomeReason:
      "Lost on commercial competitiveness after the client selected a lower lead-time package with fewer compliance deviations.",
    intelligenceState: "complete",
    priority: "critical",
    nextAction:
      "Capture the commercial delta and feed the loss rationale into the next pursuit brief.",
    summaryLine:
      "Lost after commercial comparison; delivery lead-time and alternate compliance position were decisive.",
    tags: ["Lost", "Leadership Review"],
    stageHistory: buildStageHistory(
      strategicWorkflowStages,
      "award",
      "2026-03-20T09:40:00Z",
    ),
  },
  {
    id: "RFQ-2026-0102",
    title: "Coastal Security Tower Retrofit",
    client: "Maritime Protection Authority",
    owner: "GHI Estimator",
    region: "Jubail",
    valueSar: 7600000,
    dueDate: "2026-03-06",
    createdAt: "2026-01-29",
    updatedAt: "2026-03-14",
    workflowId: "workflow-standard",
    workflowName: "Standard Bid Lifecycle",
    status: "lost",
    outcomeReason:
      "Lost after the client weighted local supplier coverage and maintenance response commitments above price parity.",
    intelligenceState: "complete",
    priority: "high",
    nextAction:
      "Capture the service-coverage gap and feed it into the next coastal infrastructure pursuit.",
    summaryLine:
      "Loss review shows service coverage and maintenance response commitments were the deciding factors.",
    tags: ["Lost", "Coverage Gap"],
    stageHistory: buildStageHistory(
      standardWorkflowStages,
      "award",
      "2026-03-14T11:20:00Z",
    ),
  },
];

export const managerRfqListResponse: ManagerRfqListResponse = {
  items: rfqRecords,
  metrics: [
    {
      id: "total-rfqs",
      label: "Total RFQs",
      value: 58,
      unit: "count",
      helper: "Tracked across live and awarded pursuits.",
      trendLabel: "+6 this month",
      trendDirection: "up",
      tone: "steel",
    },
    {
      id: "active-rfqs",
      label: "Active RFQs",
      value: 17,
      unit: "count",
      helper: "In preparation, review, or submission stages.",
      trendLabel: "3 require intervention",
      trendDirection: "steady",
      tone: "gold",
    },
    {
      id: "win-rate",
      label: "Win Rate",
      value: 31,
      unit: "percent",
      helper: "Trailing 90-day weighted conversion rate.",
      trendLabel: "+4 pts vs prior quarter",
      trendDirection: "up",
      tone: "emerald",
    },
    {
      id: "avg-processing",
      label: "Avg Processing Time",
      value: 6.4,
      unit: "days",
      helper: "Package to intelligence snapshot cycle time.",
      trendLabel: "-1.2 days after workbook automation",
      trendDirection: "down",
      tone: "amber",
    },
  ],
};

export const managerRfqDetailResponses: Record<string, ManagerRfqDetailResponse> =
  {
    "RFQ-2026-0142": {
      ...rfqRecords[0],
      description:
        "Strategic RFQ covering resilient power distribution, UPS redundancy, and integration support for border surveillance nodes.",
      industry: "Power",
      country: "Saudi Arabia",
      procurementLead: "H. Alessa",
      estimatedSubmissionDate: "2026-04-14",
      stageNotes: [
        {
          id: "note-142-1",
          stageId: "technical-review",
          author: "Engineering Review Cell",
          note: "Voltage drop calculations aligned with the annex after generator sizing revision.",
          createdAt: "2026-03-30T11:40:00Z",
          tone: "success",
        },
        {
          id: "note-142-2",
          stageId: "technical-review",
          author: "Commercial Manager",
          note: "One imported cabinet SKU still needs confirmation against finish code B-17.",
          createdAt: "2026-03-31T08:15:00Z",
          tone: "warning",
        },
      ],
      recentFiles: [
        {
          id: "file-142-zip",
          label: "rfq_0142_package.zip",
          type: "ZIP Intake",
          uploadedAt: "2026-03-28T08:04:00Z",
          uploadedBy: "Estimation Manager",
          status: "processed",
        },
        {
          id: "file-142-workbook",
          label: "rfq_0142_pricing_v3.xlsx",
          type: "Workbook",
          uploadedAt: "2026-03-29T16:40:00Z",
          uploadedBy: "M. Rahman",
          status: "processed",
        },
      ],
      subtasks: [
        {
          id: "task-142-1",
          label: "Close finish code clarification",
          owner: "M. Rahman",
          dueDate: "2026-04-01",
          state: "in_progress",
        },
        {
          id: "task-142-2",
          label: "Finalize committee presentation summary",
          owner: "H. Alessa",
          dueDate: "2026-04-02",
          state: "open",
        },
        {
          id: "task-142-3",
          label: "Lock supplier lead-time assumption",
          owner: "Sourcing Cell",
          dueDate: "2026-03-31",
          state: "done",
        },
      ],
      uploads: [
        {
          kind: "zip",
          title: "Upload RFQ Package ZIP",
          description: "Refresh package understanding, snapshot inputs, and extracted sections.",
          status: "ready",
          fileName: "rfq_0142_package.zip",
          uploadedAt: "2026-03-28T08:04:00Z",
        },
        {
          kind: "workbook",
          title: "Upload Pricing Workbook",
          description: "Refresh workbook profile, workbook review, and readiness scoring.",
          status: "ready",
          fileName: "rfq_0142_pricing_v3.xlsx",
          uploadedAt: "2026-03-29T16:40:00Z",
        },
      ],
    },
    "RFQ-2026-0138": {
      ...rfqRecords[1],
      description:
        "Retrofit scope for tactical communications shelters including cooling upgrades, cable routing, and field power adjustments.",
      industry: "Infrastructure",
      country: "Saudi Arabia",
      procurementLead: "N. Tarek",
      estimatedSubmissionDate: "2026-04-07",
      stageNotes: [
        {
          id: "note-138-1",
          stageId: "pricing",
          author: "Program Worker",
          note: "Package parse identified 14 optional line items that still need workbook mapping.",
          createdAt: "2026-03-29T14:30:00Z",
          tone: "info",
        },
      ],
      recentFiles: [
        {
          id: "file-138-zip",
          label: "rfq_0138_scope_package.zip",
          type: "ZIP Intake",
          uploadedAt: "2026-03-28T09:10:00Z",
          uploadedBy: "GHI Estimator",
          status: "processed",
        },
      ],
      subtasks: [
        {
          id: "task-138-1",
          label: "Upload workbook baseline",
          owner: "A. Nasser",
          dueDate: "2026-03-31",
          state: "open",
        },
        {
          id: "task-138-2",
          label: "Confirm HVAC alternate lot",
          owner: "Engineering Support",
          dueDate: "2026-04-01",
          state: "in_progress",
        },
      ],
      uploads: [
        {
          kind: "zip",
          title: "Upload RFQ Package ZIP",
          description: "Replace the parsed package with a revised drop or addendum set.",
          status: "ready",
          fileName: "rfq_0138_scope_package.zip",
          uploadedAt: "2026-03-28T09:10:00Z",
        },
        {
          kind: "workbook",
          title: "Upload Pricing Workbook",
          description: "Workbook has not been uploaded yet for cross-check and review.",
          status: "missing",
        },
      ],
    },
    "RFQ-2026-0126": {
      ...rfqRecords[2],
      description:
        "Fiber backbone expansion with protected conduits, rack integration, and field commissioning documentation.",
      industry: "Power",
      country: "Saudi Arabia",
      procurementLead: "F. Madani",
      estimatedSubmissionDate: "2026-04-02",
      stageNotes: [
        {
          id: "note-126-1",
          stageId: "submission",
          author: "Workbook Review",
          note: "Workbook validation failed because section C7 totals do not reconcile with the annex pricing matrix.",
          createdAt: "2026-03-31T07:40:00Z",
          tone: "warning",
        },
        {
          id: "note-126-2",
          stageId: "submission",
          author: "Program Manager",
          note: "Operational submission remains staged, but final dispatch is held until workbook review is cleared.",
          createdAt: "2026-03-31T08:10:00Z",
          tone: "info",
        },
      ],
      recentFiles: [
        {
          id: "file-126-zip",
          label: "rfq_0126_design_package.zip",
          type: "ZIP Intake",
          uploadedAt: "2026-03-24T13:25:00Z",
          uploadedBy: "L. Hamed",
          status: "processed",
        },
        {
          id: "file-126-workbook",
          label: "rfq_0126_commercial_v2.xlsx",
          type: "Workbook",
          uploadedAt: "2026-03-30T18:05:00Z",
          uploadedBy: "L. Hamed",
          status: "rejected",
        },
      ],
      subtasks: [
        {
          id: "task-126-1",
          label: "Repair workbook section C7 totals",
          owner: "L. Hamed",
          dueDate: "2026-03-31",
          state: "in_progress",
        },
        {
          id: "task-126-2",
          label: "Re-run workbook review",
          owner: "Intelligence Admin",
          dueDate: "2026-04-01",
          state: "open",
        },
      ],
      uploads: [
        {
          kind: "zip",
          title: "Upload RFQ Package ZIP",
          description: "Package is already parsed, but a new revision can be staged if needed.",
          status: "ready",
          fileName: "rfq_0126_design_package.zip",
          uploadedAt: "2026-03-24T13:25:00Z",
        },
        {
          kind: "workbook",
          title: "Upload Pricing Workbook",
          description: "Latest workbook review failed and is waiting for a corrected file.",
          status: "failed",
          fileName: "rfq_0126_commercial_v2.xlsx",
          uploadedAt: "2026-03-30T18:05:00Z",
        },
      ],
    },
    "RFQ-2026-0119": {
      ...rfqRecords[3],
      description:
        "Awarded maintenance support program spanning spare lots, field support, and scheduled servicing packs.",
      industry: "Industrial Systems",
      country: "Saudi Arabia",
      procurementLead: "S. Kareem",
      estimatedSubmissionDate: "2026-03-12",
      stageNotes: [
        {
          id: "note-119-1",
          stageId: "award",
          author: "Program Office",
          note: "Award confirmation received with no post-award workbook exceptions.",
          createdAt: "2026-03-28T10:55:00Z",
          tone: "success",
        },
      ],
      recentFiles: [
        {
          id: "file-119-zip",
          label: "rfq_0119_award_package.zip",
          type: "ZIP Intake",
          uploadedAt: "2026-03-10T08:05:00Z",
          uploadedBy: "S. Kareem",
          status: "processed",
        },
        {
          id: "file-119-workbook",
          label: "rfq_0119_final_award.xlsx",
          type: "Workbook",
          uploadedAt: "2026-03-11T17:20:00Z",
          uploadedBy: "S. Kareem",
          status: "processed",
        },
      ],
      subtasks: [
        {
          id: "task-119-1",
          label: "Publish lessons-learned briefing",
          owner: "Capture Team",
          dueDate: "2026-04-03",
          state: "open",
        },
      ],
      uploads: [
        {
          kind: "zip",
          title: "Upload RFQ Package ZIP",
          description: "Award archive package is available for reference only in demo mode.",
          status: "ready",
          fileName: "rfq_0119_award_package.zip",
          uploadedAt: "2026-03-10T08:05:00Z",
        },
        {
          kind: "workbook",
          title: "Upload Pricing Workbook",
          description: "Workbook is archived and can be refreshed for comparison.",
          status: "ready",
          fileName: "rfq_0119_final_award.xlsx",
          uploadedAt: "2026-03-11T17:20:00Z",
        },
      ],
    },
    "RFQ-2026-0151": {
      ...rfqRecords[4],
      description:
        "Diagnostic toolkit bid covering ruggedized test kits, calibration support, and field integration accessories.",
      industry: "Defense Systems",
      country: "Saudi Arabia",
      procurementLead: "J. Osman",
      estimatedSubmissionDate: "2026-04-11",
      stageNotes: [
        {
          id: "note-151-1",
          stageId: "review",
          author: "Bid Coordinator",
          note: "Client annex references one optional calibration station that is not priced in the workbook draft.",
          createdAt: "2026-03-30T12:05:00Z",
          tone: "warning",
        },
      ],
      recentFiles: [
        {
          id: "file-151-zip",
          label: "rfq_0151_diagnostics.zip",
          type: "ZIP Intake",
          uploadedAt: "2026-03-27T15:15:00Z",
          uploadedBy: "GHI Estimator",
          status: "processed",
        },
        {
          id: "file-151-workbook",
          label: "rfq_0151_pricing_draft.xlsx",
          type: "Workbook",
          uploadedAt: "2026-03-30T10:18:00Z",
          uploadedBy: "GHI Estimator",
          status: "pending",
        },
      ],
      subtasks: [
        {
          id: "task-151-1",
          label: "Confirm optional calibration station",
          owner: "H. Farouk",
          dueDate: "2026-04-01",
          state: "open",
        },
        {
          id: "task-151-2",
          label: "Re-check workbook mapping after annex update",
          owner: "Pricing Cell",
          dueDate: "2026-04-02",
          state: "in_progress",
        },
      ],
      uploads: [
        {
          kind: "zip",
          title: "Upload RFQ Package ZIP",
          description: "New client addenda can be staged and reprocessed.",
          status: "ready",
          fileName: "rfq_0151_diagnostics.zip",
          uploadedAt: "2026-03-27T15:15:00Z",
        },
        {
          kind: "workbook",
          title: "Upload Pricing Workbook",
          description: "Workbook is under processing and waiting for review completion.",
          status: "processing",
          fileName: "rfq_0151_pricing_draft.xlsx",
          uploadedAt: "2026-03-30T10:18:00Z",
        },
      ],
    },
    "RFQ-2026-0107": {
      ...rfqRecords[5],
      description:
        "Modernization bid for audiovisual integration, resilient command displays, and operator-room fit-out across the national command center estate.",
      industry: "Infrastructure",
      country: "Saudi Arabia",
      outcomeReason:
        "Lost on commercial competitiveness after the client selected a lower lead-time package with fewer compliance deviations.",
      procurementLead: "Estimation Manager",
      estimatedSubmissionDate: "2026-03-10",
      stageNotes: [
        {
          id: "note-107-1",
          stageId: "award",
          author: "Commercial Review",
          note: "Loss review confirmed that delivery lead-time and alternate compliance exceptions outweighed technical quality scoring.",
          createdAt: "2026-03-20T09:40:00Z",
          tone: "warning",
        },
      ],
      recentFiles: [
        {
          id: "file-107-zip",
          label: "rfq_0107_command_center.zip",
          type: "ZIP Intake",
          uploadedAt: "2026-03-02T08:30:00Z",
          uploadedBy: "Estimation Manager",
          status: "processed",
        },
        {
          id: "file-107-workbook",
          label: "rfq_0107_final_offer.xlsx",
          type: "Workbook",
          uploadedAt: "2026-03-09T18:10:00Z",
          uploadedBy: "Estimation Manager",
          status: "processed",
        },
      ],
      subtasks: [
        {
          id: "task-107-1",
          label: "Publish commercial loss review",
          owner: "Commercial Manager",
          dueDate: "2026-03-24",
          state: "done",
        },
      ],
      uploads: [
        {
          kind: "zip",
          title: "Upload RFQ Package ZIP",
          description: "Reference package retained for lessons-learned review.",
          status: "ready",
          fileName: "rfq_0107_command_center.zip",
          uploadedAt: "2026-03-02T08:30:00Z",
        },
        {
          kind: "workbook",
          title: "Upload Pricing Workbook",
          description: "Final offer workbook retained for post-mortem comparison.",
          status: "ready",
          fileName: "rfq_0107_final_offer.xlsx",
          uploadedAt: "2026-03-09T18:10:00Z",
        },
      ],
    },
    "RFQ-2026-0102": {
      id: "RFQ-2026-0102",
      title: "Coastal Security Tower Retrofit",
      client: "Maritime Protection Authority",
      owner: "GHI Estimator",
      region: "Jubail",
      industry: "Marine / Offshore",
      country: "Saudi Arabia",
      valueSar: 7600000,
      dueDate: "2026-03-06",
      createdAt: "2026-01-29",
      updatedAt: "2026-03-14",
      workflowId: "workflow-standard",
      workflowName: "Standard Bid Lifecycle",
      status: "lost",
      outcomeReason:
        "Lost after the client weighted local supplier coverage and maintenance response commitments above price parity.",
      intelligenceState: "complete",
      priority: "high",
      nextAction:
        "Capture the service-coverage gap and feed it into the next coastal infrastructure pursuit.",
      summaryLine:
        "Loss review shows service coverage and maintenance response commitments were the deciding factors.",
      tags: ["Lost", "Coverage Gap"],
      stageHistory: buildStageHistory(
        standardWorkflowStages,
        "award",
        "2026-03-14T11:20:00Z",
      ),
      description:
        "Retrofit bid for coastal observation towers covering ruggedized communications, power refresh, and maintenance support packs.",
      procurementLead: "Estimation Manager",
      estimatedSubmissionDate: "2026-03-05",
      stageNotes: [
        {
          id: "note-102-1",
          stageId: "award",
          author: "Commercial Review",
          note: "Client feedback highlighted maintenance response commitments and local service coverage as the main differentiators.",
          createdAt: "2026-03-14T11:20:00Z",
          tone: "warning",
        },
      ],
      recentFiles: [
        {
          id: "file-102-zip",
          label: "rfq_0102_coastal_package.zip",
          type: "ZIP Intake",
          uploadedAt: "2026-02-26T08:12:00Z",
          uploadedBy: "Estimation Manager",
          status: "processed",
        },
        {
          id: "file-102-workbook",
          label: "rfq_0102_service_offer.xlsx",
          type: "Workbook",
          uploadedAt: "2026-03-04T17:45:00Z",
          uploadedBy: "Estimation Manager",
          status: "processed",
        },
      ],
      subtasks: [
        {
          id: "task-102-1",
          label: "Document service-coverage lesson learned",
          owner: "Capture Team",
          dueDate: "2026-03-18",
          state: "done",
        },
      ],
      uploads: [
        {
          kind: "zip",
          title: "Upload RFQ Package ZIP",
          description: "Reference package preserved for future pursuit reviews.",
          status: "ready",
          fileName: "rfq_0102_coastal_package.zip",
          uploadedAt: "2026-02-26T08:12:00Z",
        },
        {
          kind: "workbook",
          title: "Upload Pricing Workbook",
          description: "Workbook retained for service-model comparison.",
          status: "ready",
          fileName: "rfq_0102_service_offer.xlsx",
          uploadedAt: "2026-03-04T17:45:00Z",
        },
      ],
    },
  };

function getLocalDateIsoString(baseDate = new Date()) {
  const year = baseDate.getFullYear();
  const month = `${baseDate.getMonth() + 1}`.padStart(2, "0");
  const day = `${baseDate.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getNextDemoRfqId() {
  const now = new Date();
  const currentYear = now.getFullYear();
  const maxSequence = managerRfqListResponse.items.reduce((highest, rfq) => {
    const match = /^RFQ-(\d{4})-(\d{4})$/.exec(rfq.id);
    if (!match) {
      return highest;
    }

    const [, year, sequence] = match;
    if (Number.parseInt(year, 10) !== currentYear) {
      return highest;
    }

    return Math.max(highest, Number.parseInt(sequence, 10));
  }, 0);

  return `RFQ-${currentYear}-${String(maxSequence + 1).padStart(4, "0")}`;
}

export function createDemoRfq(
  input: CreateRfqInput,
): ManagerRfqDetailResponse {
  const workflow = managerWorkflowResponses.find(
    (candidate) => candidate.id === input.workflowId,
  );

  if (!workflow) {
    throw new Error(`Workflow '${input.workflowId}' not found in demo mode.`);
  }

  if ((input.skipStageIds?.length ?? 0) > 0 && workflow.selectionMode !== "customizable") {
    throw new Error("Stage selection is only allowed for customizable workflows.");
  }

  const skippedRequiredStage = workflow.stages.find(
    (stage) => stage.isRequired && (input.skipStageIds ?? []).includes(stage.id),
  );
  if (skippedRequiredStage) {
    throw new Error("Required workflow stages cannot be removed.");
  }

  const selectedStages = workflow.stages.filter(
    (stage) => !(input.skipStageIds ?? []).includes(stage.id),
  );

  if (selectedStages.length === 0) {
    throw new Error("Customized workflow must keep at least one stage.");
  }

  const now = new Date();
  const createdDate = getLocalDateIsoString(now);
  const createdTimestamp = now.toISOString();
  const firstStage = selectedStages[0];
  const nextStage = selectedStages[1];
  const rfqId = getNextDemoRfqId();

  const listItem: ManagerRfqListItemResponse = {
    id: rfqId,
    title: input.name,
    client: input.client,
    owner: input.owner,
    region: input.country ?? "Not specified",
    valueSar: 0,
    dueDate: input.deadline,
    createdAt: createdDate,
    updatedAt: createdDate,
    workflowId: workflow.id,
    workflowName: workflow.name,
    status: "in_preparation",
    intelligenceState: "pending",
    priority: input.priority,
    nextAction: nextStage
      ? `Prepare ${nextStage.label.toLowerCase()} after intake alignment.`
      : "Kick off the first workflow stage.",
    summaryLine:
      "RFQ created successfully. Workflow stages were generated and the lifecycle started in preparation.",
    tags: ["New RFQ"],
    stageHistory: buildStageHistory(
      selectedStages,
      firstStage.id,
      createdTimestamp,
    ),
  };

  const detail: ManagerRfqDetailResponse = {
    ...listItem,
    description: input.description ?? "",
    industry: input.industry,
    country: input.country,
    procurementLead: input.owner,
    estimatedSubmissionDate: input.deadline,
    stageNotes: [],
    recentFiles: [],
    subtasks: [],
    uploads: [
      {
        kind: "zip",
        title: "Upload RFQ Package ZIP",
        description: "Stage the RFQ package to start intelligence and workspace enrichment.",
        status: "missing",
      },
      {
        kind: "workbook",
        title: "Upload Pricing Workbook",
        description: "Add the pricing workbook when the package is ready for working review.",
        status: "missing",
      },
    ],
  };

  managerRfqListResponse.items.unshift(listItem);
  managerRfqDetailResponses[rfqId] = detail;

  return detail;
}

export function updateDemoRfq(
  rfqId: string,
  input: Partial<CreateRfqInput> & {
    outcomeReason?: string;
    status?: ManagerRfqDetailResponse["status"];
  },
): ManagerRfqDetailResponse {
  const detail = managerRfqDetailResponses[rfqId];
  if (!detail) {
    throw new Error(`RFQ '${rfqId}' not found in demo mode.`);
  }

  const normalizedUpdatedAt = new Date().toISOString();
  const normalizedUpdatedDate = normalizedUpdatedAt.slice(0, 10);

  const updatedDetail: ManagerRfqDetailResponse = {
    ...detail,
    title: input.name ?? detail.title,
    client: input.client ?? detail.client,
    owner: input.owner ?? detail.owner,
    dueDate: input.deadline ?? detail.dueDate,
    updatedAt: normalizedUpdatedDate,
    status: input.status ?? detail.status,
    outcomeReason: input.outcomeReason ?? detail.outcomeReason,
    priority: input.priority ?? detail.priority,
    description: input.description ?? detail.description,
    industry: input.industry ?? detail.industry,
    country: input.country ?? detail.country,
  };

  managerRfqDetailResponses[rfqId] = updatedDetail;

  const listIndex = managerRfqListResponse.items.findIndex((item) => item.id === rfqId);
  if (listIndex >= 0) {
    managerRfqListResponse.items[listIndex] = {
      ...managerRfqListResponse.items[listIndex],
      title: updatedDetail.title,
      client: updatedDetail.client,
      owner: updatedDetail.owner,
      dueDate: updatedDetail.dueDate,
      updatedAt: normalizedUpdatedDate,
      status: updatedDetail.status,
      outcomeReason: updatedDetail.outcomeReason,
      priority: updatedDetail.priority,
      region:
        updatedDetail.country ??
        managerRfqListResponse.items[listIndex].region,
    };
  }

  return updatedDetail;
}

export function cancelDemoRfq(
  rfqId: string,
  input: CancelRfqInput,
): ManagerRfqDetailResponse {
  return updateDemoRfq(rfqId, {
    outcomeReason: input.outcomeReason,
    status: "cancelled",
  });
}
