# AI Notes

This document records how AI tools were used to build SplitBill. The developer is
accountable for every line submitted and reviews all AI-generated output before
committing it.

## AI Tools Used

| Tool | Used for |
| --- | --- |
| Claude Code (Anthropic, VS Code extension) | Learning FastAPI; turning the developer's draft of the Phase 01 specification into a more detailed one; repository exploration; design documents in `docs/`; writing the backend, frontend, tests, migrations and Docker setup; code reviews; running verification commands; drafting `README.md`, `AI_NOTES.md` and `AGENTS.md` |

## Effective Prompts

### 1. Phase 01: FastAPI project setup

A structured task specification given to Claude Code. The developer wrote a draft, and
AI made it more detailed and precise. Abridged:

> Set up a clean, maintainable FastAPI backend project for the SplitBill application.
> […] The initial FastAPI application has already been run successfully. Review the
> existing project before making changes.
>
> Out of scope: PostgreSQL configuration, SQLAlchemy models, Alembic migrations, […]
> business logic, Docker configuration, frontend implementation.
>
> […] Do not claim a check passed unless it was executed successfully. Explain any
> deviation from the specification.
>
> Stop after completing Phase 01.

Why it worked: the explicit in-scope and out-of-scope lists, the exact verification
commands and the "stop after this phase" boundary kept the output small and reviewable,
and the requirement to report deviations surfaced a needed pytest configuration fix.

### 2. Checking the frontend against the official documentation

Refined after use from a shorter request made during the project:

> อ่าน docs ของ Next.js 16 ใน `frontend/node_modules/next/dist/docs/` เฉพาะส่วนที่
> frontend นี้ใช้ แล้วลิสต์ทุกจุดที่โค้ดของเราไม่ตรงกับ docs พร้อมบอกไฟล์และ guide ที่เกี่ยวข้อง
> จากนั้นแก้ทุกจุด รัน typecheck, ESLint, unit test และ `next build` แล้วเปิดหน้าเว็บตรวจใน
> browser ถ้ามีการตรวจไหนที่ไม่ได้รัน ให้รายงานด้วย

Why it works: it makes the AI compare its own code with the documentation instead of
relying on memory. The shorter request found seven deviations in code the AI had written,
including data fetching in `useEffect` and a fully client-side page.

## Incorrect or Unsafe AI Output

### 1. Commit created without being asked

- **What AI did:** Early in the project, Claude Code ran `git commit` although the
  developer had not asked for a commit.
- **Why it was unsafe:** The changes were committed before the developer had checked
  them.
- **How it was detected:** The developer noticed it and asked for it to be undone.
- **Correction applied:** The commit was removed, and the developer now creates every
  commit.

### 2. Balances could break the zero-sum rule

- **What AI did:** `group_balances` read the amounts paid and the shares owed in two
  separate queries. All tests passed with this code.
- **Why it was incorrect:** An expense committed between the two queries counted on only
  one side, so reading balances during concurrent writes could return a sum of `-100.00`.
  The brief requires exactly `0.00`.
- **How it was detected:** An AI code review flagged the two reads. A new test with
  concurrent writes then reproduced the failure in 3 of 3 runs.
- **Correction applied:** Balances are now calculated in one SQL statement, and the test
  passes. It remains in the suite as a regression test.

## Open Concerns

### Synchronous database access feels unfamiliar

- **Concern:** The developer is used to JavaScript, where database calls use `await`, and
  finds the synchronous `def` routes with SQLAlchemy `Session` unfamiliar. They asked
  whether `async def` with `AsyncSession` is the standard choice, and which one most
  developers use.
- **What AI did:** It recommended staying synchronous. It first cited the FastAPI
  documentation from memory, then opened the SQL Databases and Concurrency pages and the
  official Full Stack FastAPI Template to confirm that they use `def` with `Session`.
- **What remains uncertain:** The AI had no reliable data on what most developers use.
  The sources show what FastAPI recommends, not what is most common. They also allow
  `async def` when a library supports `await`.
- **Current decision:** The code stays synchronous for now. Moving to async remains
  possible, but would change every layer from routers to repositories, as well as
  `alembic/env.py` and the tests.

## AI Code Review Process

### Intended process before each commit

1. **Functional correctness:** read every changed line in the diff and confirm it does
   what the task requires and nothing more.
2. **Business rules:** check money handling (no `float`, `Decimal` only), remainder
   allocation, zero-sum balances, group membership and payer permissions against the
   brief.
3. **Security:** no secrets or `.env` files committed; access control enforced on every
   group endpoint; no unvalidated input reaching the database.
4. **Tests:** run `uv run pytest -v`; add or update tests for every rule changed.
   Confirm a new test fails without the change when practical.
5. **Lint and formatting:** run `uv run ruff check .` and `uv run ruff format --check .`.
6. **Dependency changes:** review any change to `pyproject.toml` or `uv.lock`; reject
   dependencies that are not needed.
7. **Scope:** confirm no unrelated files were changed (`git status`, `git diff`).

### Checks performed

Each row shows the problem a check found, how it was fixed, and how the fix was confirmed.
Every problem listed here has been fixed. "None" means the check found no problem.

| Area | Problem found | Fix | How it was confirmed |
| --- | --- | --- | --- |
| Splitting money | None | Not needed | Tests were written first and failed until the code existed. The order for handing out leftover satang was then changed on purpose: 5 tests failed, and the code was restored. |
| Money validation | `"10.005"` was accepted and silently rounded, and Thai digits were accepted as money | Added strict validation of the money format | Tests now confirm that both are rejected |
| Access control | `alice` could read group 2, because the membership check did not exist yet | Added the membership check | Tests confirm that every route rejects a missing user and a non-member |
| Idempotency | Concurrent requests with the same key raised `UniqueViolation` in 3 of 3 runs | Catch the constraint error and return the original expense | The concurrency test passed 5 consecutive runs |
| Balances | Balances summed to `-100.00` during concurrent writes in 3 of 3 runs | Calculate balances in one SQL statement | The full suite passed 6 consecutive runs |
| Database schema | IDs used `SERIAL` instead of the `IDENTITY` in `docs/schema.md` | Declared the columns with `Identity()` | Generated DDL compared again; migration upgrade and downgrade run |
| Frontend | Seven deviations from the Next.js docs; a balance above `9999999999.99` made the page's money conversion fail; API calls had no timeout | Corrected the deviations; allowed larger balances; added a 10 second timeout | Unit tests cover the balance and the timeout. Adding and deleting expenses, URL handling and an API outage were checked in headless Chrome. After the last fixes, adding and deleting were checked again by hand |
| Docker | None | Not needed | All services started on a new volume and migrations ran from scratch in order. Containers run as non-root, and images have no `.env` files |
| Repayments | None | Not needed | Tests were written first and failed until the code existed. Five rules were then removed on purpose, one at a time: the three locks, counting only confirmed payments, and the receiver check. Each removal made at least one test fail, and the code was restored. The flow was checked in headless Chrome |

Latest results: the backend passes 180 tests, `ruff check`, `ruff format --check` and
`alembic check`, and the frontend passes 26 unit tests, ESLint and `tsc`. Before repayments
were added, the developer ran `docker compose up --build`, which also builds the frontend,
and added and deleted an expense in a browser. With repayments, the AI built and started
all services with Docker and requested the page and the payments endpoints. The AI checked
the repayment screens in headless Chrome against the test database.
