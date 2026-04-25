import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const backendSource = await readFile(
  path.join(process.cwd(), "..", "rfq_manager_ms", "scripts", "bootstrap_base_data.py"),
  "utf8",
);
const stageSource = await readFile(
  path.join(process.cwd(), "src", "demo", "manager", "stages.ts"),
  "utf8",
);
const workflowSource = await readFile(
  path.join(process.cwd(), "src", "demo", "manager", "workflows.ts"),
  "utf8",
);

function extractPythonWorkflowBlock(name) {
  const blockRegex = new RegExp(`${name} = \\{([\\s\\S]*?)\\n\\}`, "m");
  const match = backendSource.match(blockRegex);
  assert.ok(match, `Expected backend workflow block ${name}.`);
  return match[1];
}

function extractPythonStages(block) {
  return [...block.matchAll(
    /\{"name": "([^"]+)", "order": (\d+), "default_team": "[^"]+", "planned_duration_days": (\d+), "mandatory_fields": [^,]+, "is_required": (True|False)\}/g,
  )].map(([, label, order, plannedDurationDays, isRequired]) => ({
    label,
    order: Number(order),
    plannedDurationDays: Number(plannedDurationDays),
    isRequired: isRequired === "True",
  }));
}

function extractTsStageBlock(name) {
  const blockRegex = new RegExp(`export const ${name}: ManagerStageTemplateResponse\\[] = \\[([\\s\\S]*?)\\n\\];`, "m");
  const match = stageSource.match(blockRegex);
  assert.ok(match, `Expected UI stage block ${name}.`);
  return match[1];
}

function extractTsStages(block) {
  return [...block.matchAll(
    /\{[\s\S]*?label: "([^"]+)",[\s\S]*?order: (\d+),[\s\S]*?plannedDurationDays: (\d+),[\s\S]*?\n\s*\},?/g,
  )].map(([entry, label, order, plannedDurationDays]) => ({
    label,
    order: Number(order),
    plannedDurationDays: Number(plannedDurationDays),
    isRequired: entry.includes("isRequired: true"),
  }));
}

function assertWorkflowDescription(code, description, selectionMode) {
  assert.ok(
    workflowSource.includes(`code: "${code}"`),
    `Expected demo workflow catalog to include ${code}.`,
  );
  assert.ok(
    workflowSource.includes(description),
    `Expected demo workflow catalog to use backend description for ${code}.`,
  );
  assert.ok(
    workflowSource.includes(`selectionMode: "${selectionMode}"`),
    `Expected demo workflow catalog to keep ${code} selection mode ${selectionMode}.`,
  );
}

const backendLongStages = extractPythonStages(extractPythonWorkflowBlock("GHI_LONG"));
const backendShortStages = extractPythonStages(extractPythonWorkflowBlock("GHI_SHORT"));
const uiLongStages = extractTsStages(extractTsStageBlock("ghiLongWorkflowStages"));
const uiShortStages = extractTsStages(extractTsStageBlock("ghiShortWorkflowStages"));

assert.deepEqual(uiLongStages, backendLongStages);
assert.deepEqual(uiShortStages, backendShortStages);

assertWorkflowDescription(
  "GHI-LONG",
  "Full lifecycle for complex, engineered RFQs with design, BOQ/BOM and vendor inquiries.",
  "fixed",
);
assertWorkflowDescription(
  "GHI-SHORT",
  "Simplified path for repeat orders, standard items or small-value RFQs.",
  "fixed",
);
assertWorkflowDescription(
  "GHI-CUSTOM",
  "Customizable lifecycle that reuses the full GHI long workflow catalog at RFQ creation time.",
  "customizable",
);

assert.ok(
  workflowSource.includes("function buildWorkflowResponse("),
  "Expected demo workflow catalog to compute turnaround days from stage definitions.",
);
assert.ok(
  !workflowSource.includes("turnaroundDays: 19"),
  "Expected demo workflow catalog to stop hardcoding stale long-workflow turnaround days.",
);
assert.ok(
  !workflowSource.includes("turnaroundDays: 11"),
  "Expected demo workflow catalog to stop hardcoding stale short-workflow turnaround days.",
);
