import type { Metadata } from "next";
import Link from "next/link";

import { Card } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Page not found | SplitBill",
};

// The root not-found also handles every URL that matches no route.
export default function NotFound() {
  return (
    <main className="mx-auto flex max-w-xl flex-col px-4 py-16 sm:px-6">
      <Card title="Page not found" description="This page does not exist.">
        <Link
          href="/"
          className="inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-fg hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          Back to SplitBill
        </Link>
      </Card>
    </main>
  );
}
