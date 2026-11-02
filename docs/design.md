# Design Notes

Design details beyond the decisions covered in the README.

## Repository Layout

```text
.
├── README.md
├── AI_NOTES.md          # AI usage record (required by the brief)
├── AGENTS.md            # Instructions for coding agents
├── docs/                # Design: schema.md, api.md, testing.md, design.md
├── docker-compose.yml   # The whole application: db, migrate, api, web
├── backend/
│   ├── alembic/         # Migrations: schema, then seed data
│   ├── app/
│   │   ├── main.py      # FastAPI app, error handlers, routers
│   │   ├── core/        # Settings, database, error types and error handlers
│   │   ├── dependencies.py  # Requesting user and group membership
│   │   ├── routers/     # HTTP layer: groups, expenses, payments
│   │   ├── validators/  # Plain-Python validation of client input
│   │   ├── services/    # Business rules: splits, expenses, payments, balances
│   │   ├── repositories.py  # Database queries
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── schemas.py   # Response models
│   │   └── utils/responses.py  # ok(), created(), not_found(), ...
│   ├── tests/           # pytest suite against PostgreSQL (see docs/testing.md)
│   ├── .env.example
│   └── pyproject.toml
└── frontend/
    ├── src/
    │   ├── app/         # page, layout, providers, Server Actions, Route Handlers (api/), error pages
    │   ├── components/  # Page sections: picker, expense form, balances, expenses
    │   │   └── ui/      # Design system: Button, Card, Select, Input, ... and listbox.ts
    │   ├── server/      # Server only: api.ts (axios API client), selection.ts, route-response.ts
    │   ├── utils/       # Shared: money, error messages, types, users, http (axios), queries (TanStack)
    │   └── tests/       # Unit tests (node:test)
    ├── .env.example
    └── package.json
```

## Synchronous SQLAlchemy

**Decision:** The backend uses SQLAlchemy 2 with a synchronous `Session` and the
psycopg 3 driver. Endpoints that use the database are declared with `def`, not
`async def`.

**Rationale:**

- **Workload.** The application serves a small number of users with simple CRUD and
  balance queries. Async I/O helps under thousands of concurrent connections, which this
  project does not need.
- **Correctness first.** The brief weights business-rule correctness and tests most
  heavily. Synchronous code is simpler to read, test and explain, and avoids async
  pitfalls such as implicit lazy loading raising errors.
- **Concurrency is handled by the database.** The idempotency guarantee for concurrent
  requests relies on PostgreSQL constraints and transactions, which behave the same with
  a sync or async driver.
- **Framework support.** FastAPI runs `def` endpoints in a thread pool, so a blocking
  database call does not block other requests. This matches the approach in the official
  FastAPI SQL databases tutorial.
- **Tooling.** Alembic and pytest work with sync SQLAlchemy without extra async
  configuration.

**Trade-off:** Concurrency is bounded by the thread pool and connection pool size.
Moving to async later would change every layer from routers to repositories, as well as
`app/core/db.py`, `alembic/env.py` and the tests. The business rules would stay the same.

**Rule:** Never call the synchronous `Session` inside an `async def` endpoint; it would
block the event loop.

## Soft deletion

**Decision:** `DELETE` sets `expenses.deleted_at` instead of removing the row. The
expense and its shares are kept, and every query for listings and balances filters on
`deleted_at IS NULL`.

- Only the payer may delete (`403 not_payer` otherwise). Because any member may record
  an expense for another payer, the test uses an expense recorded by `alice` and paid by
  `bob`, and checks that `alice` cannot delete it.
- Deleting an expense that is already deleted, or that belongs to another group,
  returns `404 expense_not_found`.
- Retaining rows keeps a record of what was entered and deleted, which matters for
  financial data.

## Repayments

**Decision:** A member reports that they transferred their share of an expense, and the
member who paid the expense confirms or rejects the report. Only a confirmed payment
changes balances.

- **The receiver decides.** The person who should have received the money is the one who
  can check that it arrived, so a sender cannot reduce their own debt alone.
- **Per expense, whole share.** Each payment settles one member's whole share of one
  expense. Amount and receiver come from the share, so they cannot be entered wrongly.
