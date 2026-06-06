"use client";

import { AppBackground } from "@/components/layout/AppBackground";

/** Decorative backdrop for art generation / loading screens. */
export function ArtSceneBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(168, 85, 247, 0.22) 0%, transparent 65%), radial-gradient(ellipse 50% 40% at 20% 80%, rgba(244, 114, 182, 0.12) 0%, transparent 55%)",
        }}
      />
      <div className="absolute inset-0 opacity-90">
        <AppBackground />
      </div>
    </div>
  );
}
