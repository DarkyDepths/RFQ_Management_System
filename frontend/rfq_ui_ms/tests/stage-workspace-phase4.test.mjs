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

const capturedDataModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "captured-data.ts"),
);
const decisionModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "go-no-go.ts"),
);
const subtaskModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "subtask.ts"),
);
const commercialFieldModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "commercial-fields.ts"),
);
const terminalOutcomeModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "terminal-outcome.ts"),
);
const formatModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "format.ts"),
);
const estimatedSubmissionModule = await importTsModule(
  path.join(process.cwd(), "src", "utils", "estimated-submission.ts"),
);
const workspaceSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RfqOperationalWorkspace.tsx"),
  "utf8",
);
const timelineSource = await readFile(
  path.join(process.cwd(), "src", "components", "rfq", "RFQStageTimeline.tsx"),
  "utf8",
);
const workspaceHookSource = await readFile(
  path.join(process.cwd(), "src", "hooks", "use-stage-workspace.ts"),
  "utf8",
);

const hydratedEntries = capturedDataModule.buildCapturedFieldEntries(
  {
    clarification_topic: "client material confirmation",
  },
  ["go_nogo_decision"],
);

assert.deepEqual(hydratedEntries, [
  { id: "captured:go_nogo_decision", key: "go_nogo_decision", value: "" },
  {
    id: "captured:clarification_topic",
    key: "clarification_topic",
    value: "client material confirmation",
  },
]);
assert.deepEqual(
  capturedDataModule.buildCapturedData(hydratedEntries),
  {
    go_nogo_decision: "",
    clarification_topic: "client material confirmation",
  },
);
assert.deepEqual(
  capturedDataModule.buildCapturedFieldState(
    {
      clarification_topic: "client material confirmation",
    },
    ["go_nogo_decision"],
  ),
  {
    entries: [
      {
        id: "captured:go_nogo_decision",
        key: "go_nogo_decision",
        value: "",
      },
      {
        id: "captured:clarification_topic",
        key: "clarification_topic",
        value: "client material confirmation",
      },
    ],
    showAdditionalSection: true,
  },
);
assert.deepEqual(
  capturedDataModule.buildCapturedFieldState(
    {
      estimation_completed: "true",
      estimation_amount: "125000",
      estimation_currency: "SAR",
    },
    ["estimation_completed"],
  ),
  {
    entries: [
      {
        id: "captured:estimation_completed",
        key: "estimation_completed",
        value: "true",
      },
      {
        id: "captured:estimation_amount",
        key: "estimation_amount",
        value: "125000",
      },
      {
        id: "captured:estimation_currency",
        key: "estimation_currency",
        value: "SAR",
      },
    ],
    showAdditionalSection: false,
  },
);
const newDraftEntry = capturedDataModule.createEmptyCapturedFieldEntry();
assert.equal(newDraftEntry.key, "");
assert.equal(newDraftEntry.value, "");
assert.equal(newDraftEntry.id.startsWith("draft:"), true);

assert.equal(
  decisionModule.normalizeControlledStageDecisionValue(
    "design_approved",
    true,
  ),
  "yes",
);
assert.equal(
  decisionModule.normalizeControlledStageDecisionValue(
    "boq_completed",
    "No",
  ),
  "no",
);
assert.equal(
  decisionModule.getControlledStageDecisionValidationMessage([
    "design_approved",
  ]),
  decisionModule.DESIGN_APPROVED_VALIDATION_MESSAGE,
);
assert.equal(
  decisionModule.getControlledStageDecisionValidationMessage([
    "boq_completed",
  ]),
  decisionModule.BOQ_COMPLETED_VALIDATION_MESSAGE,
);
assert.equal(
  decisionModule.isNegativeAutoBlockingDecision("design_approved", "no"),
  true,
);
assert.equal(
  decisionModule.isNegativeAutoBlockingDecision("boq_completed", "yes"),
  false,
);
assert.deepEqual(
  decisionModule.getControlledStageDecisionOptions("design_approved"),
  decisionModule.YES_NO_OPTIONS,
);