- **The API records, it does not move money.** The transfer happens outside the
  application, and there is no proof of transfer.
- **An expense with a waiting or confirmed payment cannot be deleted.** If it could, money
  that really changed hands would disappear from the balances. To delete an expense with a
  waiting payment, the payer first rejects the payment. A confirmed payment cannot be
  undone in this version, so its expense stays.

**Trade-off:** A member cannot pay part of a share, or pay one combined amount for several
expenses.

## Error format

Every error, including request validation errors, returns
`{"error": {"code": "...", "message": "..."}}`. `code` is stable and machine-readable,
and the frontend maps it to a plain-language message. There is no `details` field, to
keep the contract simple. The full list of codes is in [api.md](api.md).

## Expected failures are returned

**Decision:** Access checks, validators and services return a `Failure` value
(`app/core/errors.py`) instead of raising an exception. Each route checks the result and
responds with `failure_response` (`app/core/error_handlers.py`).

- **Visible control flow.** A function's return type shows that it can fail, and a route
  shows every point where a request can stop.
- **Exception handlers remain for what is still raised:** the framework's own errors
  (unknown URL, wrong method, malformed request) and unexpected bugs.

**Trade-off:** Routes are longer, and each one must call the access checks itself, so a
forgotten check is possible. `tests/test_access.py` therefore tests every route with a
missing user and a non-member.

## Frontend architecture

**Decision:** Data in the browser is managed by **TanStack Query**, HTTP calls use
**axios**, and the setup follows the Next.js 16 guide "Client-side data fetching with
TanStack Query" (bundled in `frontend/node_modules/next/dist/docs/`).

```text
browser                         Next.js server                   SplitBill API
TanStack Query (useSuspenseQuery)
  axios  ── GET /api/... ──>    Route Handlers (app/api/...)
                                  server/api.ts (axios) ──────>  FastAPI
Server Actions (useMutation) ─> app/actions.ts ──────────────>   FastAPI
```

- **Initial data from the server.** The page is a Server Component. It reads the
  selected user from a cookie and the group from the URL, starts the group, expense and
  balance queries with `prefetchQuery` without awaiting them, and passes them to the
  browser through `<HydrationBoundary>`. The first render already contains the data.
- **One cache contract.** `src/utils/queries.ts` holds each query key and its options,
  shared by the server prefetch and the Client Components, as the guide requires.
- **Browser reads go through Route Handlers.** In the browser, query functions call
  this app's Route Handlers (`src/app/api/...`) with axios; the handlers call the API
  on the server. The SplitBill API URL (`API_URL`) never reaches the browser, and the
  API needs no CORS for this frontend.
- **Writes are Server Actions run with `useMutation`.** After a successful create or
  delete, the group's queries are invalidated and refetched. Expected failures, such as
  a rejected expense or an unreachable API, are returned as values (`ApiResult`,
  `ActionResult`) and shown inline, never thrown. Server Actions can be called
  directly, so they trust nothing: the API checks the user, membership and every rule.
- **axios and Cache Components.** Next.js tracks `fetch()` but not axios, and an axios
  call reads the current time, which Cache Components forbids while prerendering. Every
  server call therefore runs `await connection()` first, the pattern the `connection`
  reference gives for I/O that is not `fetch`.
- **User in a cookie, group in the URL.** The user says who is using the app, so it is
  saved in an `httpOnly` cookie by a Server Action. A shared link therefore never
  changes who you are. The group says what is being viewed, so it stays in the URL
  (`/?group=2`) and can be bookmarked, shared and reached with the back button. If the
  URL names no group, or one the user is not in, the page redirects to the first group
  of the user, so the URL always matches the screen. The cookie only identifies the user,
  like `X-User`; it does not authenticate them.
- **Streaming with a static shell.** The header and loading skeletons are prerendered;
  the data streams in inside `<Suspense>` (`next build` reports Partial Prerender).
- **Error pages.** `error.tsx` (with `retry`), `global-error.tsx` and `not-found.tsx`
  follow the file conventions; unknown URLs return a real `404`.
- **Fonts and styles.** Geist through `next/font`, and Tailwind through
  `@tailwindcss/postcss` as the CSS guide describes.

