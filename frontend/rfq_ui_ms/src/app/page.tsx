"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useRole } from "@/context/role-context";

export default function HomePage() {
  const { role } = useRole();
  const router = useRouter();

  useEffect(() => {
    if (role === "executive") {
      router.replace("/dashboard");
    } else {
      router.replace("/overview");
    }
  }, [role, router]);

  return (
    <div className="flex min-h-[60dvh] items-center justify-center">
      <div className="relative">
        <div className="absolute inset-0 rounded-full bg-primary/10 blur-2xl animate-breathe" />
        <div className="relative h-10 w-10 animate-spin rounded-full border-2 border-border border-t-primary" />
      </div>
    </div>
  );
}
