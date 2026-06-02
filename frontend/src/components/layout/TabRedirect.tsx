"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useNavStore } from "@/store/nav-store";

/** Redirect legacy routes to main shell with correct tab */
export function TabRedirect({ tab }: { tab: "studio" | "profile" | "chats" | "home" }) {
  const router = useRouter();
  const setTab = useNavStore((s) => s.setTab);

  useEffect(() => {
    setTab(tab);
    router.replace("/");
  }, [tab, setTab, router]);

  return null;
}
