"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, LoaderCircle, UploadCloud, XCircle } from "lucide-react";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { appConfig } from "@/config/app";
import { cn } from "@/lib/utils";

type UploadState = "ready" | "processing" | "missing" | "failed";

function buildDemoUploadFileName(title: string, fileName?: string) {
  if (fileName) {
    const extensionIndex = fileName.lastIndexOf(".");
    if (extensionIndex > 0) {
      const stem = fileName.slice(0, extensionIndex);
      const extension = fileName.slice(extensionIndex);
      return `${stem}_refresh${extension}`;
    }
    return `${fileName}_refresh`;
  }

  if (title.toLowerCase().includes("workbook")) {
    return "demo_pricing_refresh.xlsx";
  }

  return "demo_package_refresh.zip";
}

export function UploadZone({
  title,
  description,
  initialStatus,
  fileName,
  uploadedLabel,
}: {
  title: string;
  description: string;
  initialStatus: UploadState;
  fileName?: string;
  uploadedLabel?: string;
}) {
  const [dragActive, setDragActive] = useState(false);
  const [status, setStatus] = useState<UploadState>(initialStatus);
  const [currentFileName, setCurrentFileName] = useState(fileName);

  useEffect(() => {
    setStatus(initialStatus);
    setCurrentFileName(fileName);
  }, [fileName, initialStatus]);

  const triggerUpload = () => {
    setStatus("processing");
    setCurrentFileName(buildDemoUploadFileName(title, fileName));

    window.setTimeout(() => {
      setStatus("ready");
    }, appConfig.timings.uploadTransitionMs);
  };

  const statusBadge =
    status === "ready" ? (
      <Badge variant="emerald">Ready</Badge>
    ) : status === "processing" ? (
      <Badge variant="steel" className="animate-pulse">Processing</Badge>
    ) : status === "failed" ? (
      <Badge variant="rose">Failed</Badge>
    ) : (
      <Badge variant="pending">Awaiting Upload</Badge>
    );

  return (
    <motion.div
      animate={{
        scale: dragActive ? 1.01 : 1,
      }}
      className={cn(
        "surface-panel surface-panel-hover border-dashed p-6 transition-colors duration-200",
        dragActive && "border-primary bg-primary/5",
      )}
      onDragEnter={() => setDragActive(true)}
      onDragLeave={() => setDragActive(false)}
      onDragOver={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragActive(false);
        triggerUpload();
      }}
    >
      <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
        <div className="flex gap-4">
          <div
            className={cn(
              "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border transition-colors",
              dragActive
                ? "border-primary/30 bg-primary/10"
                : "border-border bg-card dark:bg-white/[0.03]",
            )}
          >
            {status === "processing" ? (
              <LoaderCircle className="h-5 w-5 animate-spin text-primary" />
            ) : status === "failed" ? (
              <XCircle className="h-5 w-5 text-rose-500" />
            ) : status === "ready" ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            ) : (
              <UploadCloud className="h-5 w-5 text-gold-500 dark:text-gold-300" />
            )}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-base font-semibold text-foreground">{title}</h3>
              {statusBadge}
            </div>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted-foreground">
              {description}
            </p>
            <div className="mt-3 inline-block rounded-md bg-muted/50 px-2.5 py-1 font-mono text-xs text-muted-foreground dark:bg-white/[0.03]">
              {currentFileName
                ? `${currentFileName}${uploadedLabel ? ` • ${uploadedLabel}` : ""}`
                : "Drag a file here or trigger a demo upload transition."}
            </div>
          </div>
        </div>

        <Button onClick={triggerUpload} variant="outline" className="w-full shrink-0 md:w-auto">
          {status === "ready" ? "Refresh Demo Upload" : "Simulate Upload"}
        </Button>
      </div>
    </motion.div>
  );
}
