"use client";

// Reads the group's data from TanStack Query. The queries were started on the server
// (see group-view.tsx), so they are already in the cache when this renders. Each
// section reads its own query, so independent data does not wait in sequence.

import { useSuspenseQuery } from "@tanstack/react-query";

import { BalanceList } from "@/components/balance-list";
import { ExpenseForm } from "@/components/expense-form";
import { ExpenseList } from "@/components/expense-list";
import { Alert } from "@/components/ui/alert";
import { friendlyMessage } from "@/utils/error-messages";
import { groupQueries } from "@/utils/queries";

type Props = { user: string; groupId: number };

export function GroupScreen({ user, groupId }: Props) {
  const { data: group } = useSuspenseQuery(groupQueries.detail(user, groupId));
  const { data: expenses } = useSuspenseQuery(groupQueries.expenses(user, groupId));
  if (!group.ok) {
    return <Alert>{friendlyMessage(group.code)}</Alert>;
  }

  return (
    <>
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-fg">{group.data.name}</h1>
        <p className="text-sm text-fg-muted">
          {group.data.members.length} members: {group.data.members.join(", ")}
        </p>
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="flex min-w-0 flex-col gap-6">
          <ExpenseForm
            // A new form, with a new Idempotency-Key, for each user and group.
            key={`${user}-${groupId}`}
            user={user}
            group={group.data}
            // The form starts closed, so the expenses and their actions are in view.
            startOpen={expenses.ok && expenses.data.length === 0}
          />
          <Expenses user={user} groupId={groupId} />
        </div>
        <aside className="order-first lg:sticky lg:top-28 lg:order-last">
          <Balances user={user} groupId={groupId} />
        </aside>
      </div>
    </>
  );
}

function Expenses({ user, groupId }: Props) {
  const { data: expenses } = useSuspenseQuery(groupQueries.expenses(user, groupId));
  const { data: payments } = useSuspenseQuery(groupQueries.payments(user, groupId));
  if (!expenses.ok) {
    return <Alert>{friendlyMessage(expenses.code)}</Alert>;
  }
  if (!payments.ok) {
    return <Alert>{friendlyMessage(payments.code)}</Alert>;
  }
  return (
    <ExpenseList
      user={user}
      groupId={groupId}
      expenses={expenses.data}
      payments={payments.data}
    />
  );
}

function Balances({ user, groupId }: Props) {
  const { data } = useSuspenseQuery(groupQueries.balances(user, groupId));
  if (!data.ok) {
    return <Alert>{friendlyMessage(data.code)}</Alert>;
  }
  return <BalanceList user={user} balances={data.data} />;
}
