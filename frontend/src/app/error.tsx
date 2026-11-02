"use client"; // Error boundaries must be Client Components

import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

// Shown when rendering the page throws unexpectedly. Expected API errors (an
// unreachable server, a rejected expense) are returned as values and shown inline.
export default function ErrorPage({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex max-w-xl flex-col px-4 py-16 sm:px-6">
      <Card title="Something went wrong" description="The page could not be displayed.">
        <Button onClick={() => retry()}>Try again</Button>
      </Card>
    </main>
  );
}
