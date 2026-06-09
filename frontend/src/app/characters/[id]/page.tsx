"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useOpenCharacter } from "@/hooks/use-catalog-navigation";

/** Legacy URL: /characters/[id] → opens overlay on main shell */
export default function CharacterLegacyPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const openCharacter = useOpenCharacter();

  useEffect(() => {
    if (id) openCharacter(id);
    router.replace("/");
  }, [id, openCharacter, router]);

  return null;
}
