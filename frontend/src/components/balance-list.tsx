import { Avatar } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import type { Balance } from "@/utils/types";
import { formatAmount, fromApiAmount } from "@/utils/money";

export function BalanceList({ user, balances }: { user: string; balances: Balance[] }) {
  return (
    <Card title="Balances" description="In THB. Positive means the member gets money back.">
      <ul className="flex flex-col gap-1">
        {balances.map(({ member, balance }) => {
          const satang = fromApiAmount(balance);
          return (
            <li key={member} className="flex items-center gap-3 py-1.5">
              <Avatar name={member} />
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="text-sm font-medium text-fg">
                  {member}
                  {member === user && (
                    <span className="font-normal text-fg-subtle"> (you)</span>
                  )}
                </span>
                <span className="text-xs text-fg-subtle">{status(satang)}</span>
              </div>
              <span
                className={`shrink-0 rounded-full px-2.5 py-1 text-sm font-medium tabular-nums ${amountStyle(satang)}`}
              >
                {satang > 0 ? "+" : ""}
                {formatAmount(satang)}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

function status(satang: number): string {
  if (satang > 0) return "gets back";
  if (satang < 0) return "owes";
  return "settled up";
}

function amountStyle(satang: number): string {
  if (satang > 0) return "bg-success-soft text-success";
  if (satang < 0) return "bg-danger-soft text-danger";
  return "text-fg-subtle";
}
