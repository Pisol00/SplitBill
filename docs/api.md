# API Design

**Status:** Implemented.

This document describes the REST API for SplitBill. The data model behind it is
described in [schema.md](schema.md).

## Contents

- [Conventions](#conventions)
- [Authentication](#authentication)
- [Headers](#headers)
- [Endpoints](#endpoints)
  - [`GET /health`](#get-health)
  - [`GET /groups`](#get-groups)
  - [`GET /groups/{group_id}`](#get-groupsgroup_id)
  - [`POST /groups/{group_id}/expenses`](#post-groupsgroup_idexpenses)
  - [`GET /groups/{group_id}/expenses`](#get-groupsgroup_idexpenses)
  - [`DELETE /groups/{group_id}/expenses/{expense_id}`](#delete-groupsgroup_idexpensesexpense_id)
  - [`GET /groups/{group_id}/balances`](#get-groupsgroup_idbalances)
- [Access Control](#access-control)
- [Errors](#errors)
- [Code Structure](#code-structure)
- [Resolved Decisions](#resolved-decisions)

## Conventions

- **Format:** JSON request and response bodies, UTF-8.
- **Users are referred to by username** in all requests and responses. Internal user
  IDs are never exposed.
- **Money is always a JSON string.** Responses always use exactly two decimal places,
  for example `"1000.00"`. Requests must also send strings; JSON numbers are rejected,
  because a client that sends `0.1` as a number may already have lost precision.
- **Timestamps** are ISO 8601 in UTC, for example `"2026-10-28T09:15:00Z"`.
- **Ordering is explicit.** Every list is returned in a defined order, stated for each
  endpoint.
- Examples use the seed data: group 1 "Chiang Mai trip" (alice, bob, carol) and group 2
  "Office lunch" (bob, dan).

## Authentication

### Model

The brief states that requests identify the user through an `X-User` header and that
full authentication is out of scope. SplitBill therefore uses **identification, not
authentication**:

- The client sends a username in `X-User`, for example `X-User: alice`.
- The server trusts the header. There is no password, token, session, login or logout.
- **Authorization is real.** Once the user is identified, every rule is enforced on the
  server: group membership for every group endpoint, and payer-only deletion.

### Security implications

> **Warning:** Any client can act as any user by changing the header. This is acceptable
> for the assessment only. The API must not be exposed publicly in this form.

What the design protects against, and what it does not:

| Threat | Protected? |
| --- | --- |
| A user reading or changing a group they do not belong to, using their own identity | Yes: membership check, `404` |
| A member deleting an expense they did not pay, using their own identity | Yes: payer check, `403` |
| A client sending someone else's username | **No**: requires real authentication |
| Discovering which groups exist | Yes: non-members receive `404`, the same as for a missing group |

### Resolving the user

Implemented once, as the function `get_current_user` in `app/dependencies.py`. Every
`/groups` route calls it first and responds with the returned `Failure` if there is one.

| Rule | Behavior |
| --- | --- |
| Header missing | `401 missing_user` |
| Header present but empty or only whitespace | `401 missing_user` |
| Matching | Exact and case-sensitive, after trimming surrounding whitespace. `Alice` does not match `alice` |
| No user with that username | `401 unknown_user` |
| Match found | The `User` row is returned to the route |

Every `401` response includes `WWW-Authenticate: X-User`, because HTTP (RFC 9110)
requires a `401` to state how to authenticate. `X-User` is not a registered scheme; the
value only tells the client which header is expected.

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: X-User
```

```json
{
  "error": {
    "code": "missing_user",
    "message": "The X-User header is required."
  }
}
```

### Public and protected endpoints

| Endpoint | `X-User` required |
| --- | --- |
| `GET /health` | No |
| `GET /docs`, `GET /openapi.json` | No |
| Every endpoint under `/groups` | Yes |

### Swagger UI

`X-User` is a plain request header. In Swagger UI at `/docs`, enter the username in the
`x-user` field of each endpoint before sending the request.

### Frontend

The frontend keeps the selected user in a cookie, and its server sends the username as
`X-User` whenever it calls the API. Nothing secret is stored in the browser.

### Replacing it with real authentication

All user resolution is in `get_current_user`. Real authentication, for example a signed
JWT in `Authorization: Bearer`, would mainly replace that function and the `X-User`
parameter of each route. Services, authorization rules and the database schema would not
change.

## Headers

### Request headers

| Header | Used by | Required | Description |
| --- | --- | --- | --- |
| `X-User` | Every `/groups` endpoint | Yes | Username of the requesting user, for example `alice`. See [Authentication](#authentication) |
| `Content-Type` | `POST` with a body | Yes | Must be `application/json` |
| `Idempotency-Key` | `POST /groups/{group_id}/expenses` | Yes | 1 to 255 characters, unique per submission, reused when retrying the same submission. The frontend uses `crypto.randomUUID()` |
| `Accept` | All | No | `application/json` is the only supported response type |

### Response headers

| Header | When | Value |
| --- | --- | --- |
| `Content-Type` | Every response with a body | `application/json` |
| `WWW-Authenticate` | Every `401` response | `X-User` |

`204 No Content` responses have no body and no `Content-Type`.

## Endpoints

| Method | Path | Success | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | `200` | Health check |
| `GET` | `/groups` | `200` | Groups of the requesting user |
| `GET` | `/groups/{group_id}` | `200` | A group with its members |
| `POST` | `/groups/{group_id}/expenses` | `201` / `200` | Record an expense (`200` on idempotent replay) |
| `GET` | `/groups/{group_id}/expenses` | `200` | Expenses, newest first |
| `DELETE` | `/groups/{group_id}/expenses/{expense_id}` | `204` | Soft-delete an expense (payer only) |
| `GET` | `/groups/{group_id}/balances` | `200` | Net balance of each member |

---

### `GET /health`

Liveness check. Does not check the database. No headers required.

**Request**

```http
GET /health HTTP/1.1
```

**Response**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"status": "ok"}
```

---

### `GET /groups`

Returns the groups the requesting user belongs to, ordered by `id`.

**Request**

| Part | Value |
| --- | --- |
| Headers | `X-User` (required) |
| Path parameters | None |
| Body | None |

```http
GET /groups HTTP/1.1
X-User: alice
```

**Response `200 OK`**

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
[
  { "id": 1, "name": "Chiang Mai trip" }
]
```

| Field | Type | Description |
| --- | --- | --- |
| `[].id` | integer | Group ID |
| `[].name` | string | Group name |

A user with no groups receives `[]`.

**Errors:** `401 missing_user`, `401 unknown_user`.

---

### `GET /groups/{group_id}`

Returns a group and its members, ordered by username.

**Request**

| Part | Value |
| --- | --- |
| Headers | `X-User` (required) |
| Path parameters | `group_id` (integer) |
| Body | None |

```http
GET /groups/1 HTTP/1.1
X-User: alice
```

**Response `200 OK`**

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "id": 1,
  "name": "Chiang Mai trip",
  "members": ["alice", "bob", "carol"]
}
```

| Field | Type | Description |
| --- | --- | --- |
| `id` | integer | Group ID |
| `name` | string | Group name |
| `members` | string[] | Usernames of all members, ordered by username |

**Errors:** `401 missing_user`, `401 unknown_user`, `404 group_not_found`.

---

### `POST /groups/{group_id}/expenses`

Records an expense. Any group member may record an expense paid by any group member.

**Request**

| Part | Value |
| --- | --- |
| Headers | `X-User` (required), `Content-Type: application/json` (required), `Idempotency-Key` (required) |
| Path parameters | `group_id` (integer) |
| Body | See below |

Equal split:

```http
POST /groups/1/expenses HTTP/1.1
X-User: alice
Content-Type: application/json
Idempotency-Key: 7f3c2a10-dinner-0001
```

```json
{
  "description": "Dinner at the night market",
  "paid_by": "alice",
  "amount": "1000.00",
  "split": { "type": "equal", "members": ["alice", "bob", "carol"] }
}
```

Exact split:

```http
POST /groups/1/expenses HTTP/1.1
X-User: bob
Content-Type: application/json
Idempotency-Key: 0b9e4c7d-hotel-0001
```

```json
{
  "description": "Hotel room",
  "paid_by": "bob",
  "amount": "1000.00",
  "split": {
    "type": "exact",
    "shares": { "alice": "500.00", "bob": "300.00", "carol": "200.00" }
  }
}
```

| Field | Type | Rule |
| --- | --- | --- |
| `description` | string | 1 to 255 characters after trimming whitespace; no NUL characters or lone surrogates, which PostgreSQL cannot store |
| `paid_by` | string | Username of a group member |
| `amount` | string | Greater than `0`; at most 2 decimal places; at most `9999999999.99` |
| `split.type` | string | `"equal"` or `"exact"` |
| `split.members` | string[] | Equal split only. Non-empty; distinct usernames; all group members |
| `split.shares` | object | Exact split only. Non-empty; username → amount string; every user a group member; every share `>= 0` with at most 2 decimal places; shares sum exactly to `amount` |

Member order in `members`, and key order in `shares`, is preserved and stored as
`position`. For equal splits, remainder satang go to members in this order.

**Response `201 Created`** (new expense)

```http
HTTP/1.1 201 Created
Content-Type: application/json
```

```json
{
  "id": 7,
  "group_id": 1,
  "description": "Dinner at the night market",
  "paid_by": "alice",
  "amount": "1000.00",
  "split_type": "equal",
  "shares": [
    { "member": "alice", "amount": "333.34" },
    { "member": "bob", "amount": "333.33" },
    { "member": "carol", "amount": "333.33" }
  ],
  "created_at": "2026-10-28T09:15:00Z"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `id` | integer | Expense ID |
| `group_id` | integer | Group ID |
| `description` | string | As submitted, trimmed |
| `paid_by` | string | Payer's username |
| `amount` | string | Total, two decimal places |
| `split_type` | string | `"equal"` or `"exact"` |
| `shares` | object[] | One entry per member, in the submitted order |
| `shares[].member` | string | Username |
| `shares[].amount` | string | Member's share, two decimal places |
| `created_at` | string | Creation time, ISO 8601 UTC |

`shares` is a list rather than an object so that its order is explicit in every client.

**Response `200 OK`** (repeated `Idempotency-Key` with the same request)

The body is identical to the original `201` response. Nothing is created.

**Errors:** `401 missing_user`, `401 unknown_user`, `404 group_not_found`,
`422 validation_error`, `422 member_not_in_group`, `422 shares_mismatch`,
`422 idempotency_key_reused`.

Example, exact shares that do not sum to the amount:

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/json
```

```json
{
  "error": {
    "code": "shares_mismatch",
    "message": "The shares do not add up to the total."
  }
}
```

---

### `GET /groups/{group_id}/expenses`

Returns the group's expenses that are not deleted, newest first
(`created_at DESC, id DESC`). No pagination.

**Request**

| Part | Value |
| --- | --- |
| Headers | `X-User` (required) |
| Path parameters | `group_id` (integer) |
| Body | None |

```http
GET /groups/1/expenses HTTP/1.1
X-User: carol
```

**Response `200 OK`**

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
[
  {
    "id": 8,
    "group_id": 1,
    "description": "Hotel room",
    "paid_by": "bob",
    "amount": "1000.00",
    "split_type": "exact",
    "shares": [
      { "member": "alice", "amount": "500.00" },
      { "member": "bob", "amount": "300.00" },
      { "member": "carol", "amount": "200.00" }
    ],
    "created_at": "2026-10-28T10:02:00Z"
  },
  {
    "id": 7,
    "group_id": 1,
    "description": "Dinner at the night market",
    "paid_by": "alice",
    "amount": "1000.00",
    "split_type": "equal",
    "shares": [
      { "member": "alice", "amount": "333.34" },
      { "member": "bob", "amount": "333.33" },
      { "member": "carol", "amount": "333.33" }
    ],
    "created_at": "2026-10-28T09:15:00Z"
  }
]
```

Each item has the same fields as the `POST` response. A group with no expenses returns
`[]`.

**Errors:** `401 missing_user`, `401 unknown_user`, `404 group_not_found`.

---

### `DELETE /groups/{group_id}/expenses/{expense_id}`

Soft-deletes an expense: sets `deleted_at`, keeps the row, and excludes it from listings
and balances. Only the payer may delete.

**Request**

| Part | Value |
| --- | --- |
| Headers | `X-User` (required) |
| Path parameters | `group_id` (integer), `expense_id` (integer) |
| Body | None |

```http
DELETE /groups/1/expenses/7 HTTP/1.1
X-User: alice
```

**Response `204 No Content`**

```http
HTTP/1.1 204 No Content
```

No body.

**Errors:** `401 missing_user`, `401 unknown_user`, `404 group_not_found`,
`404 expense_not_found` (missing, in another group, or already deleted),
`403 not_payer`.

Example, `bob` deleting an expense paid by `alice`:

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json
```

```json
{
  "error": {
    "code": "not_payer",
    "message": "Only the payer can delete this expense."
  }
}
```

---

### `GET /groups/{group_id}/balances`

Net balance of each member, ordered by username. A positive balance means the member is
owed money; a negative balance means the member owes money. Balances sum to exactly
`0.00`. Members with no expenses have `"0.00"`.

**Request**

| Part | Value |
| --- | --- |
| Headers | `X-User` (required) |
| Path parameters | `group_id` (integer) |
| Body | None |

```http
GET /groups/1/balances HTTP/1.1
X-User: bob
```

**Response `200 OK`** (after the dinner expense only)

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
[
  { "member": "alice", "balance": "666.66" },
  { "member": "bob", "balance": "-333.33" },
  { "member": "carol", "balance": "-333.33" }
]
```

| Field | Type | Description |
| --- | --- | --- |
| `[].member` | string | Username |
| `[].balance` | string | Net balance, two decimal places; negative values have a leading `-` |

**Errors:** `401 missing_user`, `401 unknown_user`, `404 group_not_found`.

## Access Control

Checked in this order for every `/groups` endpoint, before the rules for the request body.
The one exception is a body that is not valid JSON, or a path ID that is not an integer:
the framework rejects these with `422 validation_error` before these checks run.

| Step | Failure | Status |
| --- | --- | --- |
| 1. `X-User` header present | Missing or empty | `401` (see [Authentication](#authentication)) |
| 2. `X-User` is a known user | Unknown username | `401` |
| 3. Group exists **and** the user is a member | Either is false | `404` |
| 4. (`DELETE` only) user is the payer | Not the payer | `403` |

Step 3 deliberately returns the same response whether the group does not exist or the
user is not a member, so non-members cannot discover which groups exist.

Business rule failures in a valid request, such as `paid_by` not being a group member,
return `422`, because the caller is allowed to access the group but the request content
is invalid.

Example, `alice` requesting group 2:

```http
GET /groups/2 HTTP/1.1
X-User: alice
```

```http
HTTP/1.1 404 Not Found
Content-Type: application/json
```

```json
{
  "error": {
    "code": "group_not_found",
    "message": "Group not found."
  }
}
```

## Errors

All errors, including FastAPI's request validation errors, use one JSON shape:

```json
{
  "error": {
    "code": "shares_mismatch",
    "message": "The shares do not add up to the total."
  }
}
```

- `code` is stable and machine-readable; the frontend maps it to a plain-language
  message.
- `message` is a human-readable English sentence. Clients must not parse it.

| Status | Code | When |
| --- | --- | --- |
| `401` | `missing_user` | `X-User` header missing or empty |
| `401` | `unknown_user` | `X-User` does not match a user |
| `403` | `not_payer` | Deleting an expense the user did not pay |
| `404` | `group_not_found` | Group missing, or user not a member |
| `404` | `expense_not_found` | Expense missing, in another group, or already deleted |
| `422` | `validation_error` | Malformed body, missing `Idempotency-Key` or `Content-Type`, invalid amount format |
| `422` | `member_not_in_group` | `paid_by` or a split member is not in the group |
| `422` | `shares_mismatch` | Exact shares do not sum to the amount |
| `422` | `idempotency_key_reused` | Repeated key with a different request |
| `404` | `not_found` | The URL matches no route |
| `405` | `method_not_allowed` | The URL exists but not for this method, for example `PUT` on an expense, which cannot be edited; the `Allow` header lists the supported methods |
| any | `http_error` | Any other error raised by the framework itself |
| `500` | `internal_error` | An unexpected server error. The message never contains details; they are written to the server log |

## Code Structure

The brief requires a clear separation between routing, business rules and data access.

```text
backend/app/
├── main.py           # App creation, router registration, error handlers
├── core/
│   ├── config.py     # Settings
│   ├── db.py         # Engine, session, Base
│   ├── errors.py     # Failure: an expected failure, returned as a value
│   └── error_handlers.py  # Failures and framework errors to JSON responses
├── models.py         # SQLAlchemy models
├── validators/       # Plain-Python validation of client input
│   ├── money.py      # parse_money
│   ├── headers.py    # validate_idempotency_key
│   └── expenses.py   # validate_expense_request and its dataclasses
├── schemas.py        # Pydantic response models
├── utils/
│   └── responses.py  # ok(), created(), no_content(), error()
├── dependencies.py   # get_current_user, get_member_group
├── routers/
│   ├── groups.py     # /groups, /groups/{id}, /groups/{id}/balances
│   └── expenses.py   # /groups/{id}/expenses...
├── services/
│   ├── splits.py     # Pure split arithmetic: equal allocation, exact validation
│   ├── expenses.py   # Create (with idempotency), list, delete
│   └── balances.py   # Balance calculation
└── repositories.py   # Database queries
```

| Layer | Responsibility | Must not |
| --- | --- | --- |
| Routers | Read HTTP input, call the access checks, a validator, then a service; turn each `Failure` into a response with `failure_response` | Contain business rules or queries |
| `validators/` | Check client input with plain `if` statements and return typed dataclasses or a `Failure` (`422 validation_error`) | Use a validation library, or touch the database |
| `dependencies.py` | Resolve `X-User` and enforce group membership, returning a `Failure` if either fails. Each route calls these itself | |
| Services | Business rules and transaction boundaries (commit/rollback) | Know about HTTP |
| `splits.py` | Pure `Decimal` arithmetic with no I/O | Touch the database |
| Repositories | SQLAlchemy queries | Make business decisions or commit |

`splits.py` has no dependencies, so the allocation rules, the core of the assessment, can
be unit-tested directly without a database.

Endpoints are declared with `def`, not `async def`, because the database session is
synchronous (see [design.md](design.md#synchronous-sqlalchemy)).

## Resolved Decisions

- **CORS** is not enabled. The browser calls the frontend's Route Handlers, and the
  frontend's server calls the API.
- **Non-member access returns `404`, not `403`.** Non-members cannot tell whether a
  group exists. `403` would be more explicit for a client but would confirm the group's
  existence. Deleting another member's expense returns `403`, because the requester is
  a member and can already see the expense.
- **An idempotent replay returns `200 OK`** with the original expense, so a client can
  tell a replay from a new creation (`201 Created`). The alternative, repeating the
  original `201` as Stripe does, was not chosen.
- **Error responses have no `details` field.** Only `code` and `message`, which keeps
  the error format simple; the frontend relies on `code` alone.
