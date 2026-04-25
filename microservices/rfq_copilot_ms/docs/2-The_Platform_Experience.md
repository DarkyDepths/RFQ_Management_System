The platform has one copilot, not many.

But that copilot can be entered in two different ways depending on where the user is.

From the user side, it should feel natural:

When I am in a general place in the platform, the copilot is general.

When I am inside a specific RFQ, the copilot already understands that RFQ.

But it is never trapped there if I explicitly ask about another RFQ.

That is the core philosophy.

## What the user sees visually

On the home page or overview page, the user sees the main copilot entry. It feels like a normal fresh AI conversation area for the whole platform.

Inside each RFQ page, the user sees a small floating copilot icon. It is lighter, contextual, and feels attached to that RFQ page. It is not another product. It is the same copilot, entered from a more specific place.

So visually the product teaches the user something without explaining it:

the home copilot is broad, the RFQ-page copilot is contextual.

## Home page behavior

When the user opens the copilot from the home page, overview page, dashboard, or any neutral area, the conversation starts without any RFQ already selected.

This means the copilot begins in a broad understanding mode:

it can help the user search across RFQs, find projects, compare situations, identify urgency, surface patterns, and answer platform-wide questions.

Typical behavior there is:

“show me urgent RFQs”

“find Aramco projects”

“which RFQs are blocked”

“what is the latest project for this client”

“compare open RFQs by priority”

In this entry point, the copilot does not assume one RFQ unless the user asks for one.

## RFQ page behavior

When the user enters a specific RFQ page and clicks the floating copilot icon, the conversation opens already centered on that RFQ.

The user does not need to select the RFQ manually.

The page itself gives the copilot the context silently.

So if the user is on IF-0038 and opens the copilot there, the assistant should naturally understand that “what’s the deadline?”, “any blockers?”, “who owns this?”, “what does the briefing say?” all refer to IF-0038 by default.

That is the big difference:

on the home page the copilot begins neutral,

inside an RFQ page it begins already anchored.

## The most important rule

Being inside a specific RFQ does not mean the copilot becomes locked to that RFQ forever.

It only means that RFQ becomes the default context.

So if the user is on IF-0038 and asks:

“what about IF-0041?”

“compare this with IF-0041”

“show me the status of IF-0041”

the copilot should answer correctly without forcing the user to leave the page, open another module, or switch modes manually.

If the user explicitly names another RFQ but that RFQ does not exist, the copilot should say clearly: “I could not find IF-0041 in the platform.”

If the RFQ exists but the user does not have access to it, the copilot should say clearly: “You do not have access to that RFQ.”

This should be handled in one simple sentence, without panic, without fake fallback, and without pretending to know anything about an inaccessible RFQ.

So the system should think like this:

If the user says nothing specific, use the current RFQ page as the reference.

If the user explicitly names another RFQ, follow that request for that question.

If the explicitly named RFQ does not exist or is not accessible, say that clearly and stop there.

If the user is vague and it is unclear, ask one simple clarification.

This is what makes the assistant feel intelligent rather than rigid.

## Conversation organization

Conversations should be split.

This is very important for clarity.

There should be one family of conversations for general use, and separate conversation histories for each RFQ.

So the platform should not show one giant mixed list where general chats and RFQ chats are all blended together. That would confuse the user very quickly.

Instead:

The home page shows general conversations only.

Each RFQ page shows conversations for that RFQ only.

So IF-0038 has its own conversation list.

IF-0041 has its own conversation list.

The general platform copilot has its own list too.

That structure matches how people think:

home chats are broad,

RFQ chats belong to a project.

## What happens when the user opens the copilot

From the home page, opening the copilot should reopen the last general conversation by default. If there is no history yet, it opens a fresh general conversation. The user should also always have an easy “new chat” action.

From an RFQ page, opening the floating copilot should reopen the most recent conversation for that RFQ by default. If that RFQ has no previous conversation, it starts a fresh one automatically. And there should also always be a clear “new chat for this RFQ” action.

There should also be one clear freshness rule: if the latest conversation is too old, for example older than N days, the copilot should start a fresh conversation instead of automatically reopening a stale thread. This applies both to the general copilot and to each RFQ copilot history.

**Freshness threshold**

- general conversations: **3 days**
- RFQ conversations: **7 days**
- based on latest activity timestamp
- stale conversations remain manually accessible but are not auto-opened

This avoids situations where the user reopens a two-month-old context that is no longer relevant and gets confused by an outdated conversation state.

This gives continuity without forcing everything into one endless thread.

So the user experience becomes very natural:

I return to where I left off,

but I can branch into a new thread anytime.

## Ownership of a conversation

A conversation belongs to the place where it was created.

If it was created from the home page, it remains a general conversation.

If it was created from IF-0038, it remains an IF-0038 conversation.

Even if, inside the IF-0038 conversation, the user briefly asks about IF-0041, that does not transform the whole conversation into an IF-0041 conversation.

That question is only a temporary override inside the thread.

This is very important because it keeps the product organized and prevents conversation history from becoming chaotic.

So:

the home of the conversation stays stable,

the scope of an individual question can still flex.

## What the assistant feels like in general mode

In general mode, the assistant behaves like a platform copilot.

It helps the user navigate the portfolio, find RFQs, compare them, surface groups, filter mentally, and reach the right project or decision faster.

