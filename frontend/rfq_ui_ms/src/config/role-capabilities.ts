import type { AppRole } from "@/models/ui/role";

export type CapabilityAccess = "allowed" | "read_only" | "hidden" | "conditional";

export type CapabilityScope =
  | "tenant-wide"
  | "department-wide"
  | "all department RFQs"
  | "assigned RFQs"
  | "new RFQs"
  | "own uploads";

export type RoleCapabilityKey =
  | "portfolio.monitor.read"
  | "rfq.lifecycle.read"
  | "rfq.intelligence.summary.read"
  | "rfq.workspace.operational.read"
  | "analytics.read"
  | "rfq.create"
  | "rfq.core.update"
  | "rfq.stage.update"
  | "rfq.stage.advance"
  | "subtask.manage"
  | "file.upload"
  | "file.delete"
  | "rfq.stage.note.write"
  | "reminder.manage"
  | "escalation.state.read"
  | "leadership_note.create"
  | "leadership_note.read"
  | "leadership_note.acknowledge"
  | "leadership_note.reply"
  | "leadership_note.close"
  | "rfq.intelligence.supportive.read"
  | "rfq.intelligence.diagnostics.read"
  | "rfq.intelligence.reprocess";

export interface CapabilityGrant {
  access: CapabilityAccess;
  scopes: readonly CapabilityScope[];
  note?: string;
}

export interface RoleCapabilityBundle {
  managerPermissions: readonly string[];
  pageChrome: {
    dashboardSubtitle: string;
    dashboardTitle: string;
    listSubtitle: string;
    listTitle: string;
    overviewSubtitle: string;
    overviewTitle: string;
  };
  capabilities: Record<RoleCapabilityKey, CapabilityGrant>;
}

function grant(
  access: CapabilityAccess,
  scopes: readonly CapabilityScope[],
  note?: string,
): CapabilityGrant {
  return {
    access,
    note,
    scopes,
  };
}

