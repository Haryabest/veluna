"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { ArtSceneBackground } from "@/components/shared/ArtSceneBackground";
import { useTranslation } from "@/hooks/use-translation";

export function StudioGeneratingView() {
  const { t } = useTranslation();

  const steps = useMemo(
    () => [
      t("studio.generating.step1"),
      t("studio.generating.step2"),
      t("studio.generating.step3"),
      t("studio.generating.step4"),
    ],
    [t]
  );

  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    setStepIndex(0);
    const interval = setInterval(() => {
      setStepIndex((i) => (i + 1) % steps.length);
    }, 2500);
    return () => clearInterval(interval);
  }, [steps]);

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6">
      <ArtSceneBackground />

      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 mb-8 flex h-28 w-28 items-center justify-center rounded-full"
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
        className="relative z-10 text-xl font-bold text-text-primary"
      >
        {t("studio.generating.title")}
      </motion.h2>

      <motion.p
        key={stepIndex}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="relative z-10 mt-3 text-sm text-text-secondary"
      >
        {steps[stepIndex]}
      </motion.p>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="relative z-10 mt-10 flex gap-1.5"
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
