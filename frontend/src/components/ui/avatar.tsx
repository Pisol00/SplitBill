const sizes = {
  md: "h-7 w-7 text-xs",
  lg: "h-11 w-11 text-base",
};

// A member's initial in a circle. Decorative: the name is always shown beside it.
export function Avatar({ name, size = "md" }: { name: string; size?: keyof typeof sizes }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-accent-soft font-semibold uppercase text-accent ${sizes[size]}`}
    >
      {name.slice(0, 1)}
    </span>
  );
}
