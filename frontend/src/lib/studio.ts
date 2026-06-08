export interface StudioArtItem {
  id: string;
  imageUrl: string;
}

export interface StudioModel {
  id: string;
  name: string;
  imageUrl?: string | null;
  civitaiModelId: string;
}

export type AspectRatioId = "1:1" | "2:3" | "3:2";

export interface AspectRatioOption {
  id: AspectRatioId;
  label: string;
  ratioLabel: string;
}

function modelThumb(seed: string): string {
  return `https://picsum.photos/seed/veluna-${seed}/256/256`;
}

export const STUDIO_MODELS: StudioModel[] = [
  { id: "nova-anime-xl", name: "Nova Anime XL", civitaiModelId: "2741698", imageUrl: modelThumb("nova-anime-xl") },
  { id: "miaomiao", name: "MiaoMiao", civitaiModelId: "934764", imageUrl: modelThumb("miaomiao") },
  { id: "velvet-mythic", name: "Velvet's Mythic Fantasy Styles", civitaiModelId: "599757", imageUrl: modelThumb("velvet-mythic") },
  { id: "nova-orange-xl", name: "Nova Orange XL", civitaiModelId: "967405", imageUrl: modelThumb("nova-orange-xl") },
];

export const STUDIO_EXTRA_MODELS: StudioModel[] = [
  { id: "sagging-breasts", name: "Sagging Breasts", civitaiModelId: "139131", imageUrl: modelThumb("sagging-breasts") },
  { id: "hoseki", name: "Hoseki", civitaiModelId: "941345", imageUrl: modelThumb("hoseki") },
  { id: "ai-styles-dump", name: "AI styles dump", civitaiModelId: "723360", imageUrl: modelThumb("ai-styles-dump") },
  { id: "perfectdeliberate-anime", name: "PerfectDeliberate-Anime", civitaiModelId: "111274", imageUrl: modelThumb("perfectdeliberate-anime") },
  { id: "miaomiao-realskin", name: "MiaoMiao RealSkin", civitaiModelId: "2026594", imageUrl: modelThumb("miaomiao-realskin") },
  { id: "cat-tower", name: "Cat Tower", civitaiModelId: "920709", imageUrl: modelThumb("cat-tower") },
];

export const ALL_STUDIO_MODELS: StudioModel[] = [...STUDIO_MODELS, ...STUDIO_EXTRA_MODELS];

export function findStudioModel(modelId: string): StudioModel | undefined {
  return ALL_STUDIO_MODELS.find((m) => m.id === modelId);
}

export const ASPECT_RATIOS: AspectRatioOption[] = [
  { id: "1:1", ratioLabel: "1:1", label: "Квадрат" },
  { id: "2:3", ratioLabel: "2:3", label: "Портрет" },
  { id: "3:2", ratioLabel: "3:2", label: "Альбом" },
];

export const STUDIO_PROMPT_MAX = 500;
export const STUDIO_GENERATION_COST = 5;

export const STUDIO_PROMPT_PLACEHOLDER =
  "Пример: Девушка с розовыми волосами в неоновом городе под дождём";
