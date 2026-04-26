"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";

export function BreadcrumbTrail() {
  const breadcrumbs = useBreadcrumbs();

  return (
    <nav
      aria-label="Breadcrumb"
      className="flex min-w-0 flex-wrap items-center gap-1.5 text-sm text-muted-foreground"
    >
      {breadcrumbs.map((crumb, index) => (
        <div key={crumb.href ?? crumb.label} className="flex min-w-0 items-center gap-1.5">
          {index > 0 ? (
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/40" strokeWidth={2} />
          ) : null}
          {crumb.isCurrent || !crumb.href ? (
            <span className="truncate font-medium text-foreground">{crumb.label}</span>
          ) : (
            <Link
              className="truncate transition-colors hover:text-foreground"
              href={crumb.href}
            >
              {crumb.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  );
}
