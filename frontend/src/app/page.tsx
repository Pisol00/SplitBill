// A Server Component: the static shell (header, layout, loading states) is
// prerendered, and the parts that depend on the URL and the API stream in through
// <Suspense>, as Cache Components requires for request-time data.

import { Suspense } from "react";

import { GroupView } from "@/components/group-view";
import { UserGroupPicker } from "@/components/user-group-picker";
import { selectionFrom } from "@/server/selection";

export default function Page(props: PageProps<"/">) {
  return (
    <div className="min-h-screen">
      <header className="z-30 border-b border-line bg-backdrop backdrop-blur sm:sticky sm:top-0">
        <div className="mx-auto flex max-w-5xl items-center gap-2.5 px-4 py-4 sm:px-6">
          <span
            aria-hidden="true"
            className="flex h-7 w-7 items-center justify-center rounded-sm bg-primary text-sm font-bold text-primary-fg"
          >
            S
          </span>
          <span className="text-base font-semibold tracking-tight text-fg">SplitBill</span>
        </div>
      </header>

      {/* Bottom padding, so the floating button never covers the last row. */}
      <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 pt-8 pb-24 sm:px-6">
        <Suspense fallback={<ViewSkeleton />}>
          <View searchParams={props.searchParams} />
        </Suspense>
      </main>

      <Suspense fallback={<PickerSkeleton />}>
        <Picker searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

type SearchParamsProp = { searchParams: PageProps<"/">["searchParams"] };

async function Picker({ searchParams }: SearchParamsProp) {
  const { user, groups, groupId } = await selectionFrom(searchParams);
  return (
    <UserGroupPicker user={user} groups={groups.ok ? groups.data : []} groupId={groupId} />
  );
}

async function View({ searchParams }: SearchParamsProp) {
  return <GroupView selection={await selectionFrom(searchParams)} />;
}

function PickerSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="fixed right-4 bottom-4 z-30 h-14 w-14 animate-pulse rounded-full bg-surface-muted sm:right-6 sm:bottom-6"
    />
  );
}

function ViewSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading" className="flex flex-col gap-3">
      <div className="h-7 w-48 animate-pulse rounded-sm bg-surface-muted" />
      <div className="h-64 animate-pulse rounded-lg bg-surface-muted" />
    </div>
  );
}
