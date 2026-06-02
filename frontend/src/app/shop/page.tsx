"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useNavStore } from "@/store/nav-store";

export default function ShopPage() {
  const router = useRouter();
  const openShop = useNavStore((s) => s.openShop);

  useEffect(() => {
    openShop();
    router.replace("/");
  }, [openShop, router]);

  return null;
}
