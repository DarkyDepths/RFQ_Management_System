export interface EstimatedSubmissionStageLike {
  name: string;
  actual_end?: string | null;
  actual_start?: string | null;
  planned_end?: string | null;
}

const OFFER_SUBMISSION_STAGE_NAME = "offer submission";

function normalizeStageName(name?: string | null) {
  return name?.trim().toLowerCase() ?? "";
}

export function resolveEstimatedSubmissionDateValue(
  stages: EstimatedSubmissionStageLike[],
  fallbackDate?: string | null,
) {
  const submissionStage = stages.find(
    (stage) => normalizeStageName(stage.name) === OFFER_SUBMISSION_STAGE_NAME,
  );

  if (!submissionStage) {
    return fallbackDate ?? undefined;
  }

  return (
    submissionStage.actual_end
    ?? submissionStage.actual_start
    ?? submissionStage.planned_end
    ?? fallbackDate
    ?? undefined
  );
}
