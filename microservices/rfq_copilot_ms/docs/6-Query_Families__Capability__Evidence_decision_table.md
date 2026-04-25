| Query family | Core meaning | Target shape | Natural context | Required context to resolve | Allowed answer / evidence path | Default assistant behavior | If it cannot proceed normally |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **1. Conversational** | The user is talking to the assistant, not really querying business data yet | No target | Both general and RFQ | Pure conversation context | **No retrieval**; assistant persona + response rules only | Respond briefly, naturally, in product tone | If it drifts outside product/domain scope, treat as **out of scope** |
| **2. Domain knowledge** | The user wants explanation of a domain concept, not one RFQ record | A concept | Both general and RFQ | Domain context only; no RFQ required unless user makes it RFQ-specific | **Domain-knowledge path only**; not manager truth, not intelligence truth | Explain the concept clearly and stay inside industrial / RFQ domain | If outside bounded domain vocabulary, treat as **out of scope** or clarify if ambiguous |
| **3. Portfolio retrieval** | The user wants visibility across many RFQs: search, filter, summarize, surface groups | Many RFQs / portfolio slice | Primarily general, still possible in RFQ | General context or explicit broad ask | **Manager truth** for operational portfolio search / listing | Search across RFQs, narrow, summarize, present sets or candidates | If target/filter is vague, **clarify**; if unsupported request type, say **unsupported** |
| **4. RFQ-specific retrieval** | The user wants information about one identifiable RFQ | One RFQ | Primarily RFQ, still possible in general | Either current RFQ default context, or explicit RFQ identification | **Manager truth** for operational state; **intelligence truth** for derived RFQ artifacts | Answer about one RFQ in a focused way | If RFQ is unclear, **clarify**; if missing/inaccessible, say so; if no grounded data, say **not enough evidence** |
| **5. Cross-RFQ reference** | The user temporarily overrides the current/default RFQ and points to another RFQ | Another RFQ relative to current/active one | Most meaningful in RFQ, still possible in general | Existing active context plus explicit other RFQ reference | Same as RFQ-specific: **manager** and/or **intelligence** depending on ask | Handle inline without changing conversation ownership | If other RFQ is missing or inaccessible, say that clearly and stop there |
| **6. Comparison** | The user wants contrast between two or more targets | Two+ RFQs or RFQ vs group | Both general and RFQ | Multiple targets must be resolved clearly | **Manager and/or intelligence** as needed, but only on grounded comparable fields | Put targets side by side and make the contrast explicit | If one target is missing/inaccessible, say so; if comparison cannot be grounded, say **not enough evidence** |
| **7. Clarification response** | The user is resolving ambiguity from the previous assistant turn, not starting a fresh ask | Inherits prior unresolved target | Both general and RFQ | Must be interpreted against the immediately prior clarification | **Inherited path** from the original pending query; no independent path by default | Resolve ambiguity, then continue the original answer path | If still ambiguous after the reply, ask one more precise clarification only if needed; otherwise fall into the relevant protected case |
| **8. Non-answerable request** | The ask cannot safely proceed as a normal answer | Any / unresolved / invalid | Both general and RFQ | Must be evaluated before normal answering | **No normal answer path yet**; first classify into protected subcase | Do not fake-help; route into the right protected behavior | Split into: **unsupported**, **out of scope**, **ambiguous**, **missing/inaccessible target**, **not enough evidence** |

**Protected subcases for Family 8**

| Protected subcase | Meaning | Assistant behavior |
| --- | --- | --- |
| **Unsupported** | Valid platform-domain ask, but feature/capability is not available yet | Brief, honest, no pretending |
| **Out of scope** | Ask is outside RFQ / platform / industrial domain | Brief refusal + redirect |
| **Ambiguous / needs clarification** | Ask may be valid, but meaning or target is still unclear | Ask one clear clarification, then stop |
| **Missing / inaccessible target** | Explicit RFQ does not exist or user cannot access it | Say that clearly in one sentence and stop |
| **Not enough evidence** | Ask is in scope, but grounded data is insufficient | State what is known, state what is missing, do not invent |

**Comparison: Comparable Field Policy v1**

**Group A — Operational comparison fields**

