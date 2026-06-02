"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useNavStore } from "@/store/nav-store";

/** Legacy URL: /characters/[id] → opens overlay on main shell */
export default function CharacterLegacyPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const openCharacter = useNavStore((s) => s.openCharacter);

  useEffect(() => {
    if (id) openCharacter(id);
    router.replace("/");
  }, [id, openCharacter, router]);

  return null;
}
