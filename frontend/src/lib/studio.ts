export interface StudioArtItem {
  id: string;
  imageUrl: string;
}

export interface StudioModel {
  id: string;
  name: string;
  imageUrl?: string | null;
}

export type AspectRatioId = "1:1" | "2:3" | "3:2";

export interface AspectRatioOption {
  id: AspectRatioId;
  label: string;
  ratioLabel: string;
}

/** Список моделей — превью подставит бэкенд (imageUrl) */
export const STUDIO_MODELS: StudioModel[] = [
  { id: "nebula", name: "Nebula" },
  { id: "bubble", name: "Bubble" },
  { id: "stardust", name: "Stardust" },
  { id: "flat", name: "Flat" },
];

export const ASPECT_RATIOS: AspectRatioOption[] = [
  { id: "1:1", ratioLabel: "1:1", label: "Квадрат" },
  { id: "2:3", ratioLabel: "2:3", label: "Портрет" },
  { id: "3:2", ratioLabel: "3:2", label: "Альбом" },
];

export const STUDIO_PROMPT_MAX = 500;
export const STUDIO_GENERATION_COST = 5;

export const STUDIO_PROMPT_PLACEHOLDER =
  "Пример: Девушка с розовыми волосами в неоновом городе под дождём";
