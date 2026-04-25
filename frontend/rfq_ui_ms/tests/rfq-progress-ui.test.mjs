import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const cardSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQCard.tsx"),
  "utf8",
);
const tableSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQTable.tsx"),
  "utf8",
);
const stageBoxSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "LifecycleProgressStageBox.tsx"),
  "utf8",
);
const progressVisualSource = await readFile(
  path.join(process.cwd(), "src", "utils", "lifecycle-progress-visual.ts"),
  "utf8",
);
const rfqModelSource = await readFile(
  path.join(process.cwd(), "src", "models", "manager", "rfq.ts"),
  "utf8",
);

assert.ok(cardSource.includes("LifecycleProgressStageBox"));
assert.ok(cardSource.includes("Lifecycle"));
assert.ok(cardSource.includes("rfq.rfqProgress"));
assert.ok(!cardSource.includes("rfq.stageProgress"));

assert.ok(tableSource.includes("LifecycleProgressStageBox"));
assert.ok(tableSource.includes("Lifecycle"));
assert.ok(tableSource.includes("item.rfqProgress"));
assert.ok(!tableSource.includes("item.stageProgress"));

assert.ok(stageBoxSource.includes("Current Stage"));
assert.ok(stageBoxSource.includes("Lifecycle"));
assert.ok(stageBoxSource.includes("getLifecycleProgressFillPercent"));
assert.ok(stageBoxSource.includes("blocked"));

assert.ok(progressVisualSource.includes("getLifecycleProgressTone"));
assert.ok(progressVisualSource.includes("getLifecycleProgressFillPercent"));
assert.ok(progressVisualSource.includes("getLifecycleProgressFillClasses"));
assert.ok(progressVisualSource.includes("isTerminalRfqStatus"));

assert.ok(rfqModelSource.includes("rfqProgress: number;"));
assert.ok(!rfqModelSource.includes("stageProgress: number;"));
