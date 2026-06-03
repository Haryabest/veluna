"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useNavStore } from "@/store/nav-store";

/** Legacy URL → shell with history screen */
export default function HistoryPage() {
  const router = useRouter();
  const openHistory = useNavStore((s) => s.openHistory);

  useEffect(() => {
    openHistory();
    router.replace("/");
  }, [openHistory, router]);

  return null;
}
