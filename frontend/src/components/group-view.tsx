// Server Component: starts the group's queries on the server and hands them to
// TanStack Query through <HydrationBoundary>, so the first render has the data and the
// browser cache takes over afterwards (Next.js guide "Provide initial data from a
// Server Component").

import {
  HydrationBoundary,
  QueryClient,
  defaultShouldDehydrateQuery,
  dehydrate,
} from "@tanstack/react-query";

import { GroupScreen } from "@/components/group-screen";
import { Alert } from "@/components/ui/alert";
import * as api from "@/server/api";
import type { Selection } from "@/server/selection";
import { friendlyMessage } from "@/utils/error-messages";
import { groupQueries } from "@/utils/queries";

export function GroupView({ selection }: { selection: Selection }) {
  const { user, groups, groupId } = selection;

  if (!groups.ok) {
    return <Alert>{friendlyMessage(groups.code)}</Alert>;
  }
  if (groupId === null) {
    return <p className="text-sm text-fg-muted">{user} is not in any group.</p>;
  }

  const queryClient = new QueryClient();
  // Not awaited, so rendering is not blocked. On the server the query functions call
  // the API directly: the browser query functions use relative Route Handler URLs.
  void queryClient.prefetchQuery({
    ...groupQueries.detail(user, groupId),
    queryFn: () => api.getGroup(user, groupId),
  });
  void queryClient.prefetchQuery({
    ...groupQueries.expenses(user, groupId),
    queryFn: () => api.listExpenses(user, groupId),
  });
  void queryClient.prefetchQuery({
    ...groupQueries.balances(user, groupId),
    queryFn: () => api.getBalances(user, groupId),
  });
  void queryClient.prefetchQuery({
    ...groupQueries.payments(user, groupId),
    queryFn: () => api.listPayments(user, groupId),
  });

  return (
    <HydrationBoundary
      state={dehydrate(queryClient, {
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) || query.state.status === "pending",
      })}
    >
      <GroupScreen user={user} groupId={groupId} />
    </HydrationBoundary>
  );
}
