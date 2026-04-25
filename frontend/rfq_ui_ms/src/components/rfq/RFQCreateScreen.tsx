"use client";

import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { ClipboardPlus, Sparkles } from "lucide-react";

import { SkeletonCard } from "@/components/common/SkeletonCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiConfig } from "@/config/api";
import {
  DEFAULT_INDUSTRY_OPTION,
  OTHER_INDUSTRY_OPTION,
  industryOptions,
  resolveIndustryValue,
  type IndustryOption,
} from "@/config/industry-options";
import { createRfq } from "@/connectors/manager/rfqs";
import { listWorkflows } from "@/connectors/manager/workflows";
import { getPermissions } from "@/config/role-permissions";
import { useRole } from "@/context/role-context";
import { getRoleActorProfile } from "@/lib/manager-actor";
import type { WorkflowModel } from "@/models/manager/workflow";
import {
  addDaysToLocalDate,
  buildWorkflowDeadlineTooNarrowMessage,
  formatWorkflowDeadlineIso,
  getLocalDateIsoString,
  getMinimumWorkflowFeasibleDeadlineIso,
} from "@/utils/workflow-deadline";
import {
  buildSelectedWorkflow,
  buildSkipStageIds,
  getInitialSelectedWorkflowStageIds,
  isCustomizableWorkflow,
} from "@/utils/workflow-selection";

const priorities = ["normal", "critical"] as const;
const selectClassName =
  "flex h-11 w-full rounded-xl border border-input bg-card px-3 py-2 text-sm text-foreground ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-transparent disabled:cursor-not-allowed disabled:opacity-50";

function normalizeText(value: string) {
  return value.trim();
}

function FieldLabel({
  htmlFor,
  isOptional = false,
  required = false,
  children,
}: {
  htmlFor?: string;
  isOptional?: boolean;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <Label htmlFor={htmlFor}>
        {children}
        {required ? <span className="ml-1 text-rose-500">*</span> : null}
      </Label>
      {isOptional ? (
        <span className="text-[0.68rem] font-medium uppercase tracking-[0.16em] text-muted-foreground">
          Optional
        </span>
      ) : null}
    </div>
  );
}

