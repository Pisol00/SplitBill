import assert from "node:assert/strict";
import { test } from "node:test";

import { shareAction } from "../utils/payments.ts";
import type { Expense, Payment } from "../utils/types.ts";

const dinner: Expense = {
  id: 7,
  group_id: 1,
  description: "Dinner",
  paid_by: "alice",
  amount: "100.00",
  split_type: "equal",
  shares: [
    { member: "alice", amount: "33.34" },
    { member: "bob", amount: "33.33" },
    { member: "carol", amount: "33.33" },
  ],
  created_at: "2026-11-02T09:00:00Z",
};
const bobShare = { member: "bob", amount: "33.33" };

function payment(id: number, status: Payment["status"], expenseId = 7): Payment {
  return {
    id,
    expense_id: expenseId,
    from_member: "bob",
    to_member: "alice",
    amount: "33.33",
    status,
    created_at: "2026-11-02T09:00:00Z",
    decided_at: null,
  };
}

test("the payer's own share and a share of zero have no payment", () => {
  const own = { member: "alice", amount: "33.34" };
  assert.deepEqual(shareAction("alice", dinner, own, []), { kind: "none" });
  const zero = { member: "bob", amount: "0.00" };
  assert.deepEqual(shareAction("bob", dinner, zero, []), { kind: "none" });
});

test("only the member who owes the share can report a transfer", () => {
  assert.deepEqual(shareAction("bob", dinner, bobShare, []), {
    kind: "unpaid",
    rejected: false,
    canRequest: true,
  });
  assert.deepEqual(shareAction("carol", dinner, bobShare, []), {
    kind: "unpaid",
    rejected: false,
    canRequest: false,
  });
});

test("only the payer of the expense can decide a waiting payment", () => {
  const waiting = [payment(1, "pending")];
  assert.deepEqual(shareAction("alice", dinner, bobShare, waiting), {
    kind: "pending",
    paymentId: 1,
    canDecide: true,
  });
  assert.deepEqual(shareAction("bob", dinner, bobShare, waiting), {
    kind: "pending",
    paymentId: 1,
    canDecide: false,
  });
});

test("the newest payment of the share decides, and the API lists newest first", () => {
  const afterRejection = [payment(2, "pending"), payment(1, "rejected")];
  assert.equal(shareAction("alice", dinner, bobShare, afterRejection).kind, "pending");

  assert.deepEqual(shareAction("bob", dinner, bobShare, [payment(1, "rejected")]), {
    kind: "unpaid",
    rejected: true,
    canRequest: true,
  });
  assert.deepEqual(shareAction("bob", dinner, bobShare, [payment(1, "confirmed")]), {
    kind: "confirmed",
  });
});

test("payments of another expense or another member do not count", () => {
  const other = [payment(1, "confirmed", 8)];
  assert.equal(shareAction("bob", dinner, bobShare, other).kind, "unpaid");
  const carolShare = { member: "carol", amount: "33.33" };
  const bobPaid = [payment(1, "confirmed")];
  assert.equal(shareAction("carol", dinner, carolShare, bobPaid).kind, "unpaid");
});
