# RFQ UI Microservice

`rfq_ui_ms` is the frontend shell for the RFQ Lifecycle Intelligence Platform. It is intentionally structured around clear service boundaries:

- `rfq_manager_ms` owns operational RFQ lifecycle state.
- `rfq_intelligence_ms` owns analytical artifacts and intelligence read models.
- `rfq_ui_ms` consumes both without duplicating backend business logic.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn-style UI primitives
- Framer Motion

## Architecture

The UI keeps page files thin and routes all data through connectors and translators:

- `src/connectors/manager/*` for manager-facing API consumption
- `src/connectors/intelligence/*` for intelligence-facing API consumption
- `src/translators/*` to shape raw payloads into presentation-safe models
- `src/demo/*` for mock payloads that flow through the exact same boundary

## Demo Mode

Mock mode is enabled by default through `NEXT_PUBLIC_USE_MOCK_DATA=true`. This keeps the platform defense-ready without requiring live backends on first run.

## Run

```bash
npm install
npm run dev
```
