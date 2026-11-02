"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { selectUserAction } from "@/app/actions";
import { Select } from "@/components/ui/select";
import type { GroupSummary } from "@/utils/types";
import { USERS } from "@/utils/users";

type Props = {
  user: string;
  groups: GroupSummary[];
  groupId: number | null;
};

// Changing the user saves it in a cookie through a Server Action. Changing the group
// navigates to a new URL. In both cases the server renders the new view.
export function UserGroupPicker({ user, groups, groupId }: Props) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function selectUser(nextUser: string) {
    startTransition(async () => {
      await selectUserAction(nextUser);
    });
  }

  function selectGroup(nextGroupId: string) {
    startTransition(() => router.push(`/?group=${nextGroupId}`, { scroll: false }));
  }

  return (
    <div
      aria-busy={pending}
      className={`grid w-full grid-cols-2 gap-3 transition-opacity duration-150 ease-standard sm:flex sm:w-auto sm:items-end ${
        pending ? "opacity-60" : ""
      }`}
    >
      <Select
        label="Signed in as"
        value={user}
        options={USERS.map((name) => ({ value: name, label: name }))}
        onChange={selectUser}
      />
      <Select
        label="Group"
        value={groupId === null ? "" : String(groupId)}
        options={groups.map((group) => ({ value: String(group.id), label: group.name }))}
        onChange={selectGroup}
        placeholder="No groups"
      />
    </div>
  );
}
