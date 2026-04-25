These are not architecture proposals yet. They are the conception gaps we need to resolve before architecture becomes clean.

### 1. Exact definition of `last_activity`

Freshness is frozen, but the exact update trigger is still open.

We need to decide whether `last_activity` changes on:

- user message only
- assistant response
- tool retrieval
- conversation title rename
- manual reopen
- failed request

My recommendation later will be: user or assistant message should update it; passive viewing should not.

---

### 2. How the system represents temporary RFQ overrides

The behavior is frozen: another RFQ can be targeted inline without changing conversation ownership.

Still open: how to represent this cleanly as state.

We need to avoid two bad extremes:

- changing the whole conversation context every time another RFQ is mentioned
- ignoring explicit RFQ references because the conversation is RFQ-bound

The future architecture must likely distinguish:

- conversation owner context
- current page default RFQ
- current turn target RFQ(s)
- unresolved/clarification target

---

### 3. Multi-intent user messages

The query families are frozen, but real users may combine intents.

Example:

> “Compare this RFQ with IF-0041 and tell me which one is more risky.”
> 

This contains:

- comparison
- RFQ-bound default reference
- explicit other RFQ
- risk judgment, which may be unsupported unless a risk artifact exists

We need rules for splitting one user ask into allowed and forbidden parts.

---

### 4. Domain knowledge source

The “domain knowledge path” is frozen, but the actual source is still open.

Possible future choices:

- curated glossary
- internal knowledge base
- static domain prompt
- retrieval over approved GHI/industrial documents
- hybrid approach

Important: it must not become a generic internet chatbot.

---

### 5. Response evidence/provenance format

The conception says answers must be grounded, but the final user-facing format is still open.

We need to decide how visible the grounding should be:

- silent grounding only
- “Based on current RFQ data…”
- compact evidence notes
- source badges
- internal trace only

For product quality, I would avoid ugly API-like citations in the chat, but keep strong internal traceability.

---

### 6. Comparison output style

Comparable fields are frozen, but the presentation style is not.

Still open:

- table vs narrative
- default comparison sections
- how many fields before the answer becomes too heavy
- how to present “missing vs unavailable vs not supported”
- how to answer when comparison is partially grounded

This matters a lot for UX.

---

### 7. Permission model integration detail

The rule is frozen: inaccessible RFQs must not leak data.

Still open:

- whether access is checked before retrieval only
- whether every tool response must include access verification
- whether the chatbot relies on manager service filtering or performs explicit access checks too

For safety, architecture should not rely only on the LLM or UI state.

---

### 8. Clarification memory

Clarification response is frozen as a query family.

Still open:

- how long a pending clarification remains valid
- whether only the immediate previous turn counts
- what happens if the user answers after several unrelated messages
- how pending clarification state is cleared

The document says clarification should be interpreted against the immediately prior clarification, so I would treat that as the strict default