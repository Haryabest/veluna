export interface StudioArtItem {
  id: string;
  imageUrl: string;
}

export interface StudioModel {
  id: string;
  name: string;
  imageUrl: string;
}

export type AspectRatioId = "1:1" | "2:3" | "3:2";

export interface AspectRatioOption {
  id: AspectRatioId;
  label: string;
  ratioLabel: string;
}

export const STUDIO_GALLERY: StudioArtItem[] = [
  { id: "1", imageUrl: "https://picsum.photos/seed/studio-art-1/400/400" },
  { id: "2", imageUrl: "https://picsum.photos/seed/studio-art-2/400/400" },
  { id: "3", imageUrl: "https://picsum.photos/seed/studio-art-3/400/400" },
  { id: "4", imageUrl: "https://picsum.photos/seed/studio-art-4/400/400" },
];

export const STUDIO_MODELS: StudioModel[] = [
  { id: "nebula", name: "Nebula", imageUrl: "https://picsum.photos/seed/model-nebula/120/120" },
  { id: "bubble", name: "Bubble", imageUrl: "https://picsum.photos/seed/model-bubble/120/120" },
  { id: "stardust", name: "Stardust", imageUrl: "https://picsum.photos/seed/model-stardust/120/120" },
  { id: "flat", name: "Flat", imageUrl: "https://picsum.photos/seed/model-flat/120/120" },
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
