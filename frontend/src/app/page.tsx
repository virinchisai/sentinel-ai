"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getMe } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    getMe()
      .then((u) => router.push(u?.id ? "/chat" : "/login"))
      .catch(() => router.push("/login"));
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-[var(--muted)]">Loading...</div>
    </div>
  );
}
