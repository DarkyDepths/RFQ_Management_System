- **General entry**
    - first-time general entry:
        
        This means:
        
        - the user opens the general copilot
        - there is **no previous general conversation to continue**
        - the copilot starts fresh
        - no RFQ is pre-attached
        - the assistant begins in broad portfolio context
        
        This is the clean “blank start” case.
        
        The key ideas here are:
        
        - fresh empty chat
        - no RFQ assumed
        - portfolio-level help
        - user can search, ask, explore, compare
        
        Typical examples:
        
        - “show me urgent RFQs”
        - “find Aramco projects”
        - “which RFQs are blocked?”
        
        For the **first-time general entry**, the user opens the copilot from home or overview and gets a **new empty general chat**.
        
        At this moment:
        
        - no RFQ is attached
        - nothing is searched automatically
        - the assistant does not guess any RFQ
        - it stays in broad portfolio context
        
        We also agreed that the user may need a little guidance, but not a real chatbot greeting.
        
        So the best solution is:
        
        - a **fresh general thread**
        - a **neutral broad starting point**
        - a **very light welcome**
        - **no long intro**
        
        And that welcome is better as a **UI empty-state hint**, not as a first assistant message inside the chat.
        
    - resume general entry:
        
        This means:
        
        - the user opens the general copilot
        - there **is** at least one previous general conversation
        - the platform must decide whether to reopen the latest one or start fresh
        
        So here the key decision is:
        
        - resume recent general conversation :
            - the last general conversation is still recent: 
            The platform should **reopen the latest general conversation**.
        - or open a new fresh general one if the last one is stale
            - the last general conversation is old / stale: 
            The platform should **start a new fresh general chat by default**.
        
        This is the continuity case.
        
        The key ideas here are:
        
        - conversation history exists
        - still no RFQ pre-attached by default
        - the assistant continues in general portfolio context
        - freshness rule matters here
- **RFQ entry**
    - first-time RFQ entry:
        
        This means:
        
        - the user opens a specific RFQ page
        - the user clicks the floating copilot icon from inside that RFQ
        - there is **no previous conversation for this RFQ to continue**
        - the copilot starts fresh
        - the current RFQ is automatically attached as the **default context**
        - the assistant begins in RFQ-focused context
        
        This is the clean “first contextual start” case.
        
        The key ideas here are:
        
        - fresh empty RFQ chat
        - current RFQ already known
        - no need for the user to repeat the RFQ code
        - direct RFQ-level help
        - user can ask immediately about deadline, blockers, owner, briefing, readiness, stages, and similar RFQ questions
        
        Typical examples:
        
        - “what’s the deadline?”
        - “any blockers?”
        - “who owns this?”
        - “what does the briefing say?”
        
        For the **first-time RFQ entry**, the user opens the copilot from inside a specific RFQ page and gets a **new empty RFQ chat**.
        
        At this moment:
        
        - the current RFQ is attached automatically as the **default context**
        - nothing is searched automatically
        - the assistant does not ask the user to specify which RFQ they mean
        - it stays in the context of the current RFQ page by default
        
        We also agreed that the user may need a little guidance, but not a real chatbot greeting.
        
        So the best solution is:
        
        - a **fresh RFQ thread**
        - a **contextual RFQ starting point**
        - a **very light welcome**
        - **no long intro**
        
        And that welcome is better as a **UI empty-state hint**, not as a first assistant message inside the chat.
        
    - resume RFQ entry:
        
        This means:
        
        - the user opens a specific RFQ page
        - the user clicks the floating copilot icon from inside that RFQ
        - there **is** at least one previous conversation for this RFQ
        - the platform must decide whether to reopen the latest one or start fresh
        
        So here the key decision is:
        
        - resume recent RFQ conversation:
            - the last conversation for this RFQ is still recent:
            The platform should **reopen the latest conversation for this RFQ**.
        - or open a new fresh RFQ one if the last one is stale
            - the last conversation for this RFQ is old / stale:
            The platform should **start a new fresh RFQ chat by default**.
        
        This is the continuity case for a contextual RFQ thread.
        
        The key ideas here are:
        
        - conversation history exists for this RFQ
        - the current RFQ is still attached automatically as the **default context**
        - the assistant continues in the context of the current RFQ page
        - freshness rule matters here
        
        At this moment:
        
        - the platform stays inside the current RFQ context by default
        - the assistant does not ask again which RFQ the user means
        - older conversations for this RFQ stay available in that RFQ’s conversation list
        - the user can always click **New chat for this RFQ** manually
        
        One important rule still remains true:
        
        - the current RFQ is the **default context**, not a forced lock
        - if the user explicitly mentions another RFQ, the assistant can answer about it inline
        - but the conversation still belongs to the RFQ page where it was opened