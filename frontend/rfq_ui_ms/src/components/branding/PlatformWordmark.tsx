import { appConfig } from "@/config/app";

export function PlatformWordmark({ className }: { className?: string }) {
  return (
    <div className={className}>
      <div className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {appConfig.shortName}
      </div>
    </div>
  );
}
