import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const workspaceSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RfqOperationalWorkspace.tsx"),
  "utf8",
);
const overviewSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQOverviewScreen.tsx"),
  "utf8",
);
const summaryCardSource = await readFile(
  path.join(process.cwd(), "src", "components", "reminders", "ReminderCenterSummaryCard.tsx"),
  "utf8",
);
const centerPanelSource = await readFile(
  path.join(process.cwd(), "src", "components", "reminders", "ReminderCenterPanel.tsx"),
  "utf8",
);
const centerScreenSource = await readFile(
  path.join(process.cwd(), "src", "components", "reminders", "ReminderCenterScreen.tsx"),
  "utf8",
);
const remindersPageSource = await readFile(
  path.join(process.cwd(), "src", "app", "(dashboard)", "reminders", "page.tsx"),
  "utf8",
);
const reminderDialogSource = await readFile(
  path.join(process.cwd(), "src", "components", "reminders", "ReminderDetailDialog.tsx"),
  "utf8",
);
const rfqHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-rfq-reminders.ts"),
  "utf8",
);
const centerHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-reminder-center.ts"),
  "utf8",
);
const summaryHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-reminder-summary.ts"),
  "utf8",
);
const navigationSource = await readFile(
  path.join(process.cwd(), "src", "config", "navigation.ts"),
  "utf8",
);
const permissionsSource = await readFile(
  path.join(process.cwd(), "src", "config", "role-capabilities.ts"),
  "utf8",
);
const reminderUtilsSource = await readFile(
  path.join(process.cwd(), "src", "utils", "reminder.ts"),
  "utf8",
);

assert.ok(workspaceSource.includes("Create and review reminders attached to this RFQ here."));
assert.ok(workspaceSource.includes("Reminder Center"));
assert.ok(workspaceSource.includes("Reminder scope"));
assert.ok(workspaceSource.includes("Stage-linked"));
assert.ok(workspaceSource.includes("RFQ-level"));
assert.ok(workspaceSource.includes("This reminder will follow the RFQ as a whole"));
assert.ok(workspaceSource.includes('rfqStageId: reminderForm.scope === "stage" ? currentStageId : undefined'));
assert.ok(!workspaceSource.includes("rfqStageId: currentStageId"));
assert.ok(workspaceSource.includes("Resolve"));
assert.ok(workspaceSource.includes("View details"));
assert.ok(workspaceSource.includes("reminderDueDateValidationMessage"));
assert.ok(workspaceSource.includes("getReminderTypeLabel(reminder.type)"));
assert.ok(!workspaceSource.includes("Portfolio Reminder Service"));
assert.ok(!workspaceSource.includes("Process Due"));
assert.ok(!workspaceSource.includes("Test Email"));

assert.ok(overviewSource.includes("ReminderCenterSummaryCard"));
assert.ok(!overviewSource.includes("<ReminderCenterPanel"));

assert.ok(summaryCardSource.includes("Reminder Snapshot"));
assert.ok(summaryCardSource.includes("Open Reminder Center"));
assert.ok(!summaryCardSource.includes("Run Batch Now"));
assert.ok(!summaryCardSource.includes("Reminder Rules"));

assert.ok(centerPanelSource.includes("Reminder Center"));
assert.ok(centerPanelSource.includes("Run Batch Now"));
assert.ok(centerPanelSource.includes("Service-wide Reminders"));
assert.ok(centerPanelSource.includes("records"));
assert.ok(centerPanelSource.includes("Reminder Rules"));
assert.ok(centerPanelSource.includes("Automatic reminders are batch-driven."));
assert.ok(centerPanelSource.includes("resolveReminder"));
assert.ok(centerPanelSource.includes("Show all records"));
assert.ok(centerPanelSource.includes("overdue first"));
assert.ok(centerPanelSource.includes("View details"));
assert.ok(centerPanelSource.includes("getReminderTypeLabel(reminder.type)"));

assert.ok(centerScreenSource.includes("ReminderCenterPanel"));
assert.ok(centerScreenSource.includes('role !== "manager"'));
assert.ok(remindersPageSource.includes("ReminderCenterScreen"));

assert.ok(rfqHookSource.includes("getRfqReminders"));
assert.ok(!rfqHookSource.includes("getReminderStats"));
assert.ok(!rfqHookSource.includes("getReminderRules"));

assert.ok(centerHookSource.includes("listReminders"));
assert.ok(centerHookSource.includes("getReminderStats"));
assert.ok(centerHookSource.includes("getReminderRules"));
assert.ok(summaryHookSource.includes("getReminderStats"));
assert.ok(!summaryHookSource.includes("getReminderRules"));
assert.ok(!summaryHookSource.includes("listReminders"));

assert.ok(navigationSource.includes("Reminder Center"));
assert.ok(navigationSource.includes('href: "/reminders"'));
assert.ok(navigationSource.includes('roles: ["manager"]'));

assert.ok(permissionsSource.includes('"reminder:update"'));
assert.ok(reminderDialogSource.includes("Reminder Detail"));
assert.ok(reminderDialogSource.includes("Reminder Message"));
assert.ok(reminderDialogSource.includes("RFQ-level reminder"));
assert.ok(reminderUtilsSource.includes("Reminder due date cannot be in the past."));
assert.ok(reminderUtilsSource.includes("sortRemindersForDisplay"));
