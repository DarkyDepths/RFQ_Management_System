"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";

export function BreadcrumbTrail() {
  const breadcrumbs = useBreadcrumbs();

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
      {breadcrumbs.map((crumb, index) => (
        <div key={crumb.href ?? crumb.label} className="flex items-center gap-2">
          {index > 0 ? <ChevronRight className="h-4 w-4 text-muted-foreground/40" /> : null}
          {crumb.isCurrent || !crumb.href ? (
            <span className="font-medium text-foreground">{crumb.label}</span>
          ) : (
            <Link className="transition-colors hover:text-foreground" href={crumb.href}>
              {crumb.label}
            </Link>
          )}
        </div>
      ))}
    </div>
  );
}
