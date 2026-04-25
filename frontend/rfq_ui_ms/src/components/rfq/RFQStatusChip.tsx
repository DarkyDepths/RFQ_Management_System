"use client";

import { motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { getRfqStatusMeta } from "@/lib/rfq-status-display";
import type { ManagerRfqStatus } from "@/models/manager/rfq";

export function RFQStatusChip({ status }: { status: ManagerRfqStatus }) {
  const meta = getRfqStatusMeta(status);

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      initial={{ opacity: 0.6, y: 6 }}
      transition={{ duration: 0.24 }}
    >
      <Badge variant={meta.tone}>{meta.label}</Badge>
    </motion.div>
  );
}
