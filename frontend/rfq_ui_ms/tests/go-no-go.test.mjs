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
  path.join(process.cwd(), "src", "utils", "go-no-go.ts"),
);
const workspaceSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RfqOperationalWorkspace.tsx"),
  "utf8",
);

assert.deepEqual(helperModule.GO_NO_GO_OPTIONS, [
  { label: "Go", value: "go" },
  { label: "No-Go", value: "no_go" },
]);

assert.equal(helperModule.normalizeGoNoGoDecisionValue("Go"), "go");
assert.equal(helperModule.normalizeGoNoGoDecisionValue("proceed"), "go");
assert.equal(helperModule.normalizeGoNoGoDecisionValue("No-Go"), "no_go");
assert.equal(helperModule.normalizeGoNoGoDecisionValue("no go"), "no_go");

assert.equal(
  helperModule.getGoNoGoValidationMessage(["go_nogo_decision"]),
  "Please choose Go or No-Go before continuing.",
);
assert.equal(helperModule.getGoNoGoValidationMessage(["final_price"]), null);

assert.equal((workspaceSource.match(/window\.prompt\(/g) ?? []).length, 0);
assert.equal((workspaceSource.match(/window\.confirm\(/g) ?? []).length, 0);
assert.ok(workspaceSource.includes("Confirm No-Go decision"));
assert.ok(
  workspaceSource.includes(
    "This will cancel {rfqBusinessIdentity}, preserve its history, and skip the",
  ),
);
assert.ok(workspaceSource.includes("Cancel RFQ"));
assert.ok(workspaceSource.includes("Confirm Cancellation"));
assert.ok(workspaceSource.includes("Cancellation reason"));
assert.ok(workspaceSource.includes("Please enter a cancellation reason."));
assert.ok(workspaceSource.includes('role="dialog"'));
assert.ok(workspaceSource.includes('aria-modal="true"'));
assert.ok(workspaceSource.includes("RFQ cancelled from Go / No-Go. History is preserved."));
assert.equal(workspaceSource.includes("confirmNoGoCancel: true"), false);
