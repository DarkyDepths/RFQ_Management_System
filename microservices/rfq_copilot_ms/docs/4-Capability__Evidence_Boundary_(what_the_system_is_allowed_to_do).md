This is the clean version:

### 1. Conversational answers

These are things like greetings, thanks, short help, identity, and simple conversational continuity.

They do **not** need manager or intelligence evidence.

They come from assistant persona and response rules only.

But they still must stay within product tone and not drift into irrelevant long answers.

### 2. RFQ operational truth

These are live RFQ facts such as status, deadline, owner, stage, blockers, reminders, and portfolio search results.

These must come from **`rfq_manager_ms`**.

The copilot can explain them, but it must not invent or infer them.

This fits the manager service’s role as the lifecycle and tracking backbone of the platform.

### 3. RFQ derived intelligence

These are briefing-like or intelligence-like outputs such as gaps, readiness, review flags, and similar derived artifacts.

These must come from **`rfq_intelligence_ms`**.

The copilot can surface and explain them, but it should not generate its own fake briefing or readiness judgment.

### 4. Domain knowledge

These are domain-specific questions not tied to one RFQ, like PWHT, RT, ASME, fabrication concepts, and industrial estimation language.

These do not come from live RFQ truth.

They come from the domain-knowledge path only, and that path must stay tightly bounded to GHI/RFQ/industrial domain vocabulary so the assistant does not become a generic internet chatbot.

### 5. Not answerable as normal content

These are cases where the copilot should **not** behave like a normal “just answer” assistant.

This bucket splits into:

### 5.1 Unsupported

The ask belongs to the platform domain, but the capability is not available yet.

Response style:

brief, honest, no pretending.

### 5.2 Out of scope

The ask is outside RFQ/platform/industrial scope.

Response style:

brief refusal + redirect.

### 5.3 Ambiguous / needs clarification

The ask may be valid, but the assistant cannot know what the user means yet.

Response style:

ask **one** clear clarification, then stop.

### 5.4 Missing / inaccessible target

The user explicitly asks about an RFQ that either does not exist or is not accessible to their role.

Response style:

say that clearly in one sentence and stop there.

This is already part of the platform experience you froze.

### 5.5 Not enough evidence

The question is in scope, but the assistant does not currently have grounded data to answer safely.

Response style:

state only what is known, say what is missing, do not invent.

That matches the “surface honestly” philosophy you want.

## The simple rule behind everything

Before the copilot answers any query, it should silently decide:

1. **What kind of thing is this?**
2. **Am I allowed to answer it normally?**
3. **If yes, what evidence source is valid?**
4. **If no, is this unsupported, out of scope, ambiguous, missing/inaccessible, or lacking evidence?**