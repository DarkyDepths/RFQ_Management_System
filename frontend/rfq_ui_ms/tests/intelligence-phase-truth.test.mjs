import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const apiRfqModelSource = await readFile(
  path.join(process.cwd(), "src", "models", "manager", "api-rfq.ts"),
  "utf8",
);
const rfqModelSource = await readFile(
  path.join(process.cwd(), "src", "models", "manager", "rfq.ts"),
  "utf8",
);
const rfqTranslatorSource = await readFile(
  path.join(process.cwd(), "src", "translators", "manager", "rfqs.ts"),
  "utf8",
);
const actionsPanelSource = await readFile(
  path.join(process.cwd(), "src", "components", "intelligence", "IntelligenceActionsPanel.tsx"),
  "utf8",
);
const intelligencePanelSource = await readFile(
  path.join(process.cwd(), "src", "components", "intelligence", "IntelligencePanel.tsx"),
  "utf8",
);

assert.ok(apiRfqModelSource.includes("source_package_available: boolean;"));
assert.ok(apiRfqModelSource.includes("workbook_available: boolean;"));
assert.ok(rfqModelSource.includes("sourcePackageAvailable: boolean;"));
assert.ok(rfqModelSource.includes("workbookAvailable: boolean;"));
assert.ok(rfqTranslatorSource.includes("const sourcePackageUpload = resolveMilestoneUpload(item.uploads, \"zip\");"));
assert.ok(rfqTranslatorSource.includes("const workbookUpload = resolveMilestoneUpload(item.uploads, \"workbook\");"));
assert.ok(rfqTranslatorSource.includes("sourcePackageAvailable ="));
assert.ok(rfqTranslatorSource.includes("workbookAvailable ="));
assert.ok(actionsPanelSource.includes("Package Intelligence"));
assert.ok(actionsPanelSource.includes("Workbook Enrichment"));
assert.ok(actionsPanelSource.includes("Historical Insights"));
assert.ok(actionsPanelSource.includes("Waiting for RFQ package upload"));
assert.ok(actionsPanelSource.includes("Waiting for workbook upload"));
assert.ok(actionsPanelSource.includes("Historical insights unlock only after enough completed RFQs and retained workbooks exist."));
assert.ok(actionsPanelSource.includes("Support Actions"));
assert.ok(actionsPanelSource.includes("Refresh Outcome Enrichment"));
assert.ok(!actionsPanelSource.includes("processed. rfq intake profile"));
assert.ok(!actionsPanelSource.includes("Trigger Intake"));
assert.ok(!actionsPanelSource.includes("Trigger Workbook"));
assert.ok(intelligencePanelSource.includes("Initial Package Intelligence Ready"));
assert.ok(intelligencePanelSource.includes("Workbook Comparison Ready"));
assert.ok(intelligencePanelSource.includes("Historical Maturity Not Reached Yet"));
assert.ok(intelligencePanelSource.includes("Needs Human Review"));
assert.ok(intelligencePanelSource.includes("Recommended Next Step"));
assert.ok(intelligencePanelSource.includes("What Needs Review"));
assert.ok(intelligencePanelSource.includes("What Will Unlock This Phase"));
assert.ok(intelligencePanelSource.includes("An initial package summary is available from the client RFQ package."));
assert.ok(intelligencePanelSource.includes("Workbook comparison is available, but it still needs human review"));
assert.ok(!intelligencePanelSource.includes("rfq_intake_profile"));
assert.ok(!intelligencePanelSource.includes("rfq_analytical_record"));
assert.ok(!intelligencePanelSource.includes("rfq_intelligence_snapshot"));
assert.ok(!intelligencePanelSource.includes("Upload workbook to unlock workbook_profile"));
assert.ok(!intelligencePanelSource.includes("review_report slices"));
assert.ok(!intelligencePanelSource.includes("scenario://"));
