"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { deleteExpenseAction } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { TrashIcon } from "@/components/ui/icons";
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

  // The Server Action deletes the expense; on success the group's queries refetch.
  const remove = useMutation({
    mutationFn: () => deleteExpenseAction(user, groupId, expenseId),
    onSuccess: async (result) => {
      if (!result.ok) {
        setError(result.message);
        return;
      }
      await queryClient.invalidateQueries({ queryKey: groupQueries.all(groupId) });
    },
    // Only unexpected failures, such as a lost connection, reach onError.
    onError: () => setError(friendlyMessage("network_error")),
  });

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant="danger-ghost"
        size="icon"
        aria-label={`Delete ${description}`}
        title="Delete"
        disabled={remove.isPending}
        onClick={() => {
          setError(null);
          remove.mutate();
        }}
      >
        <TrashIcon />
      </Button>
      {error && (
        <p role="alert" className="max-w-48 text-right text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
