"use client";

import { BackButton } from "@/components/shared/BackButton";
import { useNavStore } from "@/store/nav-store";
import { ALL_STUDIO_MODELS } from "@/lib/studio";
import { CHAT_BORDER } from "@/lib/theme";

export function StudioAllModelsView() {
  const goBack = useNavStore((s) => s.goBack);

  return (
    <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
      <header className="mb-6 flex items-center gap-2">
        <BackButton onClick={goBack} />
        <h1 className="flex-1 text-center text-lg font-bold pr-9">Все модели</h1>
      </header>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {ALL_STUDIO_MODELS.map((model) => (
          <div key={model.id} className="flex flex-col items-center gap-2">
            <div
              className="flex aspect-square w-full max-w-[7rem] items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br from-accent-deep/80 to-accent/40"
              style={{ border: `1px solid ${CHAT_BORDER}` }}
            >
              {model.imageUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={model.imageUrl} alt="" className="h-full w-full object-cover" />
              ) : (
                <span className="text-2xl font-bold text-white/90">{model.name.charAt(0)}</span>
              )}
            </div>
            <span className="line-clamp-2 text-center text-xs font-medium text-text-secondary">
              {model.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
