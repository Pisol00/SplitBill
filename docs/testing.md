# Testing

**Status:** Every test case in this document is implemented, except those listed under
[Known Gaps](#known-gaps).

This document describes how SplitBill is tested: the test layers, the test database,
isolation between tests, and the test cases. It is based on [schema.md](schema.md) and
[api.md](api.md).

## Contents

- [Goals](#goals)
- [Seams](#seams)
- [Test Layers](#test-layers)
- [Test Database](#test-database)
- [Isolation Between Tests](#isolation-between-tests)
- [Fixtures](#fixtures)
- [Test Cases](#test-cases)
- [File Layout](#file-layout)
- [Running the Tests](#running-the-tests)
- [Frontend Tests](#frontend-tests)
- [Known Gaps](#known-gaps)

## Goals

1. **Cover every test required by the brief**, with names that make the mapping obvious.
2. **Detect regressions,** not just pass once. The brief weights this explicitly
   ("tests cover the required cases and detect regressions", 20%). Test data is chosen
   so that a plausible bug fails a test; for example, the deletion test uses a recorder
   who is not the payer.
3. **Test against real PostgreSQL 16,** not SQLite. `NUMERIC` rounding, constraints and
   concurrent inserts behave differently in SQLite.
4. **Run with a single command:** `uv run pytest`.

## Seams

Tests go through two agreed public interfaces only:

| Seam | Catches | Misses |
| --- | --- | --- |
| `app.services.splits` (`allocate_equal`, `check_exact`) | Wrong remainder allocation, wrong totals, arithmetic edge cases | Whether the endpoints use it; HTTP and database behavior |
| HTTP API through `TestClient` with real PostgreSQL | Access control, validation, idempotency, persistence, ordering, balances, error format, seed data | Arithmetic edge cases, which are cheaper at the first seam |

Repositories, services other than `splits`, and models are internal and are covered
through the API seam, so they can be refactored without changing tests. Results are
checked through the API (for example, counting expenses with
`GET /groups/{id}/expenses`), not by querying the database.

**One deliberate exception:** the brief requires a deleted expense to be retained and
flagged, which no endpoint exposes. The soft-deletion test checks that one fact with a
direct database query.

Tests are written test-first in vertical slices: one failing test, the minimum code to
pass it, then the next test.

## Test Layers

| Layer | What it tests | Database | Speed |
| --- | --- | --- | --- |
| **Unit** | `app/services/splits.py`: equal allocation and exact-split validation, pure `Decimal` arithmetic | No | Milliseconds |
| **API** | Endpoints end to end through `TestClient`: HTTP status, headers, JSON shape, access control, business rules, persistence | Yes | Fast |
| **Concurrency** | Idempotency and payments under simultaneous requests, and balances read during concurrent writes | Yes, with real commits across connections | Slower |

The allocation arithmetic is tested at the unit level with many cases, because it is
cheap there. API tests then check that the endpoints use it correctly with a smaller
number of cases.

## Test Database

- A separate database, **`splitbill_test`**, in the same PostgreSQL 16 container as
  the development database. Tests never touch the development database `splitbill`.
- The URL is read from a **`TEST_DATABASE_URL`** environment variable (or `.env`),
  documented in `.env.example`:

  ```text
  TEST_DATABASE_URL=postgresql+psycopg://splitbill:splitbill@localhost:5434/splitbill_test
  ```

- `tests/conftest.py` sets `DATABASE_URL` to `TEST_DATABASE_URL` **before importing the
  application**, so the app's own engine and `get_db` point at the test database. No
  dependency override is needed.
- **Safety guard:** the test session aborts if the database name does not end in
  `_test`, so a misconfigured URL can never truncate development data.
- **Setup, once per test session:**
  1. Drop and recreate `splitbill_test`, so it always matches the current migrations
     even after a migration is edited during development.
  2. Run `alembic upgrade head`, the same migrations used in development, including the
     seed migration. This also tests that the migrations apply cleanly.
- Unit tests that do not request the `client` fixture never touch the database.
- If PostgreSQL is not reachable, the session stops within seconds with a message telling
  the developer to run `docker compose up -d --wait db`. The admin connection uses
  `connect_timeout`, because without it a connection to an unreachable port can hang
  indefinitely on Windows.

## Isolation Between Tests

**Approach:** after every test that uses the database, `TRUNCATE payments,
expense_shares, expenses RESTART IDENTITY`. Seed data (users, groups, memberships) is never modified by
the application, so it stays in place for all tests.

**Why not roll back a transaction per test?** Rolling back is a common pattern, but it
does not fit two parts of this project:

- The service layer commits its own transactions.
- The concurrency test needs two connections to see each other's committed rows, which
  is impossible inside a single rolled-back transaction.

Truncating these small tables is fast enough for a suite of this size, and it tests the
application exactly as it runs.

## Fixtures

| Fixture | Scope | Provides |
| --- | --- | --- |
| `database` | Session | Recreates the test database and runs migrations once |
| `client` | Function | `fastapi.testclient.TestClient(app)`; truncates expense tables after the test |

Request builders in `tests/helpers.py`, such as `post_expense`, keep each test focused on
the rule it checks rather than on request boilerplate.

## Test Cases

Tests marked **Required** are listed in the brief. Their test functions are named after
the brief's wording, so no separate pytest marker is needed.

### Split arithmetic (unit)

| Test | Required |
| --- | --- |
| `100.00` equal among three gives `33.34`, `33.33`, `33.33` | **Required** (arithmetic part) |
| `1000.00` equal among three gives `333.34`, `333.33`, `333.33` (brief's example) | |
| Remainder follows the given order: `["carol", "alice", "bob"]` gives carol `33.34` | |
| Remainder of two satang: `100.01` among three gives `33.34`, `33.34`, `33.33` | |
| Even division has no remainder: `90.00` among three gives `30.00` each | |
| Amount smaller than the member count: `0.01` among three gives `0.01`, `0.00`, `0.00` | |
| Single member receives the full amount | |
| Shares always sum exactly to the amount, over a range of amounts and member counts | |
| Exact shares summing to the amount are accepted | |
| Exact shares not summing to the amount are rejected | **Required** (arithmetic part) |

### Access control (API)

| Test | Expected | Required |
| --- | --- | --- |
| `alice` cannot read group 2: `GET /groups/2`, `/groups/2/expenses`, `/groups/2/balances` | `404 group_not_found` each | **Required** |
| `alice` cannot write group 2: `POST /groups/2/expenses` | `404 group_not_found`; no expense created | **Required** |
| `alice` cannot delete in group 2 | `404 group_not_found` | |
| Group that does not exist | `404 group_not_found`, identical to the non-member response | |
| Group ID outside the `INTEGER` range | `404 group_not_found`, not `500` | |
| Every route without a user | `401 missing_user` | |
| Every group route as a non-member (`dan` in group 1) | `404 group_not_found` | |
| Missing `X-User` | `401 missing_user` with `WWW-Authenticate: X-User` | |
| Unknown `X-User` | `401 unknown_user` | |
| `X-User: Alice` (wrong case) | `401 unknown_user` | |
| `GET /health` without `X-User` | `200` | |

### Groups (API)

| Test | Expected |
| --- | --- |
| `GET /groups` as `alice` | Group 1 only |
| `GET /groups` as `bob` | Groups 1 and 2, ordered by ID. Known weakness: the seed inserts group 1 first, so this test would likely still pass without `ORDER BY` |
| `GET /groups/1` | Members `["alice", "bob", "carol"]`. Known weakness: seed members are already in alphabetical order, so this does not prove the ordering |
| `GET /groups/2` as `dan` | Members `["bob", "dan"]` |
| `GET /groups/abc` | `422 validation_error` in the standard error format |

### Creating expenses (API)

| Test | Expected | Required |
| --- | --- | --- |
| Equal split of `100.00` among three, then balances | Shares `33.34`, `33.33`, `33.33`; balances sum to `0.00` | **Required** |
| Exact split not summing to the amount | `422 shares_mismatch`; no expense created | **Required** |
| Amount with 3 decimal places (`"10.005"`) | `422 validation_error`; no expense created | **Required** |
| Exact split share with 3 decimal places | `422 validation_error` | |
| Amount `"0.00"` and `"-5.00"` | `422 validation_error` | |
| Amount sent as a JSON number (`100`) | `422 validation_error` | |
| Amount above `9999999999.99` | `422 validation_error` | |
| Amount or share with digits outside `0-9` (`"๑๐.๕๐"`) | `422 validation_error` | |
| Text PostgreSQL cannot store: NUL or a lone surrogate, in the description or a member name | `422`, not `500` | |
| `paid_by` not in the group (`dan` in group 1) | `422 member_not_in_group` | |
| Split member not in the group | `422 member_not_in_group` | |
| Duplicate member in an equal split | `422 validation_error` | |
| Empty description, or empty member list | `422 validation_error` | |
| Missing `Idempotency-Key`, or one that is empty or over 255 characters | `422 validation_error` | |
| Body that is not a JSON object, and fields of the wrong type | `422 validation_error` | |
| Recording an expense paid by another member (`alice` records, `bob` pays) | `201` | |
| Response shape | All fields from api.md; money as two-decimal strings; shares in submitted order | |
| Error response shape | Exactly `{"error": {"code", "message"}}` | |

### Idempotency (API and concurrency)

| Test | Expected | Required |
| --- | --- | --- |
| Repeated key with the same request | First `201`, second `200` with the same body; one expense in the database | **Required** |
| Same key in two different groups | Two separate expenses | |
| Same request with `"1000.0"` instead of `"1000.00"` | Treated as the same request: `200` | |
| Repeated key with a different request | `422 idempotency_key_reused`; still one expense | |
| Repeated key with members in a different order | `422 idempotency_key_reused` | |
| Concurrent requests with the same key | Exactly one expense; every response returns the same expense ID | |
| Repeated key after the expense was deleted | `200` with the original expense; it stays deleted | |

The concurrency test sends the same request from several threads at once, synchronized
with a `threading.Barrier`, then lists the group's expenses through the API.

### Deleting expenses (API)

| Test | Expected | Required |
| --- | --- | --- |
| Only the payer can delete: `alice` records an expense paid by `bob`; `carol` and `alice` try to delete, then `bob` | `403 not_payer`, `403 not_payer`, then `204` | **Required** |
| Deleted expense is kept but excluded | Absent from list and balances (API); row still exists with `deleted_at` set (the one direct database check) | |
| Deleting twice | Second attempt `404 expense_not_found` | |
| Expense ID from another group | `404 expense_not_found` | |
| Expense ID outside the `INTEGER` range | `404 expense_not_found`, not `500` | |

### Listing and balances (API)

| Test | Expected |
| --- | --- |
| Expenses are listed newest first | Order by `created_at DESC, id DESC` |
| Balances with no expenses | Every member `"0.00"` |
| Balances after several equal and exact expenses | Expected values; sum exactly `0.00` |
| Balance sign | Payer positive, others negative |
| Reading balances while expenses are being recorded | Every read sums to exactly `0.00` |

### Payments (API and concurrency)

| Test | Expected |
| --- | --- |
| A member reports a transfer for their share | `201`; sender, receiver and amount from the share; `pending` |
| Waiting or rejected payment | Balances unchanged |
| Confirmed payment | `alice 33.33`, `bob 0.00`, `carol -33.33`; sum exactly `0.00` |
| Reporting again after a rejection | `201` with a new payment |
| Reporting again while waiting or confirmed | `409 payment_already_requested`; still one payment |
| The payer reports on their own expense | `422 own_share` |
| No share, or a share of `0.00` | `422 no_share` |
| Deciding as the sender or another member | `403 not_payment_receiver`; still `pending`, balances unchanged |
| Deciding twice, in every combination of confirm and reject | `409 payment_not_pending`; balances keep the first decision |
| Payment that is missing, in another group, or with an ID outside the `INTEGER` range | `404 payment_not_found`, not `500` |
| Expense that is deleted, in another group, or with an ID outside the `INTEGER` range | `404 expense_not_found`, not `500` |
| Body that is not an object, or `expense_id` that is not an integer | `422 validation_error` |
| Deleting an expense with a waiting or confirmed payment | `409 expense_has_payments` |
| Deleting an expense with only rejected payments | `204`; its payments leave the list |
| Payments are listed newest first, and only for the group | Order by `created_at DESC, id DESC` |
| Concurrent reports for one share | One `201`, the others `409`; one payment |
| Concurrent confirms and rejects | One `200`, the others `409`; balances sum to `0.00` |
| Concurrent report and deletion of an expense | Either `201` and `409`, or `404` and `204`; never both succeed |

### Migrations and seed

| Test | Expected |
| --- | --- |
| Seed data present after `alembic upgrade head` | Four users exist; groups 1 and 2 have the brief's names and members; each user sees exactly their groups. Checked through the API |

### Errors and API documentation

| Test | Expected |
| --- | --- |
| Unknown URL | `404 not_found` in the standard error format |
| Unsupported method | `405 method_not_allowed` with an `Allow` header |
| Unexpected error | `500 internal_error`; no details in the response, full details in the server log |
| `Failure` with no mapped status | `500 internal_error` in the standard error format |
| Every endpoint with a body | Its response schema appears in OpenAPI |

## File Layout

```text
backend/tests/
├── conftest.py           # Test database setup, safety guard, client fixture
├── helpers.py            # Request builders shared by the API tests
├── test_health.py        # GET /health
├── test_splits.py        # Unit: split arithmetic
├── test_access.py        # X-User, 401, 404 for non-members, validation error format
├── test_groups.py        # GET /groups, GET /groups/{id}
├── test_expenses.py      # POST validation and business rules, response shape, listing
├── test_idempotency.py   # Idempotency, including concurrency and replay after deletion
├── test_delete.py        # Soft deletion and payer-only rule
├── test_balances.py      # Balance calculation and zero sum
├── test_payments.py      # Reporting, confirming and rejecting payments, with concurrency
├── test_seed.py          # Seed data, checked through the API
├── test_errors.py        # 404, 405 and 500 in the standard error format
└── test_openapi.py       # Every endpoint documents its response schema
```

## Running the Tests

```bash
docker compose up -d --wait db   # from the repository root, once
cd backend
uv run pytest                 # all tests
uv run pytest tests/test_splits.py   # unit tests only, no database needed
```

## Frontend Tests

`frontend/src/tests/*.test.ts`, run with `npm test` using Node's built-in `node:test`
(no test library). They cover the integer-satang arithmetic against the backend's own
cases (`100.00` three ways, remainder order, `0.01` three ways, `0.1 + 0.2` displays
`0.30`, Thai formatting, parsing rules, balances above the largest single amount), the
plain-language error messages, keyboard handling, a server that never answers, and which
payment action each user is offered for a share.

There are no automated browser tests. The page was checked in headless Chrome against
the running API and the test database: server-rendered data, switching user and group
(URL and history), adding and deleting an expense through the Server Actions with
TanStack Query refetching through the Route Handlers, a `404`
for unknown URLs, an inline message when the API is down, and that the browser makes no
request to the API itself. The payment flow was checked the same way: reporting, waiting,
rejecting, reporting again and confirming as `bob`, `carol` and `alice`, the balances
after each step, the message when deleting an expense with a waiting payment, and the
layout at 390px. The floating user and group picker was also checked: choosing a user and
a group, the arrow keys, every way to close the modal, focus returning to the button, and
the pointer cursor on its controls.

## Known Gaps

- An exact split with a share of `0.00` has no automated test. It was checked once against
  the test database: the API returned `201`, and the balances summed to `0.00`.
- The idempotency concurrency test does not guarantee that two requests reach the database
  constraint at the same moment on every run, so it may not always exercise that path.
- The same applies to the payment concurrency tests. In one check with the lock removed
  from reporting a payment, the test for concurrent reports still passed, while the test
  for a concurrent report and deletion failed. The unique index still prevents a duplicate.