assert.deepEqual(
  subtaskModule.normalizeSubtaskDraftState({
    progress: "0",
    status: "Done",
  }),
  {
    progress: "0",
    status: "Open",
  },
);
assert.deepEqual(
  subtaskModule.normalizeSubtaskDraftState({
    progress: "30",
    status: "Open",
  }),
  {
    progress: "30",
    status: "In progress",
  },
);
assert.deepEqual(
  subtaskModule.normalizeSubtaskDraftState({
    progress: "100",
    status: "Open",
  }),
  {
    progress: "100",
    status: "Done",
  },
);
assert.deepEqual(
  subtaskModule.normalizeSubtaskDraftState({
    progress: "60",
    status: "Done",
  }),
  {
    progress: "60",
    status: "In progress",
  },
);
assert.equal(
  subtaskModule.getSubtaskCreateValidationMessage(
    "",
    "Estimator A",
    "2026-04-15",
    "2026-04-10",
    "2026-04-20",
  ),
  subtaskModule.SUBTASK_NAME_REQUIRED_MESSAGE,
);
assert.equal(
  subtaskModule.getSubtaskCreateValidationMessage(
    "Clarify scope",
    "",
    "2026-04-15",
    "2026-04-10",
    "2026-04-20",
  ),
  subtaskModule.SUBTASK_ASSIGNEE_REQUIRED_MESSAGE,
);
assert.equal(
  subtaskModule.getSubtaskCreateValidationMessage(
    "Clarify scope",
    "Estimator A",
    "",
    "2026-04-10",
    "2026-04-20",
  ),
  subtaskModule.SUBTASK_DUE_DATE_REQUIRED_MESSAGE,
);
assert.equal(
  subtaskModule.getSubtaskDueDateValidationMessage(
    "2026-04-09",
    "2026-04-10",
    "2026-04-20",
  ),
  subtaskModule.SUBTASK_DUE_DATE_WINDOW_MESSAGE,
);
assert.equal(
  subtaskModule.getSubtaskProgressValidationMessage("40", 60),
  subtaskModule.SUBTASK_PROGRESS_DECREASE_MESSAGE,
);
assert.deepEqual(
  subtaskModule.resolveSubtaskStageWindow(
    "2026-04-10",
    "2026-04-20",
  ),
  {
    startValue: "2026-04-10",
    endValue: "2026-04-20",
    mode: "planned",
  },
);
assert.deepEqual(
  subtaskModule.resolveSubtaskStageWindow(
    "2026-04-10",
    "2026-04-20",
    "2026-04-15",
  ),
  {
    startValue: "2026-04-15",
    endValue: "2026-04-25",
    mode: "shifted_actual",
  },
);
assert.deepEqual(
  subtaskModule.resolveSubtaskStageWindow(
    "2026-04-10",
    "2026-04-20",
    "2026-04-15",
    "2026-04-22",
  ),
  {
    startValue: "2026-04-15",
    endValue: "2026-04-22",
    mode: "actual",
  },
);

assert.equal(
  commercialFieldModule.getCommercialFieldAmountValue(
    {
      estimation_amount: "125000",
    },
    commercialFieldModule.ESTIMATION_COMPLETED_FIELD_KEY,
  ),
  "125000",
);
assert.equal(
  commercialFieldModule.getCommercialFieldCurrencyValue(
    {},
    commercialFieldModule.ESTIMATION_COMPLETED_FIELD_KEY,
  ),
  commercialFieldModule.DEFAULT_CURRENCY_CODE,
);
assert.equal(
  commercialFieldModule.getCommercialFieldNumericValidationError(
    {
      estimation_amount: "abc",
    },
    commercialFieldModule.ESTIMATION_COMPLETED_FIELD_KEY,
  ),
  commercialFieldModule.ESTIMATION_AMOUNT_VALIDATION_MESSAGE,
);
assert.equal(
  commercialFieldModule.getCommercialFieldNumericValidationError(
    {
      final_price: "971150",
    },
    commercialFieldModule.FINAL_PRICE_FIELD_KEY,
  ),
  null,
);
assert.equal(
  commercialFieldModule.getApprovalSignatureLabel(),
  "Approval Reference",
);
assert.equal(
  commercialFieldModule.getApprovalSignatureHelpText(),
  "Enter the internal approval sign-off or reference code used to record commercial approval, for example APP-4481.",
);
assert.deepEqual(
  commercialFieldModule.CURRENCY_OPTIONS[0],
  {
    code: "SAR",
    label: "Saudi Riyal",
  },
);
assert.equal(
  terminalOutcomeModule.normalizeTerminalOutcomeValue("Award"),
  terminalOutcomeModule.TERMINAL_OUTCOME_AWARDED,
);
assert.equal(
  terminalOutcomeModule.normalizeLostReasonCode("Commercial competitiveness"),
  "commercial_gap",
);
assert.equal(
  terminalOutcomeModule.normalizeLostReasonCode("Other"),
  terminalOutcomeModule.LOST_REASON_OTHER_VALUE,
);
assert.equal(
  terminalOutcomeModule.getTerminalOutcomeLabel("lost"),
  "Lost",
);
assert.equal(
  terminalOutcomeModule.getLostReasonLabel("technical_gap"),
  "Technical non-compliance",
);
assert.equal(
  terminalOutcomeModule.getTerminalOutcomeHelpText(),
  "Record the final business outcome here before closing the workflow stage.",
);
assert.equal(
  terminalOutcomeModule.getLostReasonHelpText(),
  "A lost RFQ must keep a clear reason for the final business outcome. Choose Other when the listed reasons do not fit.",
);
assert.equal(
  formatModule.formatCommercialAmount("250654.98"),
  "250,654.980",
);
assert.equal(
  formatModule.formatCommercialAmountWithCurrency("500000000", "SAR"),
  "SAR 500,000,000.000",
);
assert.equal(
  estimatedSubmissionModule.resolveEstimatedSubmissionDateValue(
    [
      {
        name: "Offer submission",
        planned_end: "2026-04-24",
        actual_start: "2026-04-25",
        actual_end: "2026-04-26",
      },
    ],
    "2026-05-01",
  ),
  "2026-04-26",
);
assert.equal(
  estimatedSubmissionModule.resolveEstimatedSubmissionDateValue(
    [
      {
        name: "Offer submission",
        planned_end: "2026-04-24",
      },
    ],
    "2026-05-01",
  ),
  "2026-04-24",
);
assert.equal(
  estimatedSubmissionModule.resolveEstimatedSubmissionDateValue(
    [],
    "2026-05-01",
  ),
  "2026-05-01",
);

