// What the page shows for one share of an expense. The API enforces the same rules:
// this only decides which buttons to offer.

import { fromApiAmount } from "./money.ts";
import type { Expense, Payment, Share } from "./types.ts";

export type ShareAction =
  | { kind: "none" }
  | { kind: "unpaid"; rejected: boolean; canRequest: boolean }
  | { kind: "pending"; paymentId: number; canDecide: boolean }
  | { kind: "confirmed" };

/** `payments` must be newest first, the order the API returns. */
export function shareAction(
  user: string,
  expense: Expense,
  share: Share,
  payments: Payment[],
): ShareAction {
  if (share.member === expense.paid_by || fromApiAmount(share.amount) === 0) {
    return { kind: "none" };
  }
  const latest = payments.find(
    (payment) => payment.expense_id === expense.id && payment.from_member === share.member,
  );
  if (latest?.status === "confirmed") {
    return { kind: "confirmed" };
  }
  if (latest?.status === "pending") {
    return { kind: "pending", paymentId: latest.id, canDecide: user === expense.paid_by };
  }
  return {
    kind: "unpaid",
    rejected: latest?.status === "rejected",
    canRequest: user === share.member,
  };
}
