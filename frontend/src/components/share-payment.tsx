"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  type ActionResult,
  decidePaymentAction,
  requestPaymentAction,
} from "@/app/actions";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { friendlyMessage } from "@/utils/error-messages";
import { formatAmount, fromApiAmount } from "@/utils/money";
import { type ShareAction, shareAction } from "@/utils/payments";
import { groupQueries } from "@/utils/queries";
import type { Expense, Payment, Share } from "@/utils/types";

type Props = {
  user: string;
  groupId: number;
  expense: Expense;
  share: Share;
  payments: Payment[];
};

// One member's share of an expense: the amount, whether it has been paid back, and the
// action the selected user can take.
export function SharePayment({ user, groupId, expense, share, payments }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (run: () => Promise<ActionResult>) => run(),
    onSuccess: async (result) => {
      if (!result.ok) {
        setError(result.message);
      }
      // Also after a failure: "already decided" means this page is out of date.
      await queryClient.invalidateQueries({ queryKey: groupQueries.all(groupId) });
    },
    // Only unexpected failures, such as a lost connection, reach onError.
    onError: () => setError(friendlyMessage("network_error")),
  });

  function run(action: () => Promise<ActionResult>) {
    setError(null);
    mutation.mutate(action);
  }

  const action = shareAction(user, expense, share, payments);
  const waitingForUser = action.kind === "pending" && action.canDecide;

  return (
    <li
      className={`flex flex-wrap items-center gap-x-3 gap-y-2 px-3 py-2.5 ${
        waitingForUser ? "bg-accent-soft" : ""
      }`}
    >
      <Avatar name={share.member} />
      <div className="flex min-w-0 flex-1 basis-24 flex-col">
        <span className="text-sm text-fg">
          {share.member}
          {share.member === user && <span className="text-fg-subtle"> (you)</span>}
        </span>
        <span className="text-xs text-fg-muted tabular-nums">
          {formatAmount(fromApiAmount(share.amount))} THB
        </span>
      </div>

      <ShareStatus action={action} share={share} expense={expense} />

      {action.kind === "pending" && action.canDecide && (
        <div className="flex gap-2">
          <Button
            size="sm"
            disabled={mutation.isPending}
            aria-label={`Confirm you received the payment from ${share.member} for ${expense.description}`}
            onClick={() =>
              run(() => decidePaymentAction(user, groupId, action.paymentId, "confirm"))
            }
          >
            Confirm received
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={mutation.isPending}
            aria-label={`You did not receive the payment from ${share.member} for ${expense.description}`}
            onClick={() =>
              run(() => decidePaymentAction(user, groupId, action.paymentId, "reject"))
            }
          >
            Not received
          </Button>
        </div>
      )}

      {action.kind === "unpaid" && action.canRequest && (
        <Button
          size="sm"
          variant="secondary"
          disabled={mutation.isPending}
          aria-label={`I paid my share of ${expense.description}`}
          onClick={() => run(() => requestPaymentAction(user, groupId, expense.id))}
        >
          I paid
        </Button>
      )}

      {error && (
        <p role="alert" className="w-full text-xs text-danger">
          {error}
        </p>
      )}
    </li>
  );
}

function ShareStatus({
  action,
  share,
  expense,
}: {
  action: ShareAction;
  share: Share;
  expense: Expense;
}) {
  switch (action.kind) {
    case "none":
      return (
        <span className="text-xs text-fg-subtle">
          {share.member === expense.paid_by ? "Paid the bill" : "Nothing to pay"}
        </span>
      );
    case "confirmed":
      return <Badge tone="success">Paid</Badge>;
    case "pending":
      return (
        <Badge tone="accent">
          {action.canDecide ? "Says they paid" : `Waiting for ${expense.paid_by} to confirm`}
        </Badge>
      );
    case "unpaid":
      return action.rejected ? (
        <Badge tone="danger">Not received</Badge>
      ) : (
        <span className="text-xs text-fg-subtle">Not paid</span>
      );
  }
}
