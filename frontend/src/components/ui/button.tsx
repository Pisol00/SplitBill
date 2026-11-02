import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "danger-ghost";
type Size = "md" | "sm" | "icon";

const variants: Record<Variant, string> = {
  primary:
    "bg-primary text-primary-fg shadow-xs hover:bg-primary-hover disabled:bg-surface-muted disabled:text-fg-subtle disabled:shadow-none",
  secondary:
    "border border-line-strong bg-surface text-fg shadow-xs hover:bg-surface-hover disabled:opacity-60",
  ghost: "text-fg-muted hover:bg-surface-hover hover:text-fg disabled:opacity-60",
  danger:
    "border border-danger bg-surface text-danger shadow-xs hover:bg-danger-soft disabled:opacity-60",
  "danger-ghost":
    "text-fg-subtle hover:bg-danger-soft hover:text-danger disabled:opacity-60",
};

const sizes: Record<Size, string> = {
  md: "h-10 px-4 text-sm",
  // Larger on touch screens, where a small button is hard to hit.
  sm: "h-10 px-3 text-sm sm:h-8",
  icon: "h-10 w-10 sm:h-8 sm:w-8",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  type = "button",
  ...props
}: Props) {
  return (
    <button
      type={type}
      className={`inline-flex shrink-0 items-center justify-center gap-2 rounded-md font-medium whitespace-nowrap transition-colors duration-150 ease-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    />
  );
}
