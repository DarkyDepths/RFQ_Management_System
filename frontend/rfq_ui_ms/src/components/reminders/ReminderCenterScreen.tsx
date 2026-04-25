"use client";

import { EmptyState } from "@/components/common/EmptyState";
import { ReminderCenterPanel } from "@/components/reminders/ReminderCenterPanel";
import { getPermissions } from "@/config/role-permissions";
import { useRole } from "@/context/role-context";

export function ReminderCenterScreen() {
  const { role } = useRole();
  const permissions = getPermissions(role);

  if (role !== "manager" || !permissions.canViewPortfolio || !permissions.canManageReminders) {
    return (
      <EmptyState
        description="Reminder Center is reserved for manager-owned service-wide reminder controls."
        title="Reminder Center unavailable"
      />
    );
  }

  return <ReminderCenterPanel permissions={permissions} />;
}
