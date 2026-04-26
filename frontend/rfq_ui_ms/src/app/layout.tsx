import type { Metadata } from "next";
import { IBM_Plex_Sans, JetBrains_Mono, Outfit } from "next/font/google";

import "./globals.css";

import { appConfig } from "@/config/app";
import { AppShellProvider } from "@/context/app-shell-context";
import { ConnectionProvider } from "@/context/connection-context";
import { RoleProvider } from "@/context/role-context";
import { ThemeProvider } from "@/context/theme-context";
import { ToastProvider } from "@/context/toast-context";

const displayFont = Outfit({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700"],
});

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

const monoFont = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: {
    default: appConfig.name,
    template: `%s | ${appConfig.shortName}`,
  },
  description: appConfig.description,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${displayFont.variable} ${bodyFont.variable} ${monoFont.variable} min-h-screen bg-background text-foreground`}
      >
        <ThemeProvider>
          <ToastProvider>
            <RoleProvider>
              <ConnectionProvider>
                <AppShellProvider>{children}</AppShellProvider>
              </ConnectionProvider>
            </RoleProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