export const roleCapabilityBundles: Record<AppRole, RoleCapabilityBundle> = {
  executive: {
    managerPermissions: [
      "rfq:read",
      "rfq:stats",
      "rfq:analytics",
      "rfq_stage:read",
    ],
    pageChrome: {
      dashboardSubtitle:
        "Strategic posture, lifecycle risk, and leadership-ready conversion signals.",
      dashboardTitle: "Executive Dashboard",
      listSubtitle:
        "Read-only strategic monitor for lifecycle posture, blockers, delays, and outcome visibility.",
      listTitle: "Strategic RFQ Monitor",
      overviewSubtitle:
        "Strategic overview stays on the dashboard and RFQ monitor rather than the operational overview.",
      overviewTitle: "Executive View",
    },
    capabilities: {
      "portfolio.monitor.read": grant("allowed", ["tenant-wide", "department-wide"]),
      "rfq.lifecycle.read": grant("read_only", ["all department RFQs"]),
      "rfq.intelligence.summary.read": grant("read_only", ["all department RFQs"]),
      "rfq.workspace.operational.read": grant("hidden", []),
      "analytics.read": grant("allowed", ["tenant-wide", "department-wide"]),
      "rfq.create": grant("hidden", []),
      "rfq.core.update": grant("hidden", []),
      "rfq.stage.update": grant("hidden", []),
      "rfq.stage.advance": grant("hidden", []),
      "subtask.manage": grant("hidden", []),
      "file.upload": grant("hidden", []),
      "file.delete": grant("hidden", []),
      "rfq.stage.note.write": grant("hidden", []),
      "reminder.manage": grant("hidden", []),
      "escalation.state.read": grant("allowed", ["all department RFQs"]),
      "leadership_note.create": grant("allowed", ["department-wide"]),
      "leadership_note.read": grant("allowed", ["department-wide"]),
      "leadership_note.acknowledge": grant("hidden", []),
      "leadership_note.reply": grant("hidden", []),
      "leadership_note.close": grant("hidden", []),
      "rfq.intelligence.supportive.read": grant("hidden", []),
      "rfq.intelligence.diagnostics.read": grant("hidden", []),
      "rfq.intelligence.reprocess": grant("hidden", []),
    },
  },
  manager: {
    managerPermissions: [
      "rfq:create",
      "rfq:read",
      "rfq:update",
      "rfq:export",
      "rfq:stats",
      "rfq:analytics",
      "workflow:read",
      "rfq_stage:read",
      "rfq_stage:update",
      "rfq_stage:advance",
      "rfq_stage:add_note",
      "rfq_stage:add_file",
      "subtask:create",
      "subtask:read",
      "subtask:update",
      "subtask:delete",
      "reminder:create",
      "reminder:read",
      "reminder:update",
      "reminder:update_rules",
      "reminder:test",
      "reminder:process",
      "file:list",
      "file:download",
      "file:delete",
    ],
    pageChrome: {
      dashboardSubtitle:
        "Department-wide operational control, analytics, and intelligence posture.",
      dashboardTitle: "Department Dashboard",
      listSubtitle:
        "Operational queue for active RFQs, workflow progression, and intervention signals.",
      listTitle: "Operational RFQ Queue",
      overviewSubtitle:
        "Department-wide lifecycle health, intelligence posture, and operational throughput.",
      overviewTitle: "Operational Overview",
    },
    capabilities: {
      "portfolio.monitor.read": grant("allowed", ["department-wide"]),
      "rfq.lifecycle.read": grant("allowed", ["department-wide"]),
      "rfq.intelligence.summary.read": grant("allowed", ["department-wide"]),
      "rfq.workspace.operational.read": grant("allowed", ["department-wide"]),
      "analytics.read": grant("allowed", ["department-wide"]),
      "rfq.create": grant("allowed", ["department-wide"]),
      "rfq.core.update": grant("allowed", ["department-wide"]),
      "rfq.stage.update": grant("allowed", ["department-wide"]),
      "rfq.stage.advance": grant("allowed", ["department-wide"]),
      "subtask.manage": grant("allowed", ["department-wide"]),
      "file.upload": grant("allowed", ["department-wide"]),
      "file.delete": grant("allowed", ["department-wide"]),
      "rfq.stage.note.write": grant("allowed", ["department-wide"]),
      "reminder.manage": grant("allowed", ["department-wide"]),
      "escalation.state.read": grant("allowed", ["department-wide"]),
      "leadership_note.create": grant("hidden", []),
      "leadership_note.read": grant("allowed", ["department-wide"]),
      "leadership_note.acknowledge": grant("allowed", ["department-wide"]),
      "leadership_note.reply": grant("allowed", ["department-wide"]),
      "leadership_note.close": grant("allowed", ["department-wide"]),
      "rfq.intelligence.supportive.read": grant("allowed", ["department-wide"]),
      "rfq.intelligence.diagnostics.read": grant("allowed", ["department-wide"]),
      "rfq.intelligence.reprocess": grant("allowed", ["department-wide"]),
    },
  },
  estimator: {
    managerPermissions: [
      "rfq:create",
      "rfq:read",
      "rfq:update",
      "workflow:read",
      "rfq_stage:read",
      "rfq_stage:add_file",
      "subtask:create",
      "subtask:read",
      "subtask:update",
      "subtask:delete",
      "reminder:read",
      "file:list",
      "file:download",
      "file:delete",
    ],
    pageChrome: {
      dashboardSubtitle:
        "Estimator access stays on assignments and contributor work rather than portfolio analytics.",
      dashboardTitle: "Estimator View",
      listSubtitle:
        "Assigned RFQs with contributor-only lifecycle and intelligence access.",
      listTitle: "Assigned RFQ Worklist",
      overviewSubtitle:
        "Assigned RFQs, next actions, and scoped contributor signals for your working set.",
      overviewTitle: "My Assignments",
    },
    capabilities: {
      "portfolio.monitor.read": grant("hidden", []),
      "rfq.lifecycle.read": grant("allowed", ["assigned RFQs"]),
      "rfq.intelligence.summary.read": grant("allowed", ["assigned RFQs"]),
      "rfq.workspace.operational.read": grant(
        "read_only",
        ["assigned RFQs"],
      ),
      "analytics.read": grant("hidden", []),
      "rfq.create": grant("allowed", ["new RFQs"]),
      "rfq.core.update": grant("hidden", []),
      "rfq.stage.update": grant("hidden", []),
      "rfq.stage.advance": grant("hidden", []),
      "subtask.manage": grant("allowed", ["assigned RFQs"]),
      "file.upload": grant("allowed", ["assigned RFQs"]),
      "file.delete": grant("allowed", ["own uploads"]),
      "rfq.stage.note.write": grant("hidden", []),
      "reminder.manage": grant("hidden", []),
      "escalation.state.read": grant("read_only", ["assigned RFQs"]),
      "leadership_note.create": grant("hidden", []),
      "leadership_note.read": grant("hidden", []),
      "leadership_note.acknowledge": grant("hidden", []),
      "leadership_note.reply": grant("hidden", []),
      "leadership_note.close": grant("hidden", []),
      "rfq.intelligence.supportive.read": grant("allowed", ["assigned RFQs"]),
      "rfq.intelligence.diagnostics.read": grant(
        "read_only",
        ["assigned RFQs"],
      ),
      "rfq.intelligence.reprocess": grant("hidden", []),
    },
  },
} as const;

export function getRoleCapabilityBundle(role: AppRole): RoleCapabilityBundle {
  return roleCapabilityBundles[role];
}

export function getCapabilityGrant(
  role: AppRole,
  capability: RoleCapabilityKey,
): CapabilityGrant {
  return roleCapabilityBundles[role].capabilities[capability];
}

export function isCapabilityReadable(grant: CapabilityGrant): boolean {
  return grant.access === "allowed" || grant.access === "read_only";
}

export function isCapabilityAllowed(grant: CapabilityGrant): boolean {
  return grant.access === "allowed";
}
