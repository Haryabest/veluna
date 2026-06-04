"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const STEPS = [
  "Перевожу промпт на английский…",
  "Отправляю запрос на CivitAI…",
  "Модель генерирует изображение…",
  "Сохраняю результат…",
];

export function StudioGeneratingView() {
  const stepRef = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const el = document.getElementById("gen-step");
    if (!el) return;
    stepRef.current = 0;
    el.textContent = STEPS[0];
    intervalRef.current = setInterval(() => {
      stepRef.current = (stepRef.current + 1) % STEPS.length;
      el.textContent = STEPS[stepRef.current];
    }, 2500);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="mb-8 flex h-28 w-28 items-center justify-center rounded-full"
        style={{
          background: "linear-gradient(135deg, #f9a8d4 0%, #e879f9 50%, #c084fc 100%)",
          boxShadow: "0 0 60px rgba(232, 121, 249, 0.5)",
        }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
        >
          <Sparkles className="h-14 w-14 text-white" strokeWidth={1.5} />
        </motion.div>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-xl font-bold text-text-primary"
      >
        Создаю арт
      </motion.h2>

      <motion.p
        id="gen-step"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mt-3 text-sm text-text-secondary"
      >
        {STEPS[0]}
      </motion.p>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-10 flex gap-1.5"
      >
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="h-2 w-2 rounded-full bg-accent-light"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{
              repeat: Infinity,
              duration: 1.2,
              delay: i * 0.2,
            }}
          />
        ))}
      </motion.div>
    </div>
  );
}
