// The API has no endpoint that lists users, so the page offers the seeded users
// (backend/alembic/versions/da8d57b826a7_seed_users_and_groups.py).
export const USERS = ["alice", "bob", "carol", "dan"] as const;

/** Remembers which user is selected. It identifies, it does not authenticate. */
export const USER_COOKIE = "splitbill_user";

export function isKnownUser(name: string | undefined): name is (typeof USERS)[number] {
  return (USERS as readonly (string | undefined)[]).includes(name);
}
