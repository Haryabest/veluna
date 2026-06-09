"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSetTab } from "@/hooks/use-catalog-navigation";

/** Redirect legacy routes to main shell with correct tab */
export function TabRedirect({ tab }: { tab: "studio" | "profile" | "chats" | "home" }) {
  const router = useRouter();
  const setTab = useSetTab();

  useEffect(() => {
    setTab(tab);
    router.replace("/");
  }, [tab, setTab, router]);

  return null;
}
