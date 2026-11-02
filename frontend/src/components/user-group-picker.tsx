"use client";

import { ArrowLeftRight, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useTransition } from "react";

import { selectUserAction } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { RadioCard } from "@/components/ui/radio-card";
import type { GroupSummary } from "@/utils/types";
import { USERS } from "@/utils/users";

type Props = {
  user: string;
  groups: GroupSummary[];
  groupId: number | null;
};

// A floating button that opens a modal with the users and the groups. Changing the user
// saves it in a cookie through a Server Action. Changing the group navigates to a new
// URL. In both cases the server renders the new view behind the modal.
export function UserGroupPicker({ user, groups, groupId }: Props) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  // A native dialog: showModal() traps focus, closes on Escape and returns focus.
  const dialog = useRef<HTMLDialogElement>(null);
  const groupName = groups.find((group) => group.id === groupId)?.name ?? "No groups";

  function selectUser(nextUser: string) {
    startTransition(async () => {
      await selectUserAction(nextUser);
    });
  }

  function selectGroup(nextGroupId: number) {
    startTransition(() => router.push(`/?group=${nextGroupId}`, { scroll: false }));
  }

  return (
    <>
      <button
        type="button"
        aria-haspopup="dialog"
        aria-label={`Change user or group. Signed in as ${user}, group ${groupName}`}
        title={`${user} in ${groupName}`}
        onClick={() => dialog.current?.showModal()}
        className="fixed right-4 bottom-4 z-30 flex h-14 w-14 items-center justify-center rounded-full border border-line bg-surface text-lg font-semibold uppercase text-accent shadow-lg transition-colors duration-150 ease-standard hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 sm:right-6 sm:bottom-6"
      >
        {user.slice(0, 1)}
        <span className="absolute -right-0.5 -bottom-0.5 flex h-5.5 w-5.5 items-center justify-center rounded-full border-2 border-surface bg-accent text-primary-fg">
          <ArrowLeftRight className="h-3 w-3" strokeWidth={2.5} />
        </span>
      </button>

      <dialog
        ref={dialog}
        aria-labelledby="picker-title"
        // A click on the backdrop reaches the dialog itself, not the panel inside it.
        onClick={(event) => {
          if (event.target === dialog.current) {
            dialog.current.close();
          }
        }}
        className="m-auto w-[calc(100%-2rem)] max-w-md rounded-lg border border-line bg-surface shadow-lg backdrop:bg-overlay backdrop:backdrop-blur-sm"
      >
        <div className="flex flex-col gap-5 p-5" aria-busy={pending}>
          <header className="flex items-center justify-between gap-4">
            <h2 id="picker-title" className="text-base font-semibold tracking-tight text-fg">
              Switch user or group
            </h2>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Close"
              onClick={() => dialog.current?.close()}
            >
              <X className="h-4 w-4" />
            </Button>
          </header>

          <div
            className={`flex flex-col gap-5 transition-opacity duration-150 ease-standard ${
              pending ? "opacity-60" : ""
            }`}
          >
            <fieldset className="flex flex-col gap-2">
              <legend className="mb-2 text-sm font-medium text-fg">Signed in as</legend>
              <div className="grid grid-cols-4 gap-2">
                {USERS.map((name) => (
                  <RadioCard
                    key={name}
                    name="picker-user"
                    label={name}
                    checked={name === user}
                    onChange={() => selectUser(name)}
                  />
                ))}
              </div>
            </fieldset>

            <fieldset className="flex flex-col gap-2">
              <legend className="mb-2 text-sm font-medium text-fg">Group</legend>
              {groups.length === 0 ? (
                <p className="text-sm text-fg-subtle">{user} is not in any group.</p>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {groups.map((group) => (
                    <RadioCard
                      key={group.id}
                      name="picker-group"
                      label={group.name}
                      checked={group.id === groupId}
                      onChange={() => selectGroup(group.id)}
                    />
                  ))}
                </div>
              )}
            </fieldset>
          </div>

          <Button className="self-end" onClick={() => dialog.current?.close()}>
            Done
          </Button>
        </div>
      </dialog>
    </>
  );
}
