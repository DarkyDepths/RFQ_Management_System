## 1. Context dilution must become a first-class risk

You are right: the danger is not only token limit. The real danger is that the LLM receives too much irrelevant content and loses attention on the real task.

So when we review the architecture, I will check whether it prevents:

- **RAG flooding**: sending RAG context on every turn even when no retrieval is needed.
- **History overload**: injecting the full conversation every time.
- **Tool-result verbosity**: dumping raw API JSON into the prompt.
- **System prompt bloat**: trying to solve behavior with a giant prompt instead of clean orchestration.

The right posture should be:

> The copilot should build a small, precise, turn-specific context packet — not a huge “everything we know” prompt.
> 

So yes, the architecture must include something like a **context translator / context pack builder** whose job is to convert raw backend data into compact, relevant, grounded text for the LLM.

Not raw manager JSON.

Not raw intelligence artifact dumps.

Not all RFQ history.

Only the fields needed for this user’s current question.

---

## 2. LLM-as-judge must be present, but carefully scoped

Yes, the LLM-as-judge layer is important, but it should not become a retry loop that hides failures.

The judge should verify before final output:

- Did the answer claim something not present in evidence?
- Did the answer use the correct evidence source?
- Did it answer outside the allowed capability boundary?
- Did it ignore missing/inaccessible targets?
- Did it make forbidden comparison judgments?
- Did it present unsupported intelligence as truth?

The correct failure behavior is exactly like your screenshot:

> Surface honestly. Do not silently release a fabricated answer. Do not loop forever.
> 

So the judge is not there to make the answer “prettier.”

It is there to enforce **grounding, scope, evidence alignment, and honesty**.

A good architecture should therefore have:

1. **Draft answer generation**
2. **Judge / verification pass**
3. **If pass → return**
4. **If fail → produce safe grounded fallback**
    - “I can confirm X and Y.”
    - “I do not have grounded data for Z.”
    - “That RFQ is inaccessible.”
    - “That comparison is not supported by available artifacts.”

This is crucial for your system because your frozen philosophy says: the LLM understands, but the platform controls what may be claimed.

---

## 3. The judge should not replace deterministic checks

Important nuance: not everything should be judged by the LLM.

Some checks must be deterministic before the LLM even speaks:

- RFQ exists or not
- user has access or not
- conversation is stale or fresh
- query is RFQ-bound or general entry
- comparable field is Group A, B, or C
- tool result exists or missing
- required artifact exists or absent

The LLM judge should validate language and grounding, but the system should still enforce hard rules.

So the architecture needs both:

> deterministic gatekeeping + LLM semantic verification.
> 

If the architecture relies only on a judge prompt, it will still be fragile.

---

## 4. Other hidden challenges we must watch for

Beyond context dilution and judge failure, I will also watch for these when you share the architecture versions.

### A. Tool overcalling

A weak chatbot calls tools for everything.

A strong copilot calls tools only when the query family requires evidence.

Example:

- “hello” → no tool
- “what is PWHT?” → domain path, no RFQ retrieval
- “what’s the deadline?” inside IF-0038 → manager tool
- “what does the briefing say?” → intelligence tool
- “compare this with IF-0041” → target resolution + access checks + comparable field policy

Tool use must be intentional, not automatic.

---

### B. Context ownership vs turn target confusion

This is probably one of the biggest design traps.

The architecture must separate:

- conversation owner context
- page default RFQ
- current user-request target
- temporary cross-RFQ target
- comparison targets
- pending clarification target

If these are mixed, the bot will behave randomly inside RFQ pages.

---

### C. Prompt doing too much

If the architecture says “we’ll put all rules in the system prompt,” that is not enough.

The prompt should guide behavior, but the application layer must enforce:

- permissions
- evidence path
- comparable fields
- stale conversation selection
- tool eligibility
- fallback behavior

The prompt should not be the only safety mechanism.

---

### D. Raw evidence vs answer evidence

The LLM should not receive raw backend payloads by default.

It should receive something like:

```
Evidence packet:
- Source: rfq_manager_ms
- RFQ: IF-0038
- Fields requested: deadline, owner, current_stage, blocker_status
- Verified accessible: true
- Missing fields: none
- Data freshness: current backend read
```

This is much better than dumping full RFQ detail JSON.

---

### E. Partial evidence handling

The copilot must be good when evidence is incomplete.

That means it should not answer only in two modes: “full answer” or “I don’t know.”

It needs a third mode:

> grounded partial answer with explicit gap.
> 

This is especially important for intelligence artifacts, comparison, readiness, risk, and cost-related questions.

---

### F. Evaluation must be part of architecture, not only testing later

For this copilot, we need test cases for:

- routing
- tool selection
- context dilution
- hallucination prevention
- judge failures
- comparison boundaries
- inaccessible RFQ behavior
- stale conversation behavior
- RFQ-bound vs general behavior
- ambiguous follow-up behavior

So when I review the architecture, I will ask:

Does this design make evaluation easy, or impossible?