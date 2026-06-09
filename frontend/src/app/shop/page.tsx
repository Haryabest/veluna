"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useOpenShop } from "@/hooks/use-catalog-navigation";

export default function ShopPage() {
  const router = useRouter();
  const openShop = useOpenShop();

  useEffect(() => {
    openShop();
    router.replace("/");
  }, [openShop, router]);

  return null;
}
