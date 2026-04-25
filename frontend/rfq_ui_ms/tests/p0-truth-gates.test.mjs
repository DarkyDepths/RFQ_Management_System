import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const apiSource = await readFile(
  path.join(process.cwd(), "src", "config", "api.ts"),
  "utf8",
);
const navigationSource = await readFile(
  path.join(process.cwd(), "src", "config", "navigation.ts"),
  "utf8",
);
const rfqConnectorSource = await readFile(
  path.join(process.cwd(), "src", "connectors", "manager", "rfqs.ts"),
  "utf8",
);
const stageConnectorSource = await readFile(
  path.join(process.cwd(), "src", "connectors", "manager", "stages.ts"),
  "utf8",
);
const reminderConnectorSource = await readFile(
  path.join(process.cwd(), "src", "connectors", "manager", "reminders.ts"),
  "utf8",
);
const apiRfqModelSource = await readFile(
  path.join(process.cwd(), "src", "models", "manager", "api-rfq.ts"),
  "utf8",
);
const rfqTranslatorSource = await readFile(
  path.join(process.cwd(), "src", "translators", "manager", "rfqs.ts"),
  "utf8",
);
const listHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-rfq-list.ts"),
  "utf8",
);
const demoStatusSource = await readFile(
  path.join(process.cwd(), "src", "demo", "manager", "status.ts"),
  "utf8",
);
const sharedStatusSource = await readFile(
  path.join(process.cwd(), "src", "utils", "status.ts"),
  "utf8",
);
const listScreenSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQListScreen.tsx"),
  "utf8",
);
const overviewScreenSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQOverviewScreen.tsx"),
  "utf8",
);
const overviewHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-overview-data.ts"),
  "utf8",
);
const roleCapabilitiesSource = await readFile(
  path.join(process.cwd(), "src", "config", "role-capabilities.ts"),
  "utf8",
);
const rolePermissionsSource = await readFile(
  path.join(process.cwd(), "src", "config", "role-permissions.ts"),
  "utf8",
);
const rfqAccessSource = await readFile(
  path.join(process.cwd(), "src", "lib", "rfq-access.ts"),
  "utf8",
);
const workspaceSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RfqOperationalWorkspace.tsx"),
  "utf8",
);
const dashboardSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "DashboardScreen.tsx"),
  "utf8",
);

assert.ok(
  apiSource.includes(
    'const useMockData = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";',
  ),
);
assert.ok(
  navigationSource.includes(
    'const showFeaturedDetail = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";',
  ),
);

assert.ok(
  rfqConnectorSource.includes("Computed from awarded versus lost demo RFQs."),
);
assert.ok(
  rfqConnectorSource.includes("Margin analytics are intentionally withheld until a reliable source exists."),
);
assert.ok(!rfqConnectorSource.includes("value: 31"));
assert.ok(!rfqConnectorSource.includes("value: 74"));
assert.ok(!rfqConnectorSource.includes("value: 19"));
assert.ok(!rfqConnectorSource.includes("value: 23"));

assert.ok(
  stageConnectorSource.includes("Stage mutations are disabled in demo mode."),
);
assert.ok(
  reminderConnectorSource.includes(
    "Reminder service stays live-only in this phase.",
  ),
);
assert.ok(!apiRfqModelSource.includes('"Draft"'));
assert.ok(!apiRfqModelSource.includes('"Submitted"'));
assert.ok(apiRfqModelSource.includes("current_stage_id?: string | null;"));
assert.ok(apiRfqModelSource.includes("current_stage_order?: number | null;"));
assert.ok(apiRfqModelSource.includes("current_stage_status?: string | null;"));
assert.ok(rfqTranslatorSource.includes("function buildLiveStageHistory("));
assert.ok(rfqTranslatorSource.includes("stageHistory,"));
assert.ok(rfqTranslatorSource.includes("current_stage_order == null"));
assert.ok(rfqConnectorSource.includes("Unsupported live RFQ status filter"));
assert.ok(listScreenSource.includes("return parseDemoStatusFilter(value);"));
assert.ok(demoStatusSource.includes('case "draft":'));
assert.ok(demoStatusSource.includes('case "submitted":'));
assert.ok(demoStatusSource.includes('case "attention_required":'));
assert.ok(!sharedStatusSource.includes('label: "Draft"'));
assert.ok(!sharedStatusSource.includes('label: "Submitted"'));
assert.ok(!sharedStatusSource.includes('label: "Partial / Warning"'));
assert.ok(listHookSource.includes("? demoStatusOptions"));

const liveStatusSections = [
  ...listHookSource.matchAll(/:\s*\[\s*\{ label: "All", value: "all" }[\s\S]*?\]/g),
];
const liveStatusSection = liveStatusSections.at(-1)?.[0] ?? "";
assert.ok(liveStatusSection.includes('label: "In Preparation"'));
assert.ok(liveStatusSection.includes('label: "Awarded"'));
assert.ok(liveStatusSection.includes('label: "Lost"'));
assert.ok(liveStatusSection.includes('label: "Cancelled"'));
assert.ok(!liveStatusSection.includes('label: "Draft"'));
assert.ok(!liveStatusSection.includes('label: "Under Review"'));
assert.ok(!liveStatusSection.includes('label: "Submitted"'));
assert.ok(listScreenSource.includes('case "in_preparation":'));
assert.ok(listScreenSource.includes('case "awarded":'));
assert.ok(listScreenSource.includes('case "lost":'));
assert.ok(listScreenSource.includes('case "cancelled":'));
assert.ok(!listScreenSource.includes('case "draft":\n      return value;\n    }\n  }\n\n  switch (value) {'));

assert.ok(dashboardSource.includes("Awaiting truthful source data."));
assert.ok(
  overviewScreenSource.includes(
    "You see assigned RFQs only. Stage truth, reminders, and portfolio controls remain manager-owned.",
  ),
);
assert.ok(overviewHookSource.includes('trendLabel: "Scoped by ownership"'));
assert.ok(
  roleCapabilitiesSource.includes(
    "Assigned RFQs with contributor-only lifecycle and intelligence access.",
  ),
);
assert.ok(!roleCapabilitiesSource.includes("own-created drafts"));
assert.ok(!roleCapabilitiesSource.includes('"rfq.draft.update"'));
assert.ok(!rolePermissionsSource.includes("canEditDraftRfq"));
assert.ok(!rfqAccessSource.includes("isOwnCreatedDraft"));
assert.ok(!rfqAccessSource.includes("canEditDraftRfq"));
assert.ok(!workspaceSource.includes("Draft-phase access is active."));