Operational comparison is grounded in rfq_manager_ms. These fields are always eligible to be checked for comparison when every target RFQ exists and is accessible; if a field is nullable or absent for one target, the assistant must mark it as missing rather than infer it.

Default comparison fields:

- RFQ identity: id, rfq_code, name
- Client/context: client, country, industry, description
- Lifecycle: status, progress, outcome_reason
- Workflow/current stage: workflow_id, workflow_name, current_stage_id, current_stage_name, current_stage_order, current_stage_status
- Timing: deadline, created_at, updated_at
- Ownership: owner
- Priority: priority
- Blocker state: current_stage_blocker_status, current_stage_blocker_reason_code
- Source readiness markers: source_package_available, source_package_updated_at, workbook_available, workbook_updated_at

Extended operational comparison fields:

- Full stage plan and timing from /rfqs/{rfq_id}/stages
- Stage detail, notes, files, and subtasks from /rfqs/{rfq_id}/stages/{stage_id}
- Reminder state from /reminders?rfq_id=...
- Workflow structure from /workflows/{workflow_id}
- Portfolio stats and analytics from /rfqs/stats and /rfqs/analytics, only for portfolio-level comparison

Caution:
captured_data is semi-structured and should only be compared key-by-key when the requested key is present for all compared RFQs. Margin and estimation accuracy analytics currently return null and must not be treated as available business truth.

Excluded:
leadership notes, summaryLine, nextAction, tags, procurementLead, demo values, intelligenceState, profitability, win probability, supplier risk, risk score, readiness score, and similar-project benchmark are not Group A fields.

---

**Group B — Conditional intelligence comparison fields**

Intelligence comparison is grounded in rfq_intelligence_ms. These fields are not always comparable. They are comparable only when every target RFQ has the required current artifact and the requested field is present with grounded content.

Primary public intelligence read surfaces:

- /intelligence/v1/rfqs/{rfq_id}/artifacts
- /intelligence/v1/rfqs/{rfq_id}/snapshot
- /intelligence/v1/rfqs/{rfq_id}/briefing
- /intelligence/v1/rfqs/{rfq_id}/workbook-profile
- /intelligence/v1/rfqs/{rfq_id}/workbook-review

Conditionally comparable fields:

- Artifact health: artifact_type, version, status, is_current, schema_version, created_at, updated_at, source_event_type, source_event_id
- Snapshot: availability_matrix, intake_panel_summary, briefing_panel_summary, workbook_panel, review_panel, outcome_summary, requires_human_review, overall_status
- Briefing: executive_summary, what_is_known, what_is_missing, compliance_flags_or_placeholders, risk_notes_or_placeholders, section_availability, cold_start_limitations, recommended_next_actions, review_posture, package_readiness
- Workbook profile: workbook_source, template_name, parser_version, template_match, template_recognition, workbook_structure, detected_identifiers, workbook_profile.rfq_identity, identity_mirrors, general_item_rows, general_summary, bid_meta, pairing_validation, downstream_readiness, parser_report_status
- Workbook review: summary, structural_completeness_findings, workbook_internal_consistency_findings, intake_vs_workbook_findings, benchmark_outlier_findings, finding_id, family, severity, title, description, evidence, confidence, status

Comparison rule:
If both RFQs have the same artifact and the same field exists, compare it.
If one RFQ is missing the artifact, say the intelligence comparison is not fully grounded for that area.
If a field is null, placeholder, cold-start, or marked unavailable, report that limitation instead of inferring.
If parser failure exists, compare parser status/failure truthfully but do not invent workbook intelligence.

Excluded from Group B v1:
direct rfq_intake_profile content, direct cost_breakdown_profile content, direct parser_report content, direct rfq_analytical_record content, full MR/package parser envelope, full BOM/RVL/compliance extraction, historical similarity, benchmark engine, semantic document understanding, readiness score, risk score, cost-per-ton, profitability, margin intelligence, and final “which RFQ is better” recommendations.

---

#### C. Not comparable unless explicitly supported later

These should not be inferred by the LLM:

- “Which RFQ is better?”
- “Which one is more profitable?”
- “Which one should we prioritize?” unless priority rules/data exist
- win probability
- margin trend
- cost-per-ton if tonnage or cost is missing
- readiness judgment if readiness artifact is missing
- risk score if no risk artifact exists

The assistant can still help, but it must phrase the limitation clearly.