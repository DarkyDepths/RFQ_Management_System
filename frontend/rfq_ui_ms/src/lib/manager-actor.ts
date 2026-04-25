import { apiConfig } from "@/config/api";
import { appConfig } from "@/config/app";
import { getRoleCapabilityBundle } from "@/config/role-capabilities";
import type { AppRole } from "@/models/ui/role";

const STORAGE_KEY = "rfq-ui-ms-role";

const defaultTeamByRole: Record<AppRole, string> = {
  executive: "Executive",
  manager: "Estimation",
  estimator: "Estimation",
};

const defaultNameByRole: Record<AppRole, string> = {
  executive: "Executive Leadership",
  manager: "Estimation Manager",
  estimator: "GHI Estimator",
};

const defaultUserIdByRole: Record<AppRole, string> = {
  executive: "exec-leadership",
  manager: "estimation-manager",
  estimator: "ghi-estimator",
};

export interface ManagerActorOptions {
  permissions?: string[];
  team?: string;
  userId?: string;
  userName?: string;
}

export interface RoleActorProfile {
  permissions: string[];
  team: string;
  userId: string;
  userName: string;
}

function isRole(value: string | null): value is AppRole {
  return value === "executive" || value === "manager" || value === "estimator";
}

export function getCurrentAppRole(): AppRole {
  if (typeof window === "undefined") {
    return appConfig.defaultRole;
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isRole(stored) ? stored : appConfig.defaultRole;
}

export function getRoleActorProfile(role: AppRole): RoleActorProfile {
  return {
    permissions: [...getRoleCapabilityBundle(role).managerPermissions],
    team: defaultTeamByRole[role],
    userId: defaultUserIdByRole[role],
    userName: defaultNameByRole[role],
  };
}

export function buildManagerActorHeaders(
  options?: ManagerActorOptions,
): HeadersInit {
  if (!apiConfig.managerDebugHeadersEnabled) {
    return {};
  }

  const role = getCurrentAppRole();
  const actorProfile = getRoleActorProfile(role);
  const permissions = options?.permissions?.length
    ? options.permissions.join(",")
    : actorProfile.permissions.join(",");

  return {
    "X-Debug-User-Id": options?.userId ?? actorProfile.userId,
    "X-Debug-User-Name": options?.userName ?? actorProfile.userName,
    "X-Debug-User-Team": options?.team ?? actorProfile.team,
    "X-Debug-Permissions": permissions,
  };
}
