import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const executiveInsightsSource = await readFile(
  path.join(process.cwd(), "src", "lib", "executive-insights.ts"),
  "utf8",
);
const dashboardHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-dashboard-data.ts"),
  "utf8",
);
const executiveDetailSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "ExecutiveStrategicDetail.tsx"),
  "utf8",
);
const blockerSignalSource = await readFile(
  path.join(process.cwd(), "src", "utils", "blocker-signal.ts"),
  "utf8",
);

assert.ok(executiveInsightsSource.includes("formatBlockerReasonLabel"));
assert.ok(executiveInsightsSource.includes("getTerminalRfqOutcome"));
assert.ok(executiveInsightsSource.includes("getRfqStatusLabel"));
assert.ok(!executiveInsightsSource.includes("function toTitleCase("));
assert.ok(executiveInsightsSource.includes('getTerminalRfqOutcome(rfq.status) !== "lost"'));
assert.ok(executiveInsightsSource.includes("return getRfqStatusLabel(terminalOutcome);"));
assert.ok(dashboardHookSource.includes("getLossReasonLabel"));
assert.ok(dashboardHookSource.includes("getLossReasonLabel(rfq) !== null"));
assert.ok(executiveDetailSource.includes("getRfqBlockedSignal"));
assert.ok(executiveDetailSource.includes("getBlockedStageHeadline"));
assert.ok(executiveDetailSource.includes("blockedSignal.reasonLabel"));
assert.ok(executiveDetailSource.includes('label: getRfqStatusLabel("lost")'));
assert.ok(blockerSignalSource.includes("export function getBlockedStageHeadline"));
assert.ok(dashboardHookSource.includes("getBlockedStageHeadline"));
