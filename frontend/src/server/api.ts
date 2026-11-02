// Client for the SplitBill API. Server only: Server Components, Route Handlers and
// Server Actions call it, so the browser never talks to the API directly.
import "server-only";

import { connection } from "next/server";
import { cache } from "react";

import { type ApiResult, createHttpClient, send } from "@/utils/http";
import type {
  Balance,
  Expense,
  GroupDetail,
  GroupSummary,
  NewExpense,
} from "@/utils/types";

const http = createHttpClient(process.env.API_URL ?? "http://127.0.0.1:8000");

const asUser = (user: string) => ({ "X-User": user });

/**
 * Call the API at request time only. Next.js tracks fetch() itself, but not axios: an
 * axios call reads the current time, which Cache Components forbids while prerendering.
 * connection() stops prerendering first (Next.js "connection", "Synchronous database
 * drivers").
 */
async function call<T>(config: Parameters<typeof send>[1]): Promise<ApiResult<T>> {
  await connection();
  return send<T>(http, config);
}

// Cached per request, so every Server Component that needs the list shares one call.
export const listGroups = cache((user: string) =>
  call<GroupSummary[]>({ url: "/groups", headers: asUser(user) }),
);

export function getGroup(user: string, groupId: number) {
  return call<GroupDetail>({ url: `/groups/${groupId}`, headers: asUser(user) });
}

export function listExpenses(user: string, groupId: number) {
  return call<Expense[]>({
    url: `/groups/${groupId}/expenses`,
    headers: asUser(user),
  });
}

export function getBalances(user: string, groupId: number) {
  return call<Balance[]>({
    url: `/groups/${groupId}/balances`,
    headers: asUser(user),
  });
}

export function createExpense(
  user: string,
  groupId: number,
  expense: NewExpense,
  idempotencyKey: string,
) {
  return call<Expense>({
    method: "POST",
    url: `/groups/${groupId}/expenses`,
    headers: { ...asUser(user), "Idempotency-Key": idempotencyKey },
    data: expense,
  });
}

export function deleteExpense(user: string, groupId: number, expenseId: number) {
  return call<void>({
    method: "DELETE",
    url: `/groups/${groupId}/expenses/${expenseId}`,
    headers: asUser(user),
  });
}
