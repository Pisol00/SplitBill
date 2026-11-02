import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "danger-ghost";
type Size = "md" | "sm" | "icon";

const variants: Record<Variant, string> = {
  primary:
    "bg-primary text-primary-fg shadow-xs hover:bg-primary-hover disabled:bg-surface-muted disabled:text-fg-subtle disabled:shadow-none",
  ghost: "text-fg-muted hover:bg-surface-hover hover:text-fg",
  "danger-ghost": "text-fg-subtle hover:bg-danger-soft hover:text-danger",
};

const sizes: Record<Size, string> = {
  md: "h-10 px-4 text-sm",
  sm: "h-8 px-3 text-sm",
  icon: "h-8 w-8",
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
      className={`inline-flex shrink-0 items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 ease-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    />
  );
}
