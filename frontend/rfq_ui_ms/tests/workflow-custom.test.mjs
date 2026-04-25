import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { readFile } from "node:fs/promises";
import path from "node:path";

import ts from "../node_modules/typescript/lib/typescript.js";

async function importTsModule(modulePath) {
  const source = await readFile(modulePath, "utf8");
  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ES2020,
      target: ts.ScriptTarget.ES2020,
    },
    fileName: path.basename(modulePath),
  }).outputText;

  return import(
    `data:text/javascript;base64,${Buffer.from(transpiled).toString("base64")}`
  );
}

const helperModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "workflow-selection.ts"),
);
const createScreenSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQCreateScreen.tsx"),
  "utf8",
);
const demoWorkflowSource = await readFile(
  path.join(process.cwd(), "src", "demo", "manager", "workflows.ts"),
  "utf8",
);
const rfqTranslatorSource = await readFile(
  path.join(process.cwd(), "src", "translators", "manager", "rfqs.ts"),
  "utf8",
);

const customWorkflow = {
  id: "workflow-ghi-custom",
  name: "GHI customized workflow",
  selectionMode: "customizable",
  stageCount: 4,
  stages: [
    { id: "rfq", label: "RFQ received", isRequired: true },
    { id: "go", label: "Go / No-Go", isRequired: true },
    { id: "design", label: "Preliminary design", isRequired: false },
    { id: "award", label: "Award / Lost", isRequired: true },
  ],
};

const fixedWorkflow = {
  id: "workflow-ghi-short",
  name: "GHI short workflow",
  selectionMode: "fixed",
  stageCount: 2,
  stages: [
    { id: "rfq", label: "RFQ received", isRequired: true },
    { id: "award", label: "Award / Lost", isRequired: true },
  ],
};

assert.equal(helperModule.isCustomizableWorkflow(customWorkflow), true);
assert.equal(helperModule.isCustomizableWorkflow(fixedWorkflow), false);
assert.deepEqual(
  helperModule.getInitialSelectedWorkflowStageIds(customWorkflow),
  ["rfq", "go", "award"],
);
assert.deepEqual(
  helperModule.getInitialSelectedWorkflowStageIds(fixedWorkflow),
  ["rfq", "award"],
);
assert.deepEqual(
  helperModule.buildSkipStageIds(customWorkflow, ["rfq", "go", "award"]),
  ["design"],
);
assert.deepEqual(
  helperModule.buildSkipStageIds(fixedWorkflow, ["rfq"]),
  [],
);
assert.deepEqual(
  helperModule.buildSelectedWorkflow(customWorkflow, ["rfq", "go", "award"]).stages.map(
    (stage) => stage.id,
  ),
  ["rfq", "go", "award"],
);

assert.ok(createScreenSource.includes("Choose workflow stages"));
assert.ok(createScreenSource.includes("Required stages stay locked"));
assert.ok(createScreenSource.includes("Select at least one workflow stage before creating this RFQ."));
assert.ok(createScreenSource.includes("Preview shows only the stages that will be instantiated for this RFQ."));
assert.ok(createScreenSource.includes("skipStageIds: buildSkipStageIds"));

assert.ok(demoWorkflowSource.includes("GHI-CUSTOM"));
assert.ok(demoWorkflowSource.includes("GHI-SHORT"));
assert.ok(demoWorkflowSource.includes("GHI-LONG"));
assert.ok(rfqTranslatorSource.includes("calculateLifecycleProgress"));
assert.ok(rfqTranslatorSource.includes('item.status === "awarded"'));
assert.ok(rfqTranslatorSource.includes('stage.state === "completed"'));
assert.ok(!rfqTranslatorSource.includes("activeStage.order / item.stageHistory.length"));
