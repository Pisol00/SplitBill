"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { type FormEvent, useRef, useState } from "react";

import { createExpenseAction } from "@/app/actions";

import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/textarea";
import {
  allocateEqual,
  formatAmount,
  parseAmount,
  type Share,
  toApiAmount,
} from "@/utils/money";
import { friendlyMessage } from "@/utils/error-messages";
import { groupQueries } from "@/utils/queries";
import type { GroupDetail, NewExpense } from "@/utils/types";

type SplitType = "equal" | "exact";

type Props = {
  user: string;
  group: GroupDetail;
  startOpen: boolean;
};

export function ExpenseForm({ user, group, startOpen }: Props) {
  const members = group.members;
  const [open, setOpen] = useState(startOpen);
  const [description, setDescription] = useState("");
  const [amountText, setAmountText] = useState("");
  const [paidBy, setPaidBy] = useState(members.includes(user) ? user : members[0]);
  const [splitType, setSplitType] = useState<SplitType>("equal");
  const [selected, setSelected] = useState<string[]>(members);
  const [exactText, setExactText] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  // The Server Action saves the expense; on success the group's queries refetch.
  const create = useMutation({
    mutationFn: ({ expense, key }: { expense: NewExpense; key: string }) =>
      createExpenseAction(user, group.id, expense, key),
    onSuccess: async (result) => {
      if (!result.ok) {
        setError(result.message);
        return;
      }
      pending.current = null;
      setDescription("");
      setAmountText("");
      setExactText({});
      setOpen(false);
      await queryClient.invalidateQueries({ queryKey: groupQueries.all(group.id) });
    },
    // Only unexpected failures, such as a lost connection, reach onError.
    onError: () => setError(friendlyMessage("network_error")),
  });
  const submitting = create.isPending;
  // One Idempotency-Key per submission, reused if the same submission is retried.
  const pending = useRef<{ payload: string; key: string } | null>(null);

  const total = parseAmount(amountText);
  const amountValid = total !== null && total > 0;

  // Equal split: members in group order, so the preview gives the remainder satang
  // to the same members as the backend.
  const chosen = members.filter((member) => selected.includes(member));
  const equalShares: Share[] =
    amountValid && chosen.length > 0 ? allocateEqual(total, chosen) : [];

  // Exact split: only members with an entered amount take part.
  const exactEntries = members
    .filter((member) => (exactText[member] ?? "") !== "")
    .map((member) => ({ member, satang: parseAmount(exactText[member]) }));
  const invalidExact = exactEntries.some((entry) => entry.satang === null);
  const allocated = exactEntries.reduce(
    (sum, entry) => sum + (entry.satang ?? 0),
    0,
  );
  const unallocated = (total ?? 0) - allocated;

  const canSubmit =
    !submitting &&
    description.trim() !== "" &&
    amountValid &&
    (splitType === "equal"
      ? chosen.length > 0
      : exactEntries.length > 0 && !invalidExact && unallocated === 0);

  // Why the form cannot be submitted yet, shown next to the disabled button.
  const blocker =
    description.trim() === ""
      ? "Add a description"
      : !amountValid
        ? "Enter an amount"
        : splitType === "equal" && chosen.length === 0
          ? "Choose at least one member"
          : splitType === "exact" && (invalidExact || unallocated !== 0)
            ? "Shares must add up to the total"
            : null;

  function toggleMember(member: string) {
    setSelected((current) =>
      current.includes(member)
        ? current.filter((name) => name !== member)
        : [...current, member],
    );
  }

  function buildExpense(totalSatang: number): NewExpense {
    const split: NewExpense["split"] =
      splitType === "equal"
        ? { type: "equal", members: chosen }
        : {
            type: "exact",
            shares: Object.fromEntries(
              exactEntries.map((entry) => [
                entry.member,
                toApiAmount(entry.satang ?? 0),
              ]),
            ),
          };
    return {
      description: description.trim(),
      paid_by: paidBy,
      amount: toApiAmount(totalSatang),
      split,
    };
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit || total === null) {
      return;
    }
    const expense = buildExpense(total);
    const payload = JSON.stringify(expense);
    if (pending.current?.payload !== payload) {
      pending.current = { payload, key: crypto.randomUUID() };
    }

    setError(null);
    create.mutate({ expense, key: pending.current.key });
  }

  return (
    <Card
      title="New expense"
      description={`Split a cost within ${group.name}.`}
      action={
        open ? (
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            Close
          </Button>
        ) : (
          <Button size="sm" onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" />
            Add expense
          </Button>
        )
      }
    >
      {open && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <TextArea
                label="Description"
                value={description}
                onChange={setDescription}
                maxLength={255}
                placeholder="Dinner at the night market"
              />
            </div>

            <Input
              label="Amount"
              value={amountText}
              onChange={(value) => setAmountText(value.trim())}
              inputMode="decimal"
              placeholder="1000.00"
              suffix="THB"
              align="right"
              error={
                amountText !== "" && !amountValid
                  ? "Enter an amount above 0 with at most 2 decimal places."
                  : null
              }
            />

            <Select
              label="Paid by"
              value={paidBy}
              options={members.map((member) => ({ value: member, label: member }))}
              onChange={setPaidBy}
            />
          </div>

          <div className="flex flex-col gap-3">
            <SegmentedControl
              label="Split"
              value={splitType}
              onChange={setSplitType}
              options={[
                { value: "equal", label: "Equally" },
                { value: "exact", label: "Exact amounts" },
              ]}
            />

            <div className="rounded-md border border-line bg-canvas">
              <ul className="divide-y divide-line">
                {members.map((member) => (
                  <li
                    key={member}
                    className={`flex min-h-14 items-center justify-between gap-4 px-4 py-2 ${
                      splitType === "equal" ? "transition-colors hover:bg-surface-hover" : ""
                    }`}
                  >
                    {splitType === "equal" ? (
                      <>
                        <Checkbox
                          checked={selected.includes(member)}
                          onChange={() => toggleMember(member)}
                        >
                          <span className="flex items-center gap-2.5">
                            <Avatar name={member} />
                            {member}
                          </span>
                        </Checkbox>
                        <span className="text-sm text-fg tabular-nums">
                          {formatShare(equalShares, member)}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="flex items-center gap-2.5 text-sm text-fg">
                          <Avatar name={member} />
                          {member}
                        </span>
                        <div className="w-36">
                          <Input
                            label={`Share for ${member}`}
                            hideLabel
                            value={exactText[member] ?? ""}
                            onChange={(value) =>
                              setExactText((current) => ({
                                ...current,
                                [member]: value.trim(),
                              }))
                            }
                            inputMode="decimal"
                            placeholder="0.00"
                            align="right"
                            error={
                              (exactText[member] ?? "") !== "" &&
                              parseAmount(exactText[member]) === null
                                ? "At most 2 decimal places"
                                : null
                            }
                          />
                        </div>
                      </>
                    )}
                  </li>
                ))}
              </ul>

              {splitType === "exact" && (
                <p
                  className={`flex justify-between border-t border-line px-4 py-3 text-sm tabular-nums ${
                    unallocated === 0 && !invalidExact ? "text-success" : "text-fg-muted"
                  }`}
                >
                  <span>{unallocated < 0 ? "Over the total by" : "Left to allocate"}</span>
                  <span className="font-medium">{formatAmount(Math.abs(unallocated))}</span>
                </p>
              )}
            </div>
          </div>

          {error && <Alert>{error}</Alert>}

          <div className="flex flex-wrap items-center justify-end gap-3">
            <span className="text-sm text-fg-subtle tabular-nums">
              {blocker ?? `Total ${formatAmount(total ?? 0)} THB`}
            </span>
            <Button type="submit" disabled={!canSubmit}>
              {submitting ? "Saving..." : "Add expense"}
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
}

function formatShare(shares: Share[], member: string): string {
  const share = shares.find((entry) => entry.member === member);
  return share ? formatAmount(share.satang) : "";
}
