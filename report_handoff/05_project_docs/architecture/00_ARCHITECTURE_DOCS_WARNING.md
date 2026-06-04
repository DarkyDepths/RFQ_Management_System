# Architecture Documents Warning

The files in this folder are important design references, but they may not all reflect the latest implementation state.

Some architecture documents were written before the latest development batches, code changes, validation audits, and supervisor feedback. Therefore, they must not be treated as the final source of truth for implementation status.

## How to use these documents

Use these documents to understand:

- original design intent;
- architectural vocabulary;
- service boundaries;
- trust-boundary concepts;
- RFQ lifecycle vision;
- rationale behind major decisions.

Do not use them blindly to claim that something is implemented.

## Source-of-truth rule

When architecture documents and implementation evidence disagree, use this order:

1. Current repository code and tests.
2. Latest implementation audit.
3. Latest validation evidence report.
4. Current v0 report text.
5. Architecture documents in this folder.
6. Older microservice-specific documentation.

## Required behavior

If a document describes a capability that is not found in code or validation evidence, classify it as:

- documented only;
- architecturally specified;
- deferred/future;
- or not found / unclear.

Do not upgrade it to “implemented” unless the code or validation audit proves it.

## Examples

- If an architecture document says the copilot can consume intelligence artifacts, but the implementation audit says the copilot-intelligence connector is not wired, then the report must say: architecturally specified / future integration.
- If an architecture document says event-driven manager-to-intelligence flow exists, but the implementation audit says only manual/direct trigger flows are implemented, then the report must say: event-driven flow is future hardening.
- If an architecture document describes full IAM/SSO, but the implementation audit shows only backend auth shims and frontend role selection, then the report must say: dedicated IAM is future scope.
- If an architecture document describes long-term episodic memory, but the implementation audit shows only working-memory capture and no prompt injection, then the report must say: episodic memory is future scope.

## Goal

These documents should help reconstruct the design story, not override current implementation truth.