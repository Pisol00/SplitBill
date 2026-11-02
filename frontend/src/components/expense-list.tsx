import { DeleteExpenseButton } from "@/components/delete-expense-button";
import { SharePayment } from "@/components/share-payment";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatAmount, fromApiAmount } from "@/utils/money";
import type { Expense, Payment } from "@/utils/types";

// Rendered on the server, so the time zone is fixed rather than the server's own.
const dateFormat = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Asia/Bangkok",
});

type Props = {
  user: string;
  groupId: number;
  expenses: Expense[];
  payments: Payment[];
};

export function ExpenseList({ user, groupId, expenses, payments }: Props) {
  const toConfirm = payments.filter(
    (payment) => payment.status === "pending" && payment.to_member === user,
  ).length;

  return (
    <Card
      title="Expenses"
      description={expenses.length === 1 ? "1 expense" : `${expenses.length} expenses`}
      action={toConfirm > 0 && <Badge tone="accent">{toConfirm} to confirm</Badge>}
    >
      {expenses.length === 0 ? (
        <p className="rounded-md border border-dashed border-line py-8 text-center text-sm text-fg-subtle">
          No expenses yet. Add the first one above.
        </p>
      ) : (
        <ul className="-my-4 divide-y divide-line">
          {expenses.map((expense) => (
            <li key={expense.id} className="flex flex-col gap-3 py-4">
              <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:gap-4">
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  {/* Anywhere: a long word without spaces, such as a URL, must still wrap. */}
                  <p className="whitespace-pre-line text-sm font-medium text-fg wrap-anywhere">
                    {expense.description}
                  </p>
                  <p className="text-xs text-fg-subtle">
                    Paid by <span className="text-fg-muted">{expense.paid_by}</span> on{" "}
                    {dateFormat.format(new Date(expense.created_at))}
                  </p>
                </div>
                <div className="flex items-center justify-between gap-1">
                  <span className="text-sm font-semibold text-fg tabular-nums">
                    {formatAmount(fromApiAmount(expense.amount))} THB
                  </span>
                  {/* Only the payer may delete; the API enforces this too. */}
                  {expense.paid_by === user && (
                    <DeleteExpenseButton
                      user={user}
                      groupId={groupId}
                      expenseId={expense.id}
                      description={expense.description}
                    />
                  )}
                </div>
              </div>
              <ul className="divide-y divide-line overflow-hidden rounded-md border border-line bg-canvas">
                {expense.shares.map((share) => (
                  <SharePayment
                    key={share.member}
                    user={user}
                    groupId={groupId}
                    expense={expense}
                    share={share}
                    payments={payments}
                  />
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
