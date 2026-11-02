import type { ReactNode } from "react";

type CardProps = {
  title?: string;
  description?: ReactNode;
  action?: ReactNode;
  children?: ReactNode;
  className?: string;
};

export function Card({ title, description, action, children, className = "" }: CardProps) {
  return (
    <section
      className={`rounded-lg border border-line bg-surface shadow-sm ${className}`}
    >
      {(title || action) && (
        <header
          className={`flex flex-wrap items-start justify-between gap-x-4 gap-y-3 px-5 pt-5 ${children ? "" : "pb-5"}`}
        >
          <div className="flex min-w-40 flex-1 flex-col gap-0.5">
            {title && (
              <h2 className="text-base font-semibold tracking-tight text-fg">{title}</h2>
            )}
            {description && <p className="text-sm text-fg-muted">{description}</p>}
          </div>
          {action}
        </header>
      )}
      {children && <div className="p-5">{children}</div>}
    </section>
  );
}
