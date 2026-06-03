"use client";

import { useCallback, useRef, useState } from "react";

const DEFAULT_MS = 500;
const TOUCH_MOUSE_GUARD_MS = 450;

function vibrateShort() {
  if (typeof navigator !== "undefined" && "vibrate" in navigator) {
    navigator.vibrate(12);
  }
}

export function useLongPress(
  onLongPress: () => void,
  onShortPress?: () => void,
  delayMs = DEFAULT_MS
) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const didLongPressRef = useRef(false);
  const touchGestureRef = useRef(false);
  const shortPressLockRef = useRef(false);
  const [isHolding, setIsHolding] = useState(false);
  const [isTriggered, setIsTriggered] = useState(false);
  const [tapPulse, setTapPulse] = useState(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setIsHolding(false);
  }, []);

  const resetTriggered = useCallback(() => {
    setIsTriggered(false);
  }, []);

  const fireShortPress = useCallback(() => {
    if (!onShortPress || shortPressLockRef.current) return;
    shortPressLockRef.current = true;
    onShortPress();
    window.setTimeout(() => {
      shortPressLockRef.current = false;
    }, TOUCH_MOUSE_GUARD_MS);
  }, [onShortPress]);

  const start = useCallback(() => {
    didLongPressRef.current = false;
    setTapPulse(false);
    setIsTriggered(false);
    clearTimer();
    setIsHolding(true);
    timerRef.current = setTimeout(() => {
      didLongPressRef.current = true;
      setIsHolding(false);
      setIsTriggered(true);
      vibrateShort();
      onLongPress();
      window.setTimeout(resetTriggered, 280);
    }, delayMs);
  }, [clearTimer, delayMs, onLongPress, resetTriggered]);

  const end = useCallback(() => {
    const wasLong = didLongPressRef.current;
    clearTimer();
    if (!wasLong) {
      setTapPulse(true);
      window.setTimeout(() => setTapPulse(false), 200);
      fireShortPress();
    }
  }, [clearTimer, fireShortPress]);

  const onTouchStart = useCallback(() => {
    touchGestureRef.current = true;
    start();
  }, [start]);

  const onTouchEnd = useCallback(() => {
    end();
    window.setTimeout(() => {
      touchGestureRef.current = false;
    }, TOUCH_MOUSE_GUARD_MS);
  }, [end]);

  const onMouseDown = useCallback(() => {
    if (touchGestureRef.current) return;
    start();
  }, [start]);

  const onMouseUp = useCallback(() => {
    if (touchGestureRef.current) return;
    end();
  }, [end]);

  const onMouseLeave = useCallback(() => {
    if (touchGestureRef.current) return;
    clearTimer();
  }, [clearTimer]);

  const suppressClick = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (didLongPressRef.current) {
      didLongPressRef.current = false;
    }
  }, []);

  return {
    isHolding,
    isTriggered,
    tapPulse,
    holdDurationMs: delayMs,
    onTouchStart,
    onTouchEnd,
    onTouchCancel: onTouchEnd,
    onMouseDown,
    onMouseUp,
    onMouseLeave,
    suppressClick,
  };
}
