"""Context Builder — Stage 8 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Context Builder row) and
§12.1 (prompt-injection delimiters — deferred to Slice 5+ when LLM
Compose lands).

Slice 1 / Batch 5 implements the Path 4 deterministic-renderer path:
the context is the per-target labelled evidence packets the Tool
Executor already produced. The Path 4 renderer reads these directly.

For Slice 5+ (when LLM Compose ships), this stage will:

* Wrap untrusted retrieved data in ``<<<UNTRUSTED_RFQ_DATA>>>`` /
  ``<<<END_UNTRUSTED_RFQ_DATA>>>`` delimiters per §12.1.
* Apply per-target labels (``[IF-0001]`` etc.) outside the delimiter.
* Filter to ``plan.canonical_requested_fields`` only (already done in
  Tool Executor for Slice 1; will be re-checked here defensively when
  the LLM-Compose path enables free-form synthesis).

For Slice 1, this stage is a structural pass-through: it confirms the
packets exist, performs a defensive field-whitelist re-filter (so a
future tool that returns extra fields doesn't leak them), and that's
it.
"""

from __future__ import annotations

from src.models.execution_state import EvidencePacket, ExecutionState


# Special synthetic keys the Tool Executor produces for stage-list /
# blocker intents — always allowed through the whitelist filter.
_SYNTHETIC_PACKET_KEYS = {"stages", "active_blocker"}


def build_path_4(state: ExecutionState) -> None:
    """Defensive whitelist re-filter on the evidence packets.

    Mutates ``state.evidence_packets`` in place: each packet's
    ``fields`` dict is filtered to only keys in
    ``plan.canonical_requested_fields ∪ _SYNTHETIC_PACKET_KEYS ∪ plan.allowed_fields``.

    Forbidden fields and unsupported fields never appear here — but
    we re-check defensively. Better to drop a field the Tool Executor
    accidentally surfaced than to leak it to the renderer.
    """
    allowed_keys = (
        set(state.plan.canonical_requested_fields)
        | set(state.plan.allowed_fields)
        | _SYNTHETIC_PACKET_KEYS
    )
    forbidden_keys = set(state.plan.forbidden_fields)

    filtered_packets: list[EvidencePacket] = []
    for packet in state.evidence_packets:
        clean_fields = {
            k: v
            for k, v in packet.fields.items()
            if k in allowed_keys and k not in forbidden_keys
        }
        # EvidencePacket is frozen — replace with a new packet carrying
        # the filtered fields.
        filtered_packets.append(
            EvidencePacket(
                target_id=packet.target_id,
                target_label=packet.target_label,
                fields=clean_fields,
                source_refs=list(packet.source_refs),
            )
        )
    # Replace in-place so the renderer reads the cleaned set.
    state.evidence_packets.clear()
    state.evidence_packets.extend(filtered_packets)