**Trade-off:** TanStack Query and axios add two dependencies and more moving parts
(provider, query keys, hydration, invalidation) than Server Components alone. In return
the browser keeps a cache, refetches stale data when the window regains focus, and
updates only the affected queries after a change.

## Docker

**Decision:** One `Dockerfile` per application and one `docker-compose.yml` at the root.

- **Migrations are a separate service.** `migrate` runs once and must succeed before
  `api` starts, so several API containers could never run migrations at the same time.
- **Small images.** Both `Dockerfile`s build in one stage and copy only what is needed to
  another: the backend has no uv or development dependencies, and the frontend uses the
  Next.js `standalone` output.
- **Not root, no secrets.** Both containers run as an unprivileged user, and
  `.dockerignore` keeps `.env` files out of the images.
- **Local ports only.** The API and the application are published on `127.0.0.1`. The API
  stays reachable for Swagger UI and manual checks; the browser uses only the
  application. The credentials in `docker-compose.yml` are local placeholders.

## Frontend design system

**Decision:** A small design system built from design tokens, with no UI library. The
style is modern and minimal: neutral surfaces, thin borders, one near-black primary
action, an indigo accent, and green and red only for balances and errors.

- **Tokens are the only source of style.** `frontend/src/app/globals.css` defines every
  color, radius, shadow, font and easing as a semantic token (`bg-surface`,
  `text-fg-muted`, `border-line`, `bg-primary`, `text-danger`, `rounded-md`,
  `shadow-lg`, ...). Tailwind's default palette, radii and shadows are switched off, so
  a class such as `text-gray-500` generates no CSS and cannot slip in.
- **Icons from `lucide-react`.** Icons inherit the text color and are sized with
  classes, so they follow the tokens like everything else.
- **Light theme only.** Every value lives in one set of CSS variables, so a theme
  change touches only `globals.css`.
- **Pointer cursor in one place.** Tailwind gives buttons the default cursor, so a base
  rule in `globals.css` sets a pointer on enabled buttons and options, and `not-allowed`
  on disabled controls. New buttons get it without a class.
- **The actions come first.** The expense form starts closed once a group has expenses,
  and closes after saving, so the expenses and their payment buttons are in view. On a
  phone the balances come first. A row waiting for the selected user is highlighted and
  counted in the card header.
- **User and group in a modal.** A round floating button at the bottom right shows the
  current user's initial with a small swap badge, and opens a native `<dialog>` with
  cards for each. `showModal()` traps focus and closes on Escape, and each card is a
  native radio, so arrow keys work. The page behind is blurred and cannot scroll while
  the modal is open. The modal stays open after a choice, so a user can change both, and
  the page updates behind it. The exception is choosing a user who is not in the current
  group: the server redirects to that user's first group, and the modal closes with the
  redirect.
- **Responsive from 320px.** Below the `sm` breakpoint, small buttons grow to 40px for
  touch, an expense's amount moves under its name, and the payment buttons share a full
  row. Long words in a description wrap, so they cannot widen the page. On a short
  screen only the modal's choices scroll, so Done stays in view.
- **Slips are hard to make.** The delete icon asks before deleting, and the buttons on a
  payment say what they mean, "Confirm received" and "Not received", because a
  confirmation cannot be undone.
- **Accessible components.** `Select` follows the WAI-ARIA select-only combobox pattern
  and `SegmentedControl` the radio group pattern, both fully usable from the keyboard;
  their key handling is unit-tested (`src/components/ui/listbox.ts`). `Checkbox` is a native
  input drawn with tokens. Fields link errors with `aria-describedby` and
  `aria-invalid`. Animations respect `prefers-reduced-motion`.
- **Checked in a browser.** Desktop and a 390px mobile layout were rendered in
  headless Chrome. Switching user and group updated the URL and the browser history;
  adding and deleting an expense through the Server Actions updated the balances as
  expected; the browser made no request to the API itself. Before repayments were added,
  the developer started the application with `docker compose up --build` and added and
  deleted an expense in a browser. On the final interface, a script in headless Chrome
  walked the expense and payment flows and checked the cursor of every clickable element.
