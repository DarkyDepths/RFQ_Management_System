"use client";

import Link from "next/link";
import { ArrowUpDown, CalendarDays, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

import { LifecycleProgressStageBox } from "@/components/rfq/LifecycleProgressStageBox";
import { RFQStatusChip } from "@/components/rfq/RFQStatusChip";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import type { RfqCardModel } from "@/models/manager/rfq";
import { getRfqBlockedSignal } from "@/utils/blocker-signal";

type SortField = "client" | "due" | "status";
type SortDirection = "asc" | "desc";

function sortItems(
  items: RfqCardModel[],
  field: SortField,
  direction: SortDirection,
) {
  const factor = direction === "asc" ? 1 : -1;

  return [...items].sort((left, right) => {
    switch (field) {
      case "client":
        return left.client.localeCompare(right.client) * factor;
      case "status":
        return left.statusLabel.localeCompare(right.statusLabel) * factor;
      case "due":
      default:
        return left.dueDateValue.localeCompare(right.dueDateValue) * factor;
    }
  });
}

export function RFQTable({ items }: { items: RfqCardModel[] }) {
  const [sortField, setSortField] = useState<SortField>("due");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const toggleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }

    setSortField(field);
    setSortDirection("asc");
  };

  const sortedItems = sortItems(items, sortField, sortDirection);

  return (
    <div className="surface-panel overflow-hidden">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border bg-muted/20 px-5 py-4 dark:bg-white/[0.01]">
        <div>
          <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            RFQ Queue
          </div>
          <div className="mt-1 text-base font-medium text-foreground">
            Operational and intelligence-aligned records
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <CalendarDays className="h-4 w-4" />
          Sorted by {sortField.replace("_", " ")}
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">RFQ Detail</TableHead>
            <TableHead>
              <Button onClick={() => toggleSort("client")} size="sm" variant="ghost" className="h-8 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Client
                <ArrowUpDown className="h-3 w-3 ml-1" />
              </Button>
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Status & Intel</TableHead>
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Stage</TableHead>
            <TableHead>
              <Button onClick={() => toggleSort("due")} size="sm" variant="ghost" className="h-8 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Due Date
                <ArrowUpDown className="h-3 w-3 ml-1" />
              </Button>
            </TableHead>
            <TableHead className="text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedItems.map((item, index) => {
            const blockedSignal = getRfqBlockedSignal(item);

            return (
              <motion.tr
                key={item.id}
                animate={{ opacity: 1, y: 0 }}
                initial={{ opacity: 0, y: 14 }}
                transition={{ duration: 0.35, delay: 0.1 + index * 0.03 }}
                className="border-b border-border transition-colors hover:bg-muted/40 dark:hover:bg-white/[0.03]"
              >
              <TableCell className="py-4">
                <div>
                  <div className="font-semibold text-foreground">{item.title}</div>
                  <div className="mt-1 font-mono text-[0.68rem] text-muted-foreground">
                    {item.rfqCode ?? item.id}
                    {item.valueLabel ? ` • ${item.valueLabel}` : ""}
                  </div>
                </div>
              </TableCell>
              <TableCell className="py-4 font-medium">{item.client}</TableCell>
              <TableCell className="py-4">
                <div className="flex flex-col gap-1.5 items-start">
                  <RFQStatusChip status={item.status} />
                  {blockedSignal.isBlocked ? (
                    <Badge variant="rose">Blocked</Badge>
                  ) : null}
                  {item.intelligenceState ? (
                    <div className="text-[0.68rem] font-medium text-muted-foreground">
                      Intel: {item.intelligenceState}
                    </div>
                  ) : null}
                </div>
              </TableCell>
              <TableCell className="py-4">
                <LifecycleProgressStageBox
                  blocked={blockedSignal.isBlocked}
                  compact
                  rfqProgress={item.rfqProgress}
                  stageLabel={item.stageLabel}
                  status={item.status}
                />
                <div className="mt-2 text-xs text-muted-foreground">
                  {item.nextAction ?? `Lifecycle ${item.rfqProgress}%`}
                </div>
                {blockedSignal.isBlocked ? (
                  <div className="mt-1 text-[0.68rem] font-medium text-rose-700 dark:text-rose-300">
                    {blockedSignal.reasonLabel
                      ? `Blocked: ${blockedSignal.reasonLabel}`
                      : "Blocked"}
                  </div>
                ) : null}
              </TableCell>
              <TableCell className="py-4 font-mono text-sm">{item.dueLabel}</TableCell>
              <TableCell className="py-4 text-right">
                <Button asChild size="sm" variant="secondary">
                  <Link href={`/rfqs/${item.id}`}>
                    Open
                    <ChevronRight className="h-3.5 w-3.5 ml-1" />
                  </Link>
                </Button>
              </TableCell>
              </motion.tr>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
