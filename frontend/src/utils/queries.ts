// TanStack Query cache contract: one key and one set of options per query, shared
// by the Server Component that provides initial data and the Client Components that
// read it (Next.js guide "Client-side data fetching with TanStack Query").
//
// In the browser, the query functions call this app's Route Handlers (app/api/...),
// which call the SplitBill API on the server. Each query resolves to an ApiResult, so
// an expected failure is data to render, not an error to catch.

import { queryOptions } from "@tanstack/react-query";

import { type ApiResult, createHttpClient, send } from "./http";
import type { Balance, Expense, GroupDetail } from "./types";

const routeHandlers = createHttpClient("/api");

function get<T>(url: string, user: string): Promise<ApiResult<T>> {
  return send<T>(routeHandlers, { url, headers: { "X-User": user } });
}

// Hydrated data stays fresh this long before a background refetch.
const staleTime = 30_000;

export const groupQueries = {
  /** Prefix shared by every query of one group, used to refetch after a change. */
  all: (groupId: number) => ["groups", groupId] as const,

  detail: (user: string, groupId: number) =>
    queryOptions({
      queryKey: ["groups", groupId, "detail", user] as const,
      queryFn: () => get<GroupDetail>(`/groups/${groupId}`, user),
      staleTime,
    }),

  expenses: (user: string, groupId: number) =>
    queryOptions({
      queryKey: ["groups", groupId, "expenses", user] as const,
      queryFn: () => get<Expense[]>(`/groups/${groupId}/expenses`, user),
      staleTime,
    }),

  balances: (user: string, groupId: number) =>
    queryOptions({
      queryKey: ["groups", groupId, "balances", user] as const,
      queryFn: () => get<Balance[]>(`/groups/${groupId}/balances`, user),
      staleTime,
    }),
};
