"use client";

import { useCallback, useRef, type MouseEvent, type TouchEvent } from "react";

interface UseMessageLongPressOptions {
  delay?: number;
  disabled?: boolean;
}

export function useMessageLongPress(
  onLongPress: (clientX: number, clientY: number) => void,
  { delay = 480, disabled = false }: UseMessageLongPressOptions = {}
) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pointRef = useRef({ x: 0, y: 0 });

  const clear = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const start = useCallback(
    (clientX: number, clientY: number) => {
      if (disabled) return;
      pointRef.current = { x: clientX, y: clientY };
      clear();
      timerRef.current = setTimeout(() => {
        onLongPress(pointRef.current.x, pointRef.current.y);
      }, delay);
    },
    [clear, delay, disabled, onLongPress]
  );

  const bind = useCallback(
    () => ({
      onTouchStart: (e: TouchEvent) => {
        const t = e.touches[0];
        if (t) start(t.clientX, t.clientY);
      },
      onTouchEnd: clear,
      onTouchMove: clear,
      onMouseDown: (e: MouseEvent) => {
        if (e.button !== 0) return;
        start(e.clientX, e.clientY);
      },
      onMouseUp: clear,
      onMouseLeave: clear,
      onContextMenu: (e: MouseEvent) => e.preventDefault(),
    }),
    [clear, start]
  );

  return { bind, clear };
}
