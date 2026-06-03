"use client";

import { useEffect, useState } from "react";

/** Избегает расхождения SSR/клиент (layoutId, persist, Telegram WebApp) */
export function useMounted() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted;
}
