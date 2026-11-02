import { listExpenses } from "@/server/api";
import { requestingUser, respond } from "@/server/route-response";

// The API checks the user and group membership; this handler only forwards.
export async function GET(
  request: Request,
  ctx: RouteContext<"/api/groups/[groupId]/expenses">,
) {
  const { groupId } = await ctx.params;
  return respond(await listExpenses(requestingUser(request), Number(groupId)));
}
