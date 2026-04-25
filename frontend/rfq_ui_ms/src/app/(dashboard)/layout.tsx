import { CopilotDrawer } from "@/components/copilot/CopilotDrawer";
import { AppShell } from "@/components/layout/AppShell";
import { CopilotProvider } from "@/context/copilot-context";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <CopilotProvider>
      <AppShell>{children}</AppShell>
      <CopilotDrawer />
    </CopilotProvider>
  );
}
