"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { getRfqDetail } from "@/connectors/manager/rfqs";
import { useRole } from "@/context/role-context";
import { getRfqBusinessIdentity } from "@/lib/rfq-display";
import type { BreadcrumbItem } from "@/models/ui/dashboard";

const STATIC_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  overview: "Overview",
  new: "Create RFQ",
};

export function useBreadcrumbs(): BreadcrumbItem[] {
  const pathname = usePathname();
  const { role } = useRole();
  const segments = pathname.split("/").filter(Boolean);
  const [rfqIdentityLabel, setRfqIdentityLabel] = useState<string | null>(null);

  const rfqDetailSegment =
    segments.length === 2 && segments[0] === "rfqs" && segments[1] !== "new"
      ? segments[1]
      : null;

  const labels: Record<string, string> = {
    ...STATIC_LABELS,
    rfqs: role === "executive" ? "RFQ Monitor" : "RFQ Queue",
  };

  useEffect(() => {
    if (!rfqDetailSegment) {
      setRfqIdentityLabel(null);
      return;
    }

    let active = true;
    setRfqIdentityLabel(null);

    async function loadRfqIdentity() {
      const rfqId = rfqDetailSegment;
      if (!rfqId) {
        return;
      }

      try {
        const rfq = await getRfqDetail(rfqId);

        if (!active || !rfq) {
          return;
        }

        setRfqIdentityLabel(getRfqBusinessIdentity(rfq));
      } catch {
        if (active) {
          setRfqIdentityLabel(null);
        }
      }
    }

    void loadRfqIdentity();

    return () => {
      active = false;
    };
  }, [rfqDetailSegment]);

  if (segments.length === 0) {
    return [{ label: "Overview", href: "/overview", isCurrent: true }];
  }

  const breadcrumbs: BreadcrumbItem[] = [];
  let currentHref = "";

  segments.forEach((segment, index) => {
    currentHref += `/${segment}`;
    const isRfqDetailSegment = segment === rfqDetailSegment;
    breadcrumbs.push({
      label:
        isRfqDetailSegment
          ? rfqIdentityLabel ?? "RFQ Detail"
          : labels[segment] ?? segment.replace(/-/g, " ").toUpperCase(),
      href: currentHref,
      isCurrent: index === segments.length - 1,
    });
  });

  return breadcrumbs;
}
