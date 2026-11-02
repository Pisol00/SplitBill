# AGENTS.md

Instructions for coding agents working in this repository.

## Commands

The whole application (from the repository root): `docker compose up --build`.

Database only, for development: `docker compose up -d --wait db` starts PostgreSQL 16
on port 5434. Copy `backend/.env.example` to `backend/.env` first.

Run from `backend/`:

```bash
uv sync --locked              # install dependencies
uv run alembic upgrade head   # apply migrations
uv run alembic revision --autogenerate -m "<message>"  # new migration; review before use
uv run fastapi dev            # dev server (entry point: app.main:app)
uv run pytest -v              # tests
uv run ruff check .           # lint
uv run ruff format --check .  # format check
```

Run from `frontend/` (Node 24+; `npm ci` first):

```bash
npm run dev                   # http://localhost:3000, API from API_URL (server only)
npm test                      # unit tests (node:test)
npm run lint                  # ESLint
npm run typecheck             # next typegen, then tsc
npm run build                 # production build
```

Style the frontend with design tokens only (`frontend/src/app/globals.css`):
semantic classes such as `bg-surface`, `text-fg-muted`, `border-line`, `rounded-md`.
Tailwind's default colors, radii and shadows are disabled, so classes like
`text-gray-500` silently produce nothing. Add a token before using a new value. Build
on the components in `frontend/src/components/ui/` before adding new ones.

The frontend uses Next.js 16, which has breaking changes from earlier versions. Before
writing frontend code, read the relevant guide in `frontend/node_modules/next/dist/docs/`
and follow it strictly. In particular:

- Read data with TanStack Query, following the guide
  `02-guides/client-side-data-fetching/tanstack-query.md`. Define every query in
  `src/utils/queries.ts`; the server prefetches it and passes it through
  `<HydrationBoundary>`, and Client Components read it with `useSuspenseQuery`. Never
  fetch in `useEffect`.
- In the browser, query functions call this app's Route Handlers (`src/app/api/`) with
  axios. Only `src/server/api.ts` talks to the SplitBill API, and everything in
  `src/server/` is server only.
- Every server call to the API goes through `call()` in `src/server/api.ts`, which runs
  `await connection()` first: Cache Components rejects axios during prerendering.
- Write data with Server Actions in `src/app/actions.ts`, run with `useMutation`, and
  invalidate `groupQueries.all(groupId)` on success. Return expected errors as values.

Frontend money is always integer satang (`frontend/src/utils/money.ts`); never use
floating-point baht. Keep its rules identical to the backend's.

## Engineering Rules

- Follow the official FastAPI documentation and established Python conventions.
- Use Python 3.14 and uv. Add dependencies with `uv add`; never edit `uv.lock` by hand.
- Keep the code simple, readable and maintainable. Avoid premature abstraction.
- Keep routing, business rules and data access separate.
- Validate client input in `app/validators/` with plain Python checks, called
  explicitly from the router. Do not use Pydantic request models; Pydantic is used only
  for response models and settings.
- Routes return responses through `app/utils/responses.py` (`ok`, `created`,
  `no_content`) and must declare `response_model` on the decorator, or Swagger UI
  loses the response schema. `tests/test_openapi.py` guards this.
- Report expected failures by returning `Failure` (`app/core/errors.py`), never by
  raising. Routes check each result with `isinstance(result, Failure)` and respond with
  `failure_response`. Every new route must call `get_current_user` and, for a group,
  `get_member_group` itself; add it to the route lists in `tests/test_access.py`.
- Use the synchronous SQLAlchemy `Session`. Endpoints that use it must be `def`, never
  `async def`.
- Use Ruff for linting and formatting, and pytest for automated tests.
- Do not introduce unnecessary dependencies.
- Do not commit secrets or `.env` files. Configuration goes through environment
  variables, documented in `.env.example`.
- Do not modify unrelated files.

## Financial Data Rules

- Never use floating-point arithmetic for money.
- Use Python `Decimal` and PostgreSQL `NUMERIC(12,2)`.
- Preserve exact satang precision. Reject amounts with more than two decimal places or of
  zero or less.
- Group balances must sum to exactly `0.00`.
- Enforce group membership and payer permissions.
- Prevent duplicate expenses with concurrency-safe idempotency (`Idempotency-Key`).
- Use soft deletion for expenses. Expenses are never edited.

## AI Workflow

1. Inspect the relevant existing files before changing anything.
2. Understand the requested scope.
3. Implement only the approved task.
4. Run the relevant tests and static checks.
5. Review the diff for correctness and unintended changes.
6. Report completed work and any remaining issues.
7. Never claim a check passed unless it was executed successfully.

Do not proceed to another development phase without explicit approval. Record notable AI
usage, including incorrect output, in `AI_NOTES.md`.