It should feel broad, exploratory, and cross-project.

The user can start vague.

The assistant helps narrow things down.

If the user asks something like “show me the latest Saudi Aramco RFQ” or “which RFQs are in estimation stage,” the copilot should search the portfolio and answer directly.

If the request matches one RFQ clearly, it can surface that result immediately.

If multiple RFQs match, it should present the options clearly.

If nothing matches, it should say so cleanly.

## What the assistant feels like inside an RFQ page

Inside an RFQ page, the assistant should feel immediate and contextual.

It should feel like:

“I already know where you are. Ask me directly.”

So the user should not need to type:

“In IF-0038, what is the deadline?”

They should be able to just say:

“What’s the deadline?”

That is the whole value of the floating RFQ-page copilot.

It reduces friction.

It makes the assistant feel embedded in the workflow, not separate from it.

## How answers should feel

The assistant should answer in a natural, useful, business-aware way.

It should not feel like a raw API viewer.

It should not dump ugly backend fields.

It should not narrate internal architecture.

It should not produce fake intelligence.

It should sound like a competent RFQ copilot that reads platform data and explains it clearly.

If data exists, it answers directly.

If data is partial, it answers with what is known and states what is missing.

If the requested RFQ does not exist, it says so clearly.

If the requested RFQ exists but is not accessible to the user’s role, it says so clearly.

If the question is ambiguous, it asks one simple clarification.

If the question is outside what the platform should help with, it declines briefly and redirects.

That keeps trust high.

## What the assistant should never do

It should never act like it knows things that are not grounded.

It should not invent blockers, invent readiness judgments, invent briefing content, invent workbook conclusions, or guess what a project probably means.

It should not pretend that an RFQ exists if it cannot be found.

It should not reveal or infer details about an RFQ that the user is not allowed to access.

If the intelligence service has a briefing or a gap analysis, the assistant can surface it and explain it.

If the platform does not have the data, the assistant should say so honestly.

So the assistant is not the intelligence engine itself.

It is the conversational layer that reads, explains, guides, and helps the user move faster.

## Memory and continuity

Each conversation should remember its own recent flow so the user can ask follow-ups naturally.

That means if the user says:

“who owns this?”

then

“and what about the deadline?”

then

“is it blocked?”

the assistant should understand the continuity.

Inside an RFQ conversation, that continuity is naturally tied to the RFQ page context.

In general conversations, continuity is broader and stays at portfolio level unless the user narrows it.

Older parts of a conversation should be compressed in the background so the thread stays coherent without becoming bloated.

But very old conversations should not be reopened automatically if they are beyond the freshness threshold. In that case, the copilot should start fresh while still allowing the user to manually reopen older history if needed.

From the user side, this should feel simple:

the assistant remembers the ongoing discussion,

but does not become confused after long use.

## The edge case: asking about another RFQ from inside one RFQ

This is one of the most important behaviors.

The user is inside IF-0038.

They open the contextual copilot.

Then they ask:

“what about IF-0041?”

The assistant should not panic, refuse, or force a context switch.

It should simply handle that question inline.

So the flow should feel like this:

the assistant knows the default context is IF-0038,

but it notices the user explicitly named IF-0041,

so it temporarily answers about IF-0041,

and then naturally remains in the IF-0038 conversation unless the user keeps going in the other direction.

If IF-0041 cannot be found, the assistant should simply say: “I could not find IF-0041 in the platform.”

If IF-0041 exists but the current user is not allowed to access it, the assistant should simply say: “You do not have access to that RFQ.”

This is the balance you want:

strong context,

but not rigid context.

## The platform mental model

For the user, the product should feel like this:

There is one AI copilot across the platform.

When I open it from a general place, it helps me across RFQs.

When I open it from inside a project, it already understands that project.

If I mention another RFQ, it can still help without breaking the flow.

If the other RFQ does not exist or is not accessible, it tells me clearly.

My general chats stay in the general area.

Each RFQ keeps its own contextual chat history.

Old conversations do not automatically take over the experience if they are stale.

That is the clean mental model.

## The final experience in one walkthrough

A user lands on the home page.

They open the main copilot.

They ask broad portfolio questions.

Those conversations live in the general conversation area.

Later, they open IF-0038.

They click the floating copilot icon.

The assistant opens the latest conversation for IF-0038, or creates a new one if needed.

If the latest conversation for IF-0038 is older than the configured freshness threshold, the assistant starts a fresh conversation instead of reopening a stale thread automatically.

Now the assistant behaves as if IF-0038 is already understood.

The user asks direct RFQ questions with no setup needed.

In the middle of that thread, the user asks about IF-0041.

The assistant answers that specific question too.

If IF-0041 does not exist or is not accessible, the assistant says that clearly instead of guessing.

But the conversation still belongs to IF-0038 because that is where it was opened.

The user stays on the same page, in the same assistant, with no friction.

That is the full product picture.

## Final summary

Your ideal copilot is:

one platform copilot,

two entry contexts,

default RFQ context when opened inside an RFQ,

general context when opened from neutral areas,

temporary override when another RFQ is explicitly mentioned,

clear handling when the requested RFQ does not exist or is not accessible,

separate conversation histories for general and for each RFQ,

opening the latest relevant conversation by default,

starting fresh when the latest conversation is older than the freshness threshold,

with a clear option to start a new one.