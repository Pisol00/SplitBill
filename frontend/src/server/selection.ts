// The selected user lives in a cookie, because it says who is using the app. The
// selected group lives in the URL (/?group=1), because it says what is being viewed, so
// a link shows that group to whoever opens it. Server only.
import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

import type { ApiResult } from "@/utils/http";
import type { GroupSummary } from "@/utils/types";
import { isKnownUser, USER_COOKIE, USERS } from "@/utils/users";

import { listGroups } from "./api";

type SearchParams = { [key: string]: string | string[] | undefined };

export type Selection = {
  user: string;
  groups: ApiResult<GroupSummary[]>;
  /** The selected group, or null when the user has none (or they failed to load). */
  groupId: number | null;
};

export async function selectionFrom(searchParams: Promise<SearchParams>): Promise<Selection> {
  const [params, cookieStore] = await Promise.all([searchParams, cookies()]);
  const selection = await resolve(cookieStore.get(USER_COOKIE)?.value, first(params.group));
  // When the API fails the right group is unknown, so the URL is left alone.
  if (selection.groups.ok && !urlMatches(params, selection.groupId)) {
    redirect(selection.groupId === null ? "/" : `/?group=${selection.groupId}`);
  }
  return selection;
}

/** The URL names exactly the group on screen: /?group=1, or / when there is none. */
function urlMatches(params: SearchParams, groupId: number | null): boolean {
  const keys = Object.keys(params);
  if (groupId === null) {
    return keys.length === 0;
  }
  return keys.length === 1 && params.group === String(groupId);
}

// Cached per request: the header and the main view both resolve the same selection.
const resolve = cache(async (savedUser?: string, groupParam?: string): Promise<Selection> => {
  const user = isKnownUser(savedUser) ? savedUser : USERS[0];
  const groups = await listGroups(user);
  const ids = groups.ok ? groups.data.map((group) => group.id) : [];
  const requested = Number(groupParam);
  // Fall back to the user's first group if none is requested or it is not theirs.
  const groupId = ids.includes(requested) ? requested : (ids[0] ?? null);
  return { user, groups, groupId };
});

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}
