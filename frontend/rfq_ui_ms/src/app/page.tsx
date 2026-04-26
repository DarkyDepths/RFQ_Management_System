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
    <div className="flex h-[60vh] items-center justify-center">
      
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted-foreground/20 border-t-primary" />
    </div>
  );
}
