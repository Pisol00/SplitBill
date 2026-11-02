"use client"; // Error boundaries must be Client Components

import "./globals.css";

// Replaces the root layout when it fails, so it brings its own <html>, <body> and
// styles. metadata exports are not supported here; React's <title> is used instead.
export default function GlobalError({ error, retry }: { error: unknown; retry: () => void }) {
  console.error(error);

  return (
    <html lang="en">
      <body className="min-h-screen bg-canvas font-sans text-fg antialiased">
        <title>Something went wrong | SplitBill</title>
        <main className="mx-auto flex max-w-xl flex-col gap-4 px-4 py-16 sm:px-6">
          <h1 className="text-2xl font-semibold tracking-tight">Something went wrong</h1>
          <p className="text-sm text-fg-muted">SplitBill could not be displayed.</p>
          <button
            type="button"
            onClick={() => retry()}
            className="h-10 self-start rounded-md bg-primary px-4 text-sm font-medium text-primary-fg hover:bg-primary-hover"
          >
            Try again
          </button>
        </main>
      </body>
    </html>
  );
}
