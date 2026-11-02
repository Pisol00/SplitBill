"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useState } from "react";

import { deleteExpenseAction } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { friendlyMessage } from "@/utils/error-messages";
import { groupQueries } from "@/utils/queries";

type Props = {
  user: string;
  groupId: number;
  expenseId: number;
  description: string;
};

export function DeleteExpenseButton({ user, groupId, expenseId, description }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  // One click on the icon only asks: a deleted expense cannot be brought back here.
  const [confirming, setConfirming] = useState(false);

  // The Server Action deletes the expense; on success the group's queries refetch.
  const remove = useMutation({
    mutationFn: () => deleteExpenseAction(user, groupId, expenseId),
    onSuccess: async (result) => {
      setConfirming(false);
      if (!result.ok) {
        setError(result.message);
        return;
      }
      await queryClient.invalidateQueries({ queryKey: groupQueries.all(groupId) });
    },
    // Only unexpected failures, such as a lost connection, reach onError.
    onError: () => {
      setConfirming(false);
      setError(friendlyMessage("network_error"));
    },
  });

  return (
    <div className="flex flex-col items-end gap-1">
      {confirming ? (
        <div className="flex gap-1">
          <Button
            variant="danger"
            size="sm"
            aria-label={`Yes, delete ${description}`}
            disabled={remove.isPending}
            onClick={() => remove.mutate()}
          >
            Delete
          </Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={remove.isPending}
            onClick={() => setConfirming(false)}
          >
            Cancel
          </Button>
        </div>
      ) : (
        <Button
          variant="danger-ghost"
          size="icon"
          aria-label={`Delete ${description}`}
          title="Delete"
          onClick={() => {
            setError(null);
            setConfirming(true);
          }}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
      {error && (
        <p role="alert" className="max-w-48 text-right text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
