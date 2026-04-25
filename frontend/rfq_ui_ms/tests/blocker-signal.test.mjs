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
    `data:text/javascript;base64,${Buffer.from(transpiled).toString("base64")}`,
  );
}

const blockerSignalModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "blocker-signal.ts"),
);
const cardSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQCard.tsx"),
  "utf8",
);
const tableSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQTable.tsx"),
  "utf8",
);

assert.equal(
  blockerSignalModule.formatBlockerReasonLabel("waiting_client_input"),
  "Waiting Client Input",
);

assert.deepEqual(
  blockerSignalModule.getRfqBlockedSignal({
    blockerReasonCode: "waiting_client_input",
    blockerStatus: "Blocked",
    stageHistory: [],
    stageLabel: "Pre-bid clarifications",
  }),
  {
    isBlocked: true,
    reasonLabel: "Waiting Client Input",
    stageLabel: "Pre-bid clarifications",
  },
);

assert.deepEqual(
  blockerSignalModule.getRfqBlockedSignal({
    blockerReasonCode: undefined,
    blockerStatus: undefined,
    stageHistory: [
      {
        blockerReasonCode: "awaiting_procurement_docs",
        label: "Client Clarifications",
        state: "blocked",
      },
    ],
    stageLabel: "Client Clarifications",
  }),
  {
    isBlocked: true,
    reasonLabel: "Awaiting Procurement Docs",
    stageLabel: "Client Clarifications",
  },
);

assert.deepEqual(
  blockerSignalModule.getRfqBlockedSignal({
    blockerReasonCode: undefined,
    blockerStatus: undefined,
    stageHistory: [],
    stageLabel: "RFQ received",
  }),
  {
    isBlocked: false,
  },
);

assert.ok(cardSource.includes("getRfqBlockedSignal(rfq)"));
assert.ok(cardSource.includes("<Badge variant=\"rose\">Blocked</Badge>"));
assert.ok(tableSource.includes("getRfqBlockedSignal(item)"));
assert.ok(tableSource.includes("<Badge variant=\"rose\">Blocked</Badge>"));
