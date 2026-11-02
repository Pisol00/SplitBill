"use server";

// Server Actions for the page. They call the API on the server. TanStack Query owns the
// page's data in the browser, so the callers refetch it (useMutation then
// invalidateQueries) instead of refreshing the route.
//
// Server Functions can be reached by a direct POST, not only through this UI. They
// trust nothing: the API checks the user, group membership, the payer and every
// business rule on each request.

import { cookies } from "next/headers";

import * as api from "@/server/api";
import { friendlyMessage } from "@/utils/error-messages";
import type { NewExpense } from "@/utils/types";
import { isKnownUser, USER_COOKIE } from "@/utils/users";

/** Expected failures are returned as values (Next.js "Handling expected errors"). */
export type ActionResult = { ok: true } | { ok: false; message: string };

/** Remember the selected user. Setting a cookie makes Next.js re-render the page. */
export async function selectUserAction(user: string): Promise<ActionResult> {
  if (!isKnownUser(user)) {
    return { ok: false, message: friendlyMessage("unknown_user") };
  }
  const cookieStore = await cookies();
  cookieStore.set(USER_COOKIE, user, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
  });
  return { ok: true };
}

export async function createExpenseAction(
  user: string,
  groupId: number,
  expense: NewExpense,
  idempotencyKey: string,
): Promise<ActionResult> {
  const result = await api.createExpense(user, groupId, expense, idempotencyKey);
  if (!result.ok) {
    return { ok: false, message: friendlyMessage(result.code) };
  }
  return { ok: true };
}

export async function deleteExpenseAction(
  user: string,
  groupId: number,
  expenseId: number,
): Promise<ActionResult> {
  const result = await api.deleteExpense(user, groupId, expenseId);
  if (!result.ok) {
    return { ok: false, message: friendlyMessage(result.code) };
  }
  return { ok: true };
}
