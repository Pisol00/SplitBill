import { DeleteExpenseButton } from "@/components/delete-expense-button";
import { Card } from "@/components/ui/card";
import { formatAmount, fromApiAmount } from "@/utils/money";
import type { Expense } from "@/utils/types";

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
};

export function ExpenseList({ user, groupId, expenses }: Props) {
  return (
    <Card
      title="Expenses"
      description={expenses.length === 1 ? "1 expense" : `${expenses.length} expenses`}
    >
      {expenses.length === 0 ? (
        <p className="rounded-md border border-dashed border-line py-8 text-center text-sm text-fg-subtle">
          No expenses yet. Add the first one above.
        </p>
      ) : (
        <ul className="-my-3 divide-y divide-line">
          {expenses.map((expense) => (
            <li key={expense.id} className="flex items-start gap-4 py-3">
              <div className="flex min-w-0 flex-1 flex-col gap-1.5">
                <p className="whitespace-pre-line text-sm font-medium text-fg">
                  {expense.description}
                </p>
                <p className="text-xs text-fg-subtle">
                  Paid by <span className="text-fg-muted">{expense.paid_by}</span> on{" "}
                  {dateFormat.format(new Date(expense.created_at))}
                </p>
                <ul className="flex flex-wrap gap-1.5">
                  {expense.shares.map((share) => (
                    <li
                      key={share.member}
                      className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-fg-muted tabular-nums"
                    >
                      {share.member} {formatAmount(fromApiAmount(share.amount))}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex items-start gap-1">
                <span className="pt-1.5 text-sm font-semibold text-fg tabular-nums">
                  {formatAmount(fromApiAmount(expense.amount))}
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
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
