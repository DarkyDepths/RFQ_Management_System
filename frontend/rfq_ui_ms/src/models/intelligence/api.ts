export type IntelligenceApiArtifactStatus =
  | "pending"
  | "partial"
  | "complete"
  | "failed";

export type IntelligenceApiArtifactType =
  | "rfq_intake_profile"
  | "intelligence_briefing"
  | "workbook_profile"
  | "cost_breakdown_profile"
  | "parser_report"
  | "workbook_review_report"
  | "rfq_intelligence_snapshot"
  | "rfq_analytical_record";

export interface IntelligenceArtifactEnvelope<TContent = Record<string, unknown>> {
  id: string;
  rfq_id: string;
  artifact_type: IntelligenceApiArtifactType;
  version: number;
  status: IntelligenceApiArtifactStatus;
  is_current: boolean;
  content: TContent | null;
  source_event_type?: string | null;
  source_event_id?: string | null;
  schema_version: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface IntelligenceArtifactSummaryResponse {
  id: string;
  rfq_id: string;
  artifact_type: IntelligenceApiArtifactType;
  version: number;
  status: IntelligenceApiArtifactStatus;
  is_current: boolean;
  schema_version: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface IntelligenceArtifactIndexResponse {
  artifacts: IntelligenceArtifactSummaryResponse[];
}

export interface IntelligenceArtifactMeta {
  artifact_type?: string;
  slice?: string;
  generated_at?: string;
  source_event_id?: string;
  source_event_type?: string;
  parser_version?: string;
}

export interface IntelligenceSnapshotContent {
  artifact_meta?: IntelligenceArtifactMeta;
  rfq_summary?: {
    rfq_id?: string;
    rfq_code?: string | null;
    project_title?: string | null;
    client_name?: string | null;
  };
  availability_matrix?: Record<string, string>;
  intake_panel_summary?: {
    status?: string | null;
    source_reference?: string | null;
    quality_status?: string | null;
    key_gaps?: string[] | null;
  };
  briefing_panel_summary?: {
    status?: string | null;
    executive_summary?: string | null;
    missing_info?: string[] | null;
  };
  workbook_panel?: {
    status?: string | null;
    reason?: string | null;
    template_recognition?: Record<string, unknown> | null;
    pairing_validation?: Record<string, unknown> | null;
    parser_status?: string | null;
    parser_failure?: {
      code?: string | null;
      message?: string | null;
    } | null;
  };
  review_panel?: {
    status?: string | null;
    reason?: string | null;
    active_findings_count?: number | null;
  };
  analytical_status_summary?: {
    status?: string | null;
    historical_readiness?: boolean | null;
    notes?: string[] | null;
  };
  outcome_summary?: {
    status?: string | null;
    outcome?: string | null;
    reason?: string | null;
    learning_loop_status?: string | null;
  };
  consumer_hints?: {
    ui_recommended_tabs?: string[] | null;
    chatbot_suggested_questions?: string[] | null;
  };
  requires_human_review?: boolean | null;
  overall_status?: string | null;
}

export interface IntelligenceBriefingContent {
  artifact_meta?: IntelligenceArtifactMeta;
  executive_summary?: string | null;
  what_is_known?: {
    rfq_id?: string;
    rfq_code?: string | null;
    project_title?: string | null;
    client_name?: string | null;
    source_package_reference?: string | null;
    mr_number?: string | null;
    material_description?: string | null;
    tag_numbers?: string[] | null;
    design_codes?: string[] | null;
    vendor_count?: number | null;
    standards_count?: Record<string, number> | null;
    known_points?: string[] | null;
  };
  what_is_missing?: string[] | null;
  compliance_flags_or_placeholders?: {
    status?: string | null;
    scope_boundary?: string | null;
    review_flags?: string[] | null;
  } | null;
  risk_notes_or_placeholders?: {
    status?: string | null;
    notes?: string[] | null;
  } | null;
  section_availability?: Record<string, string> | null;
  cold_start_limitations?: string[] | null;
  recommended_next_actions?: string[] | null;
  review_posture?: string | null;
  package_readiness?: {
    parser_report_status?: string | null;
    briefing_ready?: boolean | null;
    requires_human_review?: boolean | null;
  } | null;
}

export interface IntelligenceWorkbookProfileContent {
  artifact_meta?: IntelligenceArtifactMeta;
  workbook_source?: {
    workbook_ref?: string | null;
    workbook_filename?: string | null;
    uploaded_at?: string | null;
    file_extension?: string | null;
    local_workbook_path?: string | null;
  };
  template_name?: string | null;
  parser_version?: string | null;
  template_match?: string | null;
  template_recognition?: Record<string, unknown> | null;
  workbook_structure?: {
    sheet_names?: string[] | null;
    expected_sheet_count?: number | null;
    sheet_count_found?: number | null;
    missing_sheets?: string[] | null;
    extra_sheets?: string[] | null;
  } | null;
  canonical_estimate_profile?: {
    detected_identifiers?: {
      rfq_code?: string | null;
      project_title?: string | null;
      client_name?: string | null;
      inquiry_no?: string | null;
    } | null;
  } | null;
  workbook_profile?: Record<string, unknown> | null;
  pairing_validation?: {
    pairing_status?: string | null;
    notes?: string | null;
    external_linkage_required?: boolean | null;
  } | null;
  downstream_readiness?: {
    review_report_ready?: boolean | null;
    benchmark_ready?: boolean | null;
    similarity_ready?: boolean | null;
    requires_human_review?: boolean | null;
  } | null;
  parser_report_status?: string | null;
}

export interface IntelligenceWorkbookReviewFinding {
  finding_id?: string;
  family?: string | null;
  severity?: "low" | "medium" | "high" | null;
  title?: string | null;
  description?: string | null;
  review_posture?: string | null;
  evidence?: Record<string, unknown> | null;
  confidence?: string | null;
  status?: string | null;
  suppression_reason?: string | null;
}

export interface IntelligenceWorkbookReviewContent {
  artifact_meta?: IntelligenceArtifactMeta;
  summary?: {
    review_posture?: string | null;
    active_findings_count?: number | null;
    unavailable_families?: string[] | null;
  } | null;
  structural_completeness_findings?: IntelligenceWorkbookReviewFinding[] | null;
  workbook_internal_consistency_findings?: IntelligenceWorkbookReviewFinding[] | null;
  intake_vs_workbook_findings?: IntelligenceWorkbookReviewFinding[] | null;
  benchmark_outlier_findings?: IntelligenceWorkbookReviewFinding[] | null;
}

export interface IntelligenceReprocessResponse {
  status?: string;
  message?: string;
}
