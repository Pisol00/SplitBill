import { getGroup } from "@/server/api";
import { requestingUser, respond } from "@/server/route-response";

// The API checks the user and group membership; this handler only forwards.
export async function GET(request: Request, ctx: RouteContext<"/api/groups/[groupId]">) {
  const { groupId } = await ctx.params;
  return respond(await getGroup(requestingUser(request), Number(groupId)));
}
