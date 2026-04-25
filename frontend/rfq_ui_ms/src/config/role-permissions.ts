import type { AppRole } from "@/models/ui/role";
import {
  getCapabilityGrant,
  getRoleCapabilityBundle,
  isCapabilityAllowed,
  isCapabilityReadable,
} from "@/config/role-capabilities";

export interface RolePermissions {
  canAcknowledgeLeadershipNotes: boolean;
  canAdvanceStage: boolean;
  canCloseLeadershipNotes: boolean;
  canCreateLeadershipNotes: boolean;
  canCreateRfq: boolean;
  canDeleteFiles: boolean;
  canReadRfqLifecycle: boolean;
  canEditCoreRfq: boolean;
  canManageReminders: boolean;
  canManageStageNotes: boolean;
  canManageStageWorkspace: boolean;
  canManageSubtasks: boolean;
  canReadEscalationState: boolean;
  canReadLeadershipNotes: boolean;
  canReadOperationalWorkspace: boolean;
  canReprocessArtifacts: boolean;
  canReplyLeadershipNotes: boolean;
  canTriggerIntelligence: boolean;
  canUploadFiles: boolean;
  canViewAllRfqs: boolean;
  canViewAnalytics: boolean;
  canViewArtifacts: boolean;
  canViewIntelligence: boolean;
  canViewIntelligenceDiagnostics: boolean;
  canViewIntelligenceSummary: boolean;
  canViewSupportiveIntelligence: boolean;
  canViewPortfolio: boolean;
  dashboardSubtitle: string;
  dashboardTitle: string;
  detailTabs: readonly string[];
  listSubtitle: string;
  listTitle: string;
  overviewSubtitle: string;
  overviewTitle: string;
  primaryCta: { label: string; href: string } | null;
}

function createPermissions(role: AppRole): RolePermissions {
  const bundle = getRoleCapabilityBundle(role);

  return {
    canAcknowledgeLeadershipNotes: isCapabilityAllowed(
      getCapabilityGrant(role, "leadership_note.acknowledge"),
    ),
    canAdvanceStage: isCapabilityAllowed(getCapabilityGrant(role, "rfq.stage.advance")),
    canCloseLeadershipNotes: isCapabilityAllowed(
      getCapabilityGrant(role, "leadership_note.close"),
    ),
    canCreateLeadershipNotes: isCapabilityAllowed(
      getCapabilityGrant(role, "leadership_note.create"),
    ),
    canCreateRfq: isCapabilityAllowed(getCapabilityGrant(role, "rfq.create")),
    canDeleteFiles: isCapabilityAllowed(getCapabilityGrant(role, "file.delete")),
    canReadRfqLifecycle: isCapabilityReadable(
      getCapabilityGrant(role, "rfq.lifecycle.read"),
    ),
    canEditCoreRfq: isCapabilityAllowed(getCapabilityGrant(role, "rfq.core.update")),
    canManageReminders: isCapabilityAllowed(getCapabilityGrant(role, "reminder.manage")),
    canManageStageNotes: isCapabilityAllowed(
      getCapabilityGrant(role, "rfq.stage.note.write"),
    ),
    canManageStageWorkspace: isCapabilityAllowed(
      getCapabilityGrant(role, "rfq.stage.update"),
    ),
    canManageSubtasks: isCapabilityAllowed(getCapabilityGrant(role, "subtask.manage")),
    canReadEscalationState: isCapabilityReadable(
      getCapabilityGrant(role, "escalation.state.read"),
    ),
    canReadLeadershipNotes: isCapabilityReadable(
      getCapabilityGrant(role, "leadership_note.read"),
    ),
    canReadOperationalWorkspace: isCapabilityReadable(
      getCapabilityGrant(role, "rfq.workspace.operational.read"),
    ),
    canReprocessArtifacts: isCapabilityAllowed(
      getCapabilityGrant(role, "rfq.intelligence.reprocess"),
    ),
    canReplyLeadershipNotes: isCapabilityAllowed(
      getCapabilityGrant(role, "leadership_note.reply"),
    ),
    canTriggerIntelligence: isCapabilityAllowed(
      getCapabilityGrant(role, "rfq.intelligence.reprocess"),
    ),
    canUploadFiles: isCapabilityAllowed(getCapabilityGrant(role, "file.upload")),
    canViewAllRfqs: role !== "estimator",
    canViewAnalytics: isCapabilityAllowed(getCapabilityGrant(role, "analytics.read")),
    canViewArtifacts: role !== "executive",
    canViewIntelligence: isCapabilityReadable(
      getCapabilityGrant(role, "rfq.intelligence.summary.read"),
    ),
    canViewIntelligenceDiagnostics: isCapabilityReadable(
      getCapabilityGrant(role, "rfq.intelligence.diagnostics.read"),
    ),
    canViewIntelligenceSummary: isCapabilityReadable(
      getCapabilityGrant(role, "rfq.intelligence.summary.read"),
    ),
    canViewSupportiveIntelligence: isCapabilityReadable(
      getCapabilityGrant(role, "rfq.intelligence.supportive.read"),
    ),
    canViewPortfolio: isCapabilityReadable(
      getCapabilityGrant(role, "portfolio.monitor.read"),
    ),
    dashboardSubtitle: bundle.pageChrome.dashboardSubtitle,
    dashboardTitle: bundle.pageChrome.dashboardTitle,
    detailTabs:
      role === "executive"
        ? ["intelligence"]
        : ["operational", "intelligence", "artifacts"],
    listSubtitle: bundle.pageChrome.listSubtitle,
    listTitle: bundle.pageChrome.listTitle,
    overviewSubtitle: bundle.pageChrome.overviewSubtitle,
    overviewTitle: bundle.pageChrome.overviewTitle,
    primaryCta:
      role === "executive" || !isCapabilityAllowed(getCapabilityGrant(role, "rfq.create"))
        ? null
        : { label: "Create RFQ", href: "/rfqs/new" },
  };
}

export const rolePermissions: Record<AppRole, RolePermissions> = {
  executive: createPermissions("executive"),
  manager: createPermissions("manager"),
  estimator: createPermissions("estimator"),
} as const;

export function getPermissions(role: AppRole): RolePermissions {
  return rolePermissions[role];
}