assert.ok(workspaceSource.includes("Stage note detail"));
assert.ok(workspaceSource.includes("Read more"));
assert.ok(workspaceSource.includes("Operational note"));
assert.ok(workspaceSource.includes("Additional Stage Details"));
assert.ok(workspaceSource.includes("Detail name"));
assert.ok(workspaceSource.includes("Detail value"));
assert.ok(workspaceSource.includes("Add Additional Detail"));
assert.ok(workspaceSource.includes("Add Another Detail"));
assert.ok(
  workspaceSource.includes(
    "instead of asking for manual stage progress updates.",
  ),
);
assert.ok(!workspaceSource.includes("Stage progress is read-only here."));
assert.ok(!workspaceSource.includes('id="stage-progress"'));
assert.ok(workspaceSource.includes("getControlledStageDecisionPlaceholder"));
assert.ok(workspaceSource.includes("This stage is blocked because"));
assert.ok(workspaceSource.includes("Choosing No automatically opens blocker handling for this stage."));
assert.ok(workspaceSource.includes("Terminal Outcome"));
assert.ok(workspaceSource.includes("Choose Awarded or Lost"));
assert.ok(workspaceSource.includes("Choose why the RFQ was lost"));
assert.ok(workspaceSource.includes("Finalize Outcome"));
assert.ok(workspaceSource.includes("RFQ marked as Awarded. History is preserved."));
assert.ok(workspaceSource.includes("RFQ marked as Lost. History is preserved."));
assert.ok(workspaceSource.includes("Lost Reason Detail"));
assert.ok(workspaceSource.includes("Cancel RFQ"));
assert.ok(workspaceSource.includes("Confirm Cancellation"));
assert.ok(workspaceSource.includes("remaining workflow stages as skipped rather than completed"));
assert.ok(workspaceSource.includes("Please enter a cancellation reason."));
assert.ok(workspaceSource.includes("Advance to next stage?"));
assert.ok(workspaceSource.includes("You are moving this RFQ from"));
assert.ok(workspaceSource.includes("Keep Editing"));
assert.ok(workspaceSource.includes("Terminal RFQs are read-only through standard lifecycle controls."));
assert.ok(workspaceSource.includes("Outcome reason stays visible here"));
assert.ok(!workspaceSource.includes("window.confirm"));
assert.ok(workspaceSource.includes("Due date must stay within the current stage window"));
assert.ok(workspaceSource.includes("Due date must stay within the shifted execution window"));
assert.ok(workspaceSource.includes("Due date must stay within the actual stage window"));
assert.ok(workspaceSource.includes("Lifecycle History"));
assert.ok(workspaceSource.includes("Recent Lifecycle Events"));
assert.ok(workspaceSource.includes("View Full Stage Detail"));
assert.ok(workspaceSource.includes("Recorded Activity"));
assert.ok(workspaceSource.includes("No blocker or decision events were recorded for this stage."));
assert.ok(workspaceSource.includes("Read the stored amount as"));
assert.ok(workspaceSource.includes("Stage history detail could not be loaded."));
assert.ok(workspaceSource.includes("Stage-owned history stays read-only here"));
assert.ok(workspaceSource.includes("getHistoryStageBadgeVariant(historyStageWorkspace.state)"));
assert.ok(workspaceSource.includes("key={field.id}"));
assert.ok(workspaceSource.includes("captured-key-${field.id}"));
assert.ok(!workspaceSource.includes('key={`${field.key || "field"}-${field.index}`}'));
assert.ok(workspaceSource.includes("max={stageWindowEndValue}"));
assert.ok(workspaceSource.includes("min={stageWindowStartValue}"));
assert.ok(timelineSource.includes('stage.state === "skipped"'));
assert.ok(timelineSource.includes("CircleSlash"));
assert.ok(
  workspaceHookSource.includes(
    "workspace: current.workspace?.id === stageId ? current.workspace : null",
  ),
);
