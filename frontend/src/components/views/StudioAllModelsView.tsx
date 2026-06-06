"use client";

import { BackButton } from "@/components/shared/BackButton";
import { useNavStore } from "@/store/nav-store";
import { ALL_STUDIO_MODELS } from "@/lib/studio";
import { CHAT_BORDER } from "@/lib/theme";
import { cn } from "@/lib/utils";

export function StudioAllModelsView() {
  const goBack = useNavStore((s) => s.goBack);
  const setStudioModelId = useNavStore((s) => s.setStudioModelId);
  const selectedId = useNavStore((s) => s.studioModelId);

  const handleSelect = (modelId: string) => {
    setStudioModelId(modelId);
    goBack();
  };

  return (
    <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
      <header className="mb-6 flex items-center gap-2">
        <BackButton onClick={goBack} />
        <h1 className="flex-1 text-center text-lg font-bold pr-9">Все модели</h1>
      </header>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {ALL_STUDIO_MODELS.map((model) => {
          const selected = selectedId === model.id;
          return (
            <button
              key={model.id}
              type="button"
              onClick={() => handleSelect(model.id)}
              className="flex flex-col items-center gap-2 text-left transition-transform active:scale-[0.97]"
            >
              <div
                className={cn(
                  "flex aspect-square w-full max-w-[7rem] items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br from-accent-deep/80 to-accent/40",
                  selected && "ring-2 ring-pink-400 ring-offset-2 ring-offset-bg-base"
                )}
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
            </button>
          );
        })}
      </div>
    </div>
  );
}