export function RFQCreateScreen() {
  const { role } = useRole();
  const permissions = getPermissions(role);
  const actorProfile = getRoleActorProfile(role);
  const router = useRouter();
  const todayIso = getLocalDateIsoString();
  const [loading, setLoading] = useState(true);
  const [workflows, setWorkflows] = useState<WorkflowModel[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState("");
  const [selectedStageIds, setSelectedStageIds] = useState<string[]>([]);
  const [title, setTitle] = useState("Structured Power Redundancy Upgrade");
  const [client, setClient] = useState("GHI Strategic Systems");
  const [owner, setOwner] = useState(actorProfile.userName);
  const [valueSar, setValueSar] = useState("12400000");
  const [dueDate, setDueDate] = useState(() => addDaysToLocalDate(new Date(), 14));
  const [priority, setPriority] = useState<(typeof priorities)[number]>("critical");
  const [description, setDescription] = useState(
    "High-value package requiring synchronized operational control and intelligence visibility from intake onward.",
  );
  const [selectedIndustryOption, setSelectedIndustryOption] =
    useState<IndustryOption>(DEFAULT_INDUSTRY_OPTION);
  const [customIndustry, setCustomIndustry] = useState("");
  const [country, setCountry] = useState("Saudi Arabia");
  const [errorMessage, setErrorMessage] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setOwner(actorProfile.userName);
  }, [actorProfile.userName]);

  useEffect(() => {
    if (!permissions.canCreateRfq) {
      setLoading(false);
      setWorkflows([]);
      setSelectedWorkflowId("");
      return;
    }

    let active = true;

    async function load() {
      try {
        const workflowOptions = await listWorkflows();

        if (!active) {
          return;
        }

        setWorkflows(workflowOptions);
        setSelectedWorkflowId(workflowOptions[0]?.id ?? "");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [permissions.canCreateRfq]);

  const selectedWorkflow = workflows.find(
    (workflow) => workflow.id === selectedWorkflowId,
  );
  const selectedWorkflowForCreate = buildSelectedWorkflow(
    selectedWorkflow,
    selectedStageIds,
  );
  const selectedWorkflowStages = selectedWorkflowForCreate?.stages ?? [];
  const selectedWorkflowIsCustomizable = isCustomizableWorkflow(selectedWorkflow);
  const minimumFeasibleDueDateIso =
    getMinimumWorkflowFeasibleDeadlineIso(selectedWorkflowForCreate);
  const dueDateTooNarrow =
    minimumFeasibleDueDateIso !== null && dueDate < minimumFeasibleDueDateIso;

  useEffect(() => {
    setSelectedStageIds(getInitialSelectedWorkflowStageIds(selectedWorkflow));
  }, [selectedWorkflow]);

  const handleWorkflowStageToggle = (stageId: string) => {
    if (!selectedWorkflow || !selectedWorkflowIsCustomizable) {
      return;
    }

    const stage = selectedWorkflow.stages.find((candidate) => candidate.id === stageId);
    if (!stage || stage.isRequired) {
      return;
    }

    setSelectedStageIds((current) => {
      const next = new Set(current);
      if (next.has(stageId)) {
        next.delete(stageId);
      } else {
        next.add(stageId);
      }

      return selectedWorkflow.stages
        .filter((candidate) => next.has(candidate.id))
        .map((candidate) => candidate.id);
    });
  };

  const handleSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedTitle = normalizeText(title);
    const normalizedClient = normalizeText(client);
    const normalizedOwner = normalizeText(owner);
    const normalizedDescription = normalizeText(description);
    const normalizedIndustry = normalizeText(
      resolveIndustryValue(selectedIndustryOption, customIndustry),
    );
    const normalizedCountry = normalizeText(country);

    if (!permissions.canCreateRfq) {
      return;
    }

    setErrorMessage("");

    if (
      !normalizedTitle ||
      !normalizedClient ||
      !normalizedOwner ||
      !normalizedIndustry ||
      !normalizedCountry ||
      !dueDate ||
      !selectedWorkflow
    ) {
      setErrorMessage(
        "Complete all required fields before creating the RFQ: title, client, owner, industry, country, due date, and workflow.",
      );
      return;
    }

    if (!selectedWorkflowForCreate || selectedWorkflowForCreate.stages.length === 0) {
      setErrorMessage(
        "Select at least one workflow stage before creating this RFQ.",
      );
      return;
    }

    if (dueDate < todayIso) {
      setErrorMessage("Due date cannot be in the past.");
      return;
    }

    if (minimumFeasibleDueDateIso && dueDate < minimumFeasibleDueDateIso) {
      setErrorMessage(
        buildWorkflowDeadlineTooNarrowMessage(minimumFeasibleDueDateIso),
      );
      return;
    }

    setSaving(true);

    try {
      const result = await createRfq({
        client: normalizedClient,
        country: normalizedCountry,
        deadline: dueDate,
        description: normalizedDescription || undefined,
        industry: normalizedIndustry,
        name: normalizedTitle,
        owner: normalizedOwner,
        priority,
        skipStageIds: buildSkipStageIds(selectedWorkflow, selectedStageIds),
        workflowId: selectedWorkflow.id,
      });

      router.push(`/rfqs/${result.id}?created=1`);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "RFQ creation failed.",
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SkeletonCard className="h-[620px]" lines={10} />
        <SkeletonCard className="h-[620px]" lines={10} />
      </div>
    );
  }

  return (
    <div className="grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
      <form className="surface-panel p-8" onSubmit={handleSave}>
        <div className="section-kicker">
          <ClipboardPlus className="h-3.5 w-3.5" />
          Create RFQ
        </div>
        <h1 className="mt-4 text-display text-3xl font-semibold text-foreground lg:text-4xl">
          Create a new RFQ
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          This creates a live RFQ immediately, sets it to In preparation, and auto-generates the workflow stages from the selected manager workflow.
        </p>
        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
          Required fields are marked with <span className="text-rose-500">*</span>
        </p>

        <AnimatePresence>
          {errorMessage ? (
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4"
              exit={{ opacity: 0, y: -10 }}
              initial={{ opacity: 0, y: 10 }}
            >
              <div className="text-sm font-medium text-rose-600 dark:text-rose-300">
                {errorMessage}
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>

        {!permissions.canCreateRfq ? (
          <div className="mt-6 rounded-2xl border border-gold-500/25 bg-gold-500/10 p-4 text-sm leading-relaxed text-gold-700 dark:text-gold-200">
            Your role does not have permission to create RFQs. Switch to an operational role.
          </div>
        ) : null}

        <div className="mt-8 grid gap-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-title" required>
                RFQ Title
              </FieldLabel>
              <Input
                id="rfq-title"
                onChange={(event) => setTitle(event.target.value)}
                required
                value={title}
              />
            </div>
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-client" required>
                Client
              </FieldLabel>
              <Input
                id="rfq-client"
                onChange={(event) => setClient(event.target.value)}
                required
                value={client}
              />
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-owner" required>
                Owner
              </FieldLabel>
              <Input
                id="rfq-owner"
                onChange={(event) => setOwner(event.target.value)}
                required
                value={owner}
              />
            </div>
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-due-date" required>
                Due Date
              </FieldLabel>
              <Input
                id="rfq-due-date"
                min={minimumFeasibleDueDateIso ?? todayIso}
                onChange={(event) => {
                  setErrorMessage("");
                  setDueDate(event.target.value);
                }}
                required
                type="date"
                value={dueDate}
              />
              {minimumFeasibleDueDateIso ? (
                <p
                  className={`text-xs ${
                    dueDateTooNarrow ? "text-rose-600 dark:text-rose-300" : "text-muted-foreground"
                  }`}
                >
                  {dueDateTooNarrow
                    ? buildWorkflowDeadlineTooNarrowMessage(minimumFeasibleDueDateIso)
                    : `Selected workflow requires ${formatWorkflowDeadlineIso(minimumFeasibleDueDateIso)} or later.`}
                </p>
              ) : null}
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-industry" required>
                Industry
              </FieldLabel>
              <select
                className={selectClassName}
                id="rfq-industry"
                onChange={(event) => {
                  setErrorMessage("");
                  setSelectedIndustryOption(event.target.value as IndustryOption);
                }}
                required
                value={selectedIndustryOption}
              >
                {industryOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-country" required>
                Country
              </FieldLabel>
              <Input
                id="rfq-country"
                onChange={(event) => setCountry(event.target.value)}
                required
                value={country}
              />
            </div>
          </div>

          {selectedIndustryOption === OTHER_INDUSTRY_OPTION ? (
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-custom-industry" required>
                Custom Industry
              </FieldLabel>
              <Input
                id="rfq-custom-industry"
                onChange={(event) => {
                  setErrorMessage("");
                  setCustomIndustry(event.target.value);
                }}
                placeholder="Enter the industry"
                required
                value={customIndustry}
              />
            </div>
          ) : null}

          {apiConfig.useMockData ? (
            <div className="space-y-2">
              <FieldLabel htmlFor="rfq-value">
                Demo Estimated Value (SAR)
              </FieldLabel>
              <Input
                id="rfq-value"
                onChange={(event) => setValueSar(event.target.value)}
                type="number"
                value={valueSar}
              />
            </div>
          ) : null}

          <div className="space-y-2">
            <FieldLabel required>Priority Level</FieldLabel>
            <div className="flex flex-wrap gap-2">
              {priorities.map((option) => (
                <Button
                  key={option}
                  className="capitalize"
                  onClick={() => setPriority(option)}
                  type="button"
                  variant={priority === option ? "default" : "secondary"}
                >
                  {option}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <FieldLabel htmlFor="rfq-summary" isOptional>
              Description
            </FieldLabel>
            <Textarea
              id="rfq-summary"
              className="h-24 resize-none"
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-3 border-t border-border pt-6">
          <Button disabled={saving || !permissions.canCreateRfq} size="lg" type="submit">
            {saving ? "Creating RFQ..." : "Create RFQ"}
          </Button>
        </div>
      </form>

      <div className="space-y-6">
        <div className="surface-panel p-6">
          <div className="section-kicker">
            <Sparkles className="h-3.5 w-3.5" />
            Workflow configuration
          </div>
          <h2 className="mt-3 text-xl font-semibold text-foreground">
            Select workflow <span className="text-rose-500">*</span>
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            The selected workflow is required and determines the stages generated immediately after create.
          </p>
          <div className="mt-5 space-y-3">
            {workflows.map((workflow) => (
              <button
                key={workflow.id}
                className={`w-full rounded-2xl border p-4 text-left transition-all ${
                  workflow.id === selectedWorkflowId
                    ? "border-primary/40 bg-primary/5"
                    : "border-border bg-card hover:bg-muted/40 dark:bg-white/[0.01] dark:hover:bg-white/[0.04]"
                }`}
                onClick={() => {
                  setErrorMessage("");
                  setSelectedWorkflowId(workflow.id);
                }}
                type="button"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-foreground">
                      {workflow.name}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {workflow.description ?? "Manager workflow definition."}
                    </div>
                  </div>
                  <div className="rounded-full border border-border bg-muted/40 px-2 py-0.5 font-mono text-[0.65rem] text-muted-foreground dark:bg-white/[0.04]">
                    {workflow.turnaroundDays ? `${workflow.turnaroundDays}d • ` : ""}
                    {workflow.stageCount}s
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-[0.65rem] uppercase tracking-[0.18em] text-muted-foreground">
                  <span className="rounded-full border border-border bg-muted/40 px-2 py-0.5 dark:bg-white/[0.04]">
                    {(workflow.selectionMode ?? "fixed") === "customizable"
                      ? "Customizable"
                      : "Fixed"}
                  </span>
                  {workflow.code ? (
                    <span className="rounded-full border border-border bg-muted/40 px-2 py-0.5 dark:bg-white/[0.04]">
                      {workflow.code}
                    </span>
                  ) : null}
                </div>
                {workflow.recommendedUse || workflow.code ? (
                  <div className="mt-3 text-xs text-muted-foreground">
                    <span className="font-medium text-foreground">
                      {workflow.recommendedUse ? "Use case" : "Code"}
                    </span>
                    : {workflow.recommendedUse ?? workflow.code}
                  </div>
                ) : null}
              </button>
            ))}
          </div>

          {selectedWorkflow && selectedWorkflowIsCustomizable ? (
            <div className="mt-6 rounded-2xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <h3 className="text-sm font-semibold text-foreground">
                Choose workflow stages
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                GHI customized workflow starts from the long workflow catalog. Required stages stay locked; optional stages are included only when selected.
              </p>
              <div className="mt-4 space-y-3">
                {selectedWorkflow.stages.map((stage) => {
                  const checked = selectedStageIds.includes(stage.id);
                  return (
                    <label
                      key={stage.id}
                      className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-3 transition-colors ${
                        checked
                          ? "border-primary/30 bg-primary/5"
                          : "border-border bg-card hover:bg-muted/40 dark:bg-white/[0.01] dark:hover:bg-white/[0.04]"
                      } ${stage.isRequired ? "cursor-not-allowed" : ""}`}
                    >
                      <input
                        checked={checked}
                        className="mt-1 h-4 w-4 rounded border-border"
                        disabled={stage.isRequired}
                        onChange={() => {
                          setErrorMessage("");
                          handleWorkflowStageToggle(stage.id);
                        }}
                        type="checkbox"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-medium text-foreground">
                            {stage.label}
                          </span>
                          {stage.isRequired ? (
                            <span className="rounded-full border border-gold-500/30 bg-gold-500/10 px-2 py-0.5 text-[0.62rem] font-medium uppercase tracking-[0.18em] text-gold-700 dark:text-gold-200">
                              Required
                            </span>
                          ) : null}
                        </div>
                        {stage.summary ? (
                          <div className="mt-1 text-xs text-muted-foreground">
                            {stage.summary}
                          </div>
                        ) : null}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>

        <div className="surface-panel p-6">
          <h3 className="text-base font-semibold text-foreground">
            Stage preview
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            The workflow dictates lifecycle visibility and operational progression through the manager service.
          </p>
          {selectedWorkflowIsCustomizable ? (
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              Preview shows only the stages that will be instantiated for this RFQ.
            </p>
          ) : null}
          <div className="mt-5 space-y-3 border-l border-border pl-4">
            {selectedWorkflowStages.map((stage) => (
              <div key={stage.id} className="relative">
                <div className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-border" />
                <div className="flex items-center justify-between gap-2">
                  <div className="text-sm font-medium text-foreground">{stage.label}</div>
                  <div className="text-[0.65rem] uppercase tracking-[0.18em] text-muted-foreground">
                    {stage.assignedTeam ?? stage.ownerRole ?? "Unassigned"}
                  </div>
                </div>
                {stage.summary ? (
                  <div className="mt-0.5 text-xs text-muted-foreground">{stage.summary}</div>
                ) : null}
              </div>
            ))}
            {selectedWorkflow && selectedWorkflowStages.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                Select at least one stage to generate a customized workflow.
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
