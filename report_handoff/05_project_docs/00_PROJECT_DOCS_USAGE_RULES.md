# Project Docs Usage Rules

The files in this folder contain architecture documents, service documents, audit notes, meeting notes, learning notes, and project context.

They are useful, but not all of them are guaranteed to be fully updated with the latest codebase.

## Main rule

Project documents explain intent, vocabulary, rationale, and historical decisions.

They do not automatically prove implementation status.

## Source-of-truth order

When writing or revising the report, use this order:

1. Current repository code and tests.
2. Latest implementation audit.
3. Latest validation evidence report.
4. Current v0 report text.
5. Frozen architecture documents.
6. Microservice-specific documentation.
7. Meeting notes and learning notes.
8. Reference reports for style only.

## How Claude Code should use these docs

Claude Code may use these files to:

- understand the project story;
- understand the BOQ-to-lifecycle-intelligence pivot;
- understand architectural vocabulary;
- understand service boundaries;
- identify useful figures/tables;
- detect stale documentation;
- propose improvements to the report.

Claude Code must not use these files alone to claim:

- a feature is implemented;
- a feature is validated;
- a feature is production-ready;
- a cross-service integration works end-to-end.

## If a document conflicts with code

If a document says something exists but code/audits do not confirm it, classify the claim as one of:

- documented only;
- architecturally specified;
- partial;
- deferred/future;
- not found / unclear.

Then flag the conflict instead of silently rewriting the report.