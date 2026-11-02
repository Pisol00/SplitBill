// A member's initial in a circle. Decorative: the name is always shown beside it.
export function Avatar({ name }: { name: string }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-semibold uppercase text-accent"
    >
      {name.slice(0, 1)}
    </span>
  );
}
