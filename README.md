# SplitBill

SplitBill is a shared-expense application. It records costs shared by the members of a
group, such as a dinner bill or a hotel room, and calculates each member's net balance
accurate to the satang. A member can report that they transferred their share, and the
member who paid the expense confirms it, which updates the balances.

It uses FastAPI, PostgreSQL 16 and Next.js. See [docs/](docs/) for the [API](docs/api.md),
the [database schema](docs/schema.md), the [test plan](docs/testing.md) and further
[design notes](docs/design.md).

## Run With Docker

The quickest way to run the whole application. It needs only Docker with Docker Compose,
and internet access for the first build. From the repository root:

```bash
docker compose up --build
```

| URL | Service |
| --- | --- |
| http://localhost:3000 | The application |
| http://127.0.0.1:8000/docs | API documentation (Swagger UI) |

Ports 3000, 8000 and 5434 must be free. Stop with `docker compose down`; add `-v` to also
delete the database.

## Run for Development

You need [uv](https://docs.astral.sh/uv/), Python 3.14 (`uv python install 3.14`), Docker
with Docker Compose, and Node.js 24 or later.

**Database,** from the repository root:

```bash
docker compose up -d --wait db
```

**Backend,** from `backend/`:

```bash
uv sync --locked
cp .env.example .env
uv run alembic upgrade head
uv run fastapi dev
```

The migrations create the tables and seed the users (`alice`, `bob`, `carol`, `dan`) and
the two groups from the brief. The API runs on `http://127.0.0.1:8000`.

**Frontend,** from `frontend/`, with the API running:

```bash
cp .env.example .env.local
npm ci
npm run dev
```

The application runs on `http://localhost:3000`.

## Run the Tests

**Backend,** from `backend/`, with the database running and `.env` created:

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

Each test run drops and recreates the `splitbill_test` database and applies all
migrations. The suite refuses to run against a database whose name does not end in
`_test`.

**Frontend,** from `frontend/`, after `npm ci`:

```bash
npm test
npm run lint
npm run typecheck
npm run build
```

`npm run build` needs internet access once, for `next/font` to download the font.

## Design Decisions

### Group access: 404 for non-members

A request for a group the user does not belong to returns `404`, the same response as for
a group that does not exist. With `403`, a non-member could probe group IDs and learn which
groups exist. The trade-off is that the two cases look the same when debugging a client.

Deleting another member's expense returns `403`, because a member can already see that
expense, so hiding it gains nothing and `403` states the actual reason.

### Money storage

Money is a `Decimal` in Python, `NUMERIC(12,2)` in PostgreSQL and a string in JSON, in both
directions. `float` is never used.

- Input must be a string of up to 10 integer digits and at most 2 decimal places. JSON
  numbers are rejected, because a client that sends a number may already have lost
  precision.
- `"10.005"` is rejected with `422`, not rounded. PostgreSQL would silently store it as
  `10.01`, so the API is the only safeguard.

### Allocating remaining satang

The amount is converted to whole satang and divided by the number of members. The
remaining satang go one each to the first members **in the order the request lists them**.
`100.00` among `alice, bob, carol` gives `33.34, 33.33, 33.33`; listed as
`carol, alice, bob`, carol receives `33.34`. Integer arithmetic makes the shares sum exactly
to the amount, and the order is stored in `expense_shares.position`.

### Idempotency

| Situation | Response |
| --- | --- |
| New key in the group | `201` |
| Repeated key, same request | `200` with the original expense; nothing created |
| Repeated key, different request | `422 idempotency_key_reused`; nothing created |

The database enforces `UNIQUE (group_id, idempotency_key)`. If two concurrent requests pass
the service's check for an existing key, only one insert succeeds. The other fails on the
constraint, rolls back, reads the winning row and answers as a replay. Requests are
compared by a SHA-256 hash of the validated request. Details are in
[docs/schema.md](docs/schema.md).

### Repayments

A member reports a transfer for their whole share of an expense
(`POST /groups/{group_id}/payments`). The member who paid the expense then confirms or
rejects it. Only a confirmed payment changes balances, and it moves the same amount on both
sides, so balances still sum to exactly `0.00`. Details are in
[docs/design.md](docs/design.md#repayments).

### Frontend money without floating-point error

The frontend converts every amount to whole satang, a JavaScript integer, as soon as it is
read (`frontend/src/utils/money.ts`). `0.1 + 0.2` becomes `10 + 20 = 30` satang and displays
`0.30`.

The largest amount is far below `Number.MAX_SAFE_INTEGER`, so integer arithmetic is exact
and no decimal library is needed. A balance can exceed the largest single amount, and it
would take about 9,000 expenses of that amount to pass the limit.

The equal split preview uses the backend's algorithm, and the form sends members in the
order it previews them, so `100.00` three ways shows `33.34, 33.33, 33.33` in both.
`Intl.NumberFormat("th-TH")` groups the baht, giving `1,000.00`.

## Assumptions

Ambiguities in the brief and the interpretation adopted:

| Ambiguity | Interpretation | Reason |
| --- | --- | --- |
| The brief's example sends an `Idempotency-Key`, but does not say whether it is mandatory | `POST /groups/{group_id}/expenses` requires the header and rejects requests without it | Duplicate protection for money must always apply; an optional key would leave a gap whenever a client omits it |
| The brief says a repeated `Idempotency-Key` returns the original expense, but not what happens if the request body differs | Same key and same request returns the original expense; same key with a different request is rejected with `422` | Returning the original for a different request would hide a client bug and silently drop an expense. A hash of the normalized request is stored to compare them |
| The brief does not say what a repeated `Idempotency-Key` returns after its expense was deleted | The original expense, with `200`, exactly as for any other replay. It stays deleted and does not reappear in listings or balances | Follows the brief literally ("return the expense originally created"). In practice it is rare: the frontend sends a new key for each submission, and retries happen seconds after sending, not after someone has deleted the expense |
| The frontend must offer user selection, but the API has no endpoint that lists users | The page offers the four seeded users (`frontend/src/utils/users.ts`) | Adding an endpoint outside the brief was not needed for its scope; the user list is fixed seed data |
| The brief restricts deletion to the payer but does not say who may record an expense | Any group member may record an expense paid by any other group member. Who recorded it is not stored | The frontend form in the brief has a payer field separate from the selected user. This is the simplest rule that satisfies the brief |
| The brief does not say whether an exact split may give a member a share of zero | A share of `0.00` is accepted, as long as the shares add up to the amount | It is a valid amount, and equal splits can already produce it, for example `0.01` split three ways |
| The optional repayments extension says a repayment is recorded between two members and updates the balances, but not whether the receiver must agree | A repayment is tied to one share of an expense, and updates balances only after the member who paid the expense confirms it | The receiver is the one who can check that the money arrived, so a sender cannot reduce their own debt alone |
| The brief restricts deletion to the payer, but does not cover an expense that has repayments | An expense with a waiting or confirmed payment cannot be deleted (`409`) | Deleting it would remove money that really changed hands from the balances |

## Known Limitations and Next Steps

- `GET /health` does not check the database connection.
- The frontend has unit tests, but no automated browser tests.
- The API does not enable CORS, because the browser calls the frontend's Route Handlers
  rather than the API. A web page on another origin cannot call the API from a browser.
- The API sets no database connection timeout. When PostgreSQL is down, requests that need
  the database fail after 30 seconds. A `connect_timeout` in the engine would fail fast
  instead. The frontend stops waiting after 10 seconds and shows a message.
- Per the brief, users are identified by the `X-User` header with no authentication, so any
  client can act as any user. Group membership and payer rules are still enforced on the
  server. See [docs/api.md](docs/api.md#authentication).
- The member who records an expense is not stored, so there is no audit trail of who
  entered it. A `created_by_id` column could be added later.
- A repayment covers one member's whole share of one expense. Partial payments and one
  payment across several expenses are not supported, and a confirmed payment cannot be
  undone.
- The application does not move money or check proof of transfer. It records what the two
  members report.

Next steps, in order:

1. The optional settlement suggestions extension from the brief.
2. Real authentication, kept outside the brief's scope for now.

## Time Spent

| Phase | Approximate time |
| --- | --- |
| Project setup and documentation | 1 day |
| Database and backend | 1 day |
| Frontend | 1 day |
| **Total** | 3 days |
