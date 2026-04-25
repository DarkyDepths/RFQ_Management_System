The copilot uses the LLM to understand and reason, while the platform enforces what it is allowed to know, access, and claim

The LLM decides what the user means.
The system decides what the assistant is allowed to say.

#### Part 1: the LLM

This is the part that **understands language**.
Its job is to understand what the user means, even if the wording is messy.
Example:

- user says: “what about the Aramco one?”
- the LLM understands this is not a greeting
- it understands the user is probably referring to an RFQ
- it understands the request is vague and may need clarification

So the LLM is the **interpreter**.

---

#### Part 2: the system

This is the part that **checks reality and enforces rules**.
Its job is to decide:

- does this RFQ exist?
- does the user have access?
- which service contains the truth?
- is this question in scope?
- do we have enough evidence to answer?

So the system is the **controller of truth**.

[The Platform Experience](https://www.notion.so/The-Platform-Experience-34c2ba2aed65808f85e3f0ae75e7d9b5?pvs=21)

[The Big Scenarios](https://www.notion.so/The-Big-Scenarios-34c2ba2aed658033b1e4da9553eb13c8?pvs=21)

[Capability & Evidence Boundary (what the system is allowed to do)](https://www.notion.so/Capability-Evidence-Boundary-what-the-system-is-allowed-to-do-34c2ba2aed65806eb4abd8fc0d6aa7b1?pvs=21)

[Query Families (what the user is trying to do)](https://www.notion.so/Query-Families-what-the-user-is-trying-to-do-34c2ba2aed65804d9c25f4a7513c888d?pvs=21)

[**Query Families × Capability & Evidence** decision table](https://www.notion.so/Query-Families-Capability-Evidence-decision-table-34c2ba2aed658071a8c6f511e56bd5ed?pvs=21)

[Still Open](https://www.notion.so/Still-Open-34c2ba2aed6580eba3f4d4c8130ca944?pvs=21)

[Challenges (Known & Hidden)](https://www.notion.so/Challenges-Known-Hidden-34c2ba2aed6580c29169cafc4e741662?pvs=21)

trying to build a **business copilot that behaves intelligently because it understands context, but stays trustworthy because it is evidence-controlled**.

The flow in your head is:

1. The user enters from a place.
    - home = broad/general
    - RFQ page = RFQ-bound by default
2. The conversation has an owner.
    - general or specific RFQ
    - this owner does not randomly change
3. The user asks something.
    - the LLM interprets the intent
    - the system identifies the query family
    - the system resolves the target
    - the system checks permission and existence
4. The system decides the allowed evidence path.
    - conversation only
    - manager truth
    - intelligence truth
    - domain knowledge
    - no normal answer
5. The assistant answers only inside the allowed boundary.
    - if data exists, answer clearly
    - if data is partial, say what is known and missing
    - if inaccessible, stop
    - if unsupported, be honest
    - if ambiguous, ask one clarification
    - if comparison, compare only approved comparable fields
6. The LLM then turns that controlled evidence into a natural, useful, business-aware answer.

That is the whole design philosophy.

The copilot should feel like ChatGPT in fluidity, but not behave like generic ChatGPT in authority. Its authority comes from platform evidence