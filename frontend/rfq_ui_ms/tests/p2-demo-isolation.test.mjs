import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const sharedStatusSource = await readFile(
  path.join(process.cwd(), "src", "utils", "status.ts"),
  "utf8",
);
const demoStatusSource = await readFile(
  path.join(process.cwd(), "src", "demo", "manager", "status.ts"),
  "utf8",
);
const displayStatusSource = await readFile(
  path.join(process.cwd(), "src", "lib", "rfq-status-display.ts"),
  "utf8",
);
const overviewHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-overview-data.ts"),
  "utf8",
);
const connectorSource = await readFile(
  path.join(process.cwd(), "src", "connectors", "manager", "rfqs.ts"),
  "utf8",
);
const translatorSource = await readFile(
  path.join(process.cwd(), "src", "translators", "manager", "rfqs.ts"),
  "utf8",
);

assert.ok(sharedStatusSource.includes("export const liveRfqStatusMeta"));
assert.ok(sharedStatusSource.includes("export function isLiveActiveRfqStatus"));
assert.ok(!sharedStatusSource.includes("demoOnlyRfqStatusMeta"));
assert.ok(!sharedStatusSource.includes("attention_required"));

assert.ok(demoStatusSource.includes("export const demoOnlyRfqStatusMeta"));
assert.ok(demoStatusSource.includes("export const demoStatusOptions"));
assert.ok(demoStatusSource.includes("export function isDemoActiveRfqStatus"));

assert.ok(displayStatusSource.includes("demoOnlyRfqStatusMeta"));
assert.ok(displayStatusSource.includes("getRfqStatusMeta"));
assert.ok(displayStatusSource.includes("getRfqStatusLabel"));
assert.ok(displayStatusSource.includes("getTerminalRfqOutcome"));

assert.ok(overviewHookSource.includes("isDemoActiveRfqStatus"));
assert.ok(overviewHookSource.includes("isLiveActiveRfqStatus"));
assert.ok(connectorSource.includes("isDemoActiveRfqStatus"));
assert.ok(translatorSource.includes("demoRfqStatusMeta[item.status].label"));
assert.ok(translatorSource.includes("liveRfqStatusMeta[status].label"));
