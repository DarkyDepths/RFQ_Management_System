import type { RolePermissions } from "@/config/role-permissions";
import type {
  RfqCardModel,
  RfqDetailModel,
  RfqFileModel,
} from "@/models/manager/rfq";
import type { AppRole } from "@/models/ui/role";

type ScopedRfq = Pick<RfqCardModel | RfqDetailModel, "owner" | "status">;

function normalize(value?: string | null) {
  return (value ?? "").trim().toLowerCase();
}

export function matchesActorName(actorName: string, candidate?: string | null) {
  const normalizedActor = normalize(actorName);
  const normalizedCandidate = normalize(candidate);

  return normalizedActor.length > 0 && normalizedActor === normalizedCandidate;
}

export function isAssignedRfq(
  rfq: ScopedRfq,
  actorName: string,
) {
  return matchesActorName(actorName, rfq.owner);
}

export function hasScopedEstimatorAccess(
  rfq: ScopedRfq,
  actorName: string,
) {
  return isAssignedRfq(rfq, actorName);
}

export function canReadRfqLifecycle(
  role: AppRole,
  permissions: RolePermissions,
  rfq: ScopedRfq,
  actorName: string,
) {
  if (!permissions.canReadRfqLifecycle) {
    return false;
  }

  if (role === "manager" || role === "executive") {
    return true;
  }

  return hasScopedEstimatorAccess(rfq, actorName);
}

export function canReadOperationalWorkspace(
  role: AppRole,
  permissions: RolePermissions,
  rfq: ScopedRfq,
  actorName: string,
) {
  if (!permissions.canReadOperationalWorkspace) {
    return false;
  }

  if (role === "manager") {
    return true;
  }

  if (role === "executive") {
    return false;
  }

  return hasScopedEstimatorAccess(rfq, actorName);
}

export function canManageSubtasks(
  role: AppRole,
  permissions: RolePermissions,
  rfq: ScopedRfq,
  actorName: string,
) {
  if (!permissions.canManageSubtasks) {
    return false;
  }

  return role === "manager" || hasScopedEstimatorAccess(rfq, actorName);
}

export function canUploadStageFiles(
  role: AppRole,
  permissions: RolePermissions,
  rfq: ScopedRfq,
  actorName: string,
) {
  if (!permissions.canUploadFiles) {
    return false;
  }

  return role === "manager" || hasScopedEstimatorAccess(rfq, actorName);
}

export function canDeleteStageFile(
  role: AppRole,
  permissions: RolePermissions,
  rfq: ScopedRfq,
  file: Pick<RfqFileModel, "uploadedBy">,
  actorName: string,
) {
  if (!permissions.canDeleteFiles) {
    return false;
  }

  if (role === "manager") {
    return true;
  }

  return hasScopedEstimatorAccess(rfq, actorName)
    && matchesActorName(actorName, file.uploadedBy);
}

export function canReadEscalationState(
  role: AppRole,
  permissions: RolePermissions,
  rfq: ScopedRfq,
  actorName: string,
) {
  if (!permissions.canReadEscalationState) {
    return false;
  }

  if (role === "manager" || role === "executive") {
    return true;
  }

  return hasScopedEstimatorAccess(rfq, actorName);
}

export function filterRfqsForRole(
  role: AppRole,
  permissions: RolePermissions,
  rfqs: RfqCardModel[],
  actorName: string,
) {
  if (role === "manager" || role === "executive" || permissions.canViewAllRfqs) {
    return rfqs;
  }

  return rfqs.filter((rfq) => hasScopedEstimatorAccess(rfq, actorName));
}
