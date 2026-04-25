Each family should be defined by 5 things:

### 1. User intention

What is the user trying to do?

### 2. Scope of target

Are they asking about:

- no target
- one RFQ
- many RFQs
- another RFQ
- a concept
- a comparison

### 3. Required context

Can this be answered from:

- pure conversation
- general context
- RFQ-bound context
- explicit RFQ reference
- a clarification reply

### 4. Allowed evidence path

Does it require:

- no retrieval
- manager truth
- intelligence truth
- domain knowledge
- or no answer yet

### 5. Failure behavior

If it cannot be answered, what happens:

- clarify
- refuse
- say unsupported
- say inaccessible
- say not enough evidence

### 1. Conversational

It can happen in:

- **general context**
- **RFQ context**

Simple human chat around the product.

This family covers moments where the user is **not really asking for RFQ truth, portfolio retrieval, or domain explanation yet**.

They are interacting with the copilot as an assistant surface.

This includes things like:

- hello
- thanks
- okay
- who are you
- help me

The core meaning of this family is:

**the user is talking to the assistant, not yet querying business data.**

So the assistant should respond briefly, naturally, and with the right product tone.

It should not over-explain, dump context, or turn a simple greeting into a long answer.

---

### 2. Domain knowledge

It can happen in:

- **general context**
- **RFQ context**

Questions about industrial / RFQ-related concepts, not one specific RFQ.

This family covers asks where the user wants **understanding of a concept, term, standard, process, or practice** that belongs to the RFQ / estimation / industrial domain, but is **not tied to one identified RFQ**.

This includes things like:

- what is PWHT
- explain RT
- what does ASME Section VIII mean

The core meaning of this family is:

**the user wants knowledge or explanation about the domain itself, not about one RFQ record.**

So the assistant should treat this as a concept-explanation question, not as an RFQ retrieval question.

---

### 3. Portfolio retrieval

It is:

- **natural / primary in general context**
- **still possible in RFQ context**

Questions about multiple RFQs or cross-platform search.

This family covers asks where the user wants to **search, filter, surface, or summarize across many RFQs**, rather than focus on one single RFQ.

This includes things like:

- show urgent RFQs
- find Aramco projects
- which RFQs are blocked

The core meaning of this family is:

**the user wants visibility across the RFQ portfolio, not details about one specific RFQ.**

So the assistant should think in terms of groups, search, filtering, narrowing, and portfolio-level answers.

---

### 4. RFQ-specific retrieval

It is:

- **natural / primary in RFQ context**
- **still possible in general context**

Questions about one RFQ’s live or derived state.

This family covers asks where the user wants information about **one identifiable RFQ**.

That RFQ may be:

- the current RFQ page default context
- or an explicitly named RFQ

This includes things like:

- what’s the deadline
- who owns this
- any blockers
- what does the briefing say

The core meaning of this family is:

**the user wants information about one RFQ only.**

So the assistant should treat the request as focused, contextual, and tied to a single RFQ target.

---

### 5. Cross-RFQ reference

It is:

- **natural / primary in RFQ context**
- **still possible in general context**

Questions asked in one context but explicitly pointing to another RFQ.

This family covers asks where the user is already in one RFQ context, or already discussing one RFQ, but suddenly points to **another RFQ as a temporary target**.

This includes things like:

- what about IF-0041
- show IF-0041 status

The core meaning of this family is:

**the user is temporarily overriding the current/default RFQ context to ask about another RFQ.**

So the assistant should understand that this is not necessarily a new conversation or a permanent context switch.

It is often just a temporary shift of attention inside the same thread.

---

### 6. Comparison

It can happen in:

- **general context**
- **RFQ context**

Questions comparing two RFQs or two groups.

This family covers asks where the user wants the assistant to **put two or more targets side by side** and help them understand differences, similarities, or relative position.

This includes things like:

- compare this RFQ with IF-0041
- compare open RFQs by priority

The core meaning of this family is:

**the user does not just want retrieval — they want contrast, comparison, or relative understanding.**

So the assistant should not treat this like a simple one-target answer.

It should understand that multiple targets are involved and that the output must make the contrast clear.

---

### 7. Clarification response

It can happen in:

- **general context**
- **RFQ context**
- 

A user reply to a clarification asked by the assistant.

This family covers short or incomplete-looking messages that only make sense **because the assistant asked for clarification in the previous turn**.

This includes things like:

- IF-0041
- the Aramco one
- I mean the latest lost bid

The core meaning of this family is:

**the user is not starting a new ask — they are resolving ambiguity from the previous turn.**

So the assistant should interpret the message in relation to the immediately prior clarification, not as a standalone request.

---

### 8. Non-answerable request

It can happen in:

- **general context**
- **RFQ context**

This is the top family covering cases that later split into:

- unsupported
- out of scope
- ambiguous
- missing/inaccessible target
- not enough evidence

This family covers asks that **cannot proceed as a normal answer**.

The core meaning of this family is:

**the user asked something that the assistant cannot safely answer directly in the normal way.**

That does not always mean the same thing.

Sometimes the request is valid but unsupported.

Sometimes it is unrelated to the platform.

Sometimes it is too ambiguous.

Sometimes the RFQ does not exist or is not accessible.

Sometimes the question is in scope but the assistant still lacks enough grounded evidence.

So this family is the protection family:

it prevents the copilot from pretending that every user message can be answered normally.