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

export const STUDIO_MODELS: StudioModel[] = [
  { id: "miaomiao", name: "MiaoMiao", civitaiModelId: "934764" },
  { id: "nova-anime-xl", name: "Nova Anime XL", civitaiModelId: "376130" },
  { id: "velvet-mythic", name: "Velvet's Mythic Fantasy Styles", civitaiModelId: "599757" },
  { id: "nova-orange-xl", name: "Nova Orange XL", civitaiModelId: "967405" },
];

export const STUDIO_EXTRA_MODELS: StudioModel[] = [
  { id: "sagging-breasts", name: "Sagging Breasts", civitaiModelId: "139131" },
  { id: "hoseki", name: "Hoseki", civitaiModelId: "941345" },
  { id: "ai-styles-dump", name: "AI styles dump", civitaiModelId: "723360" },
  { id: "perfectdeliberate-anime", name: "PerfectDeliberate-Anime", civitaiModelId: "111274" },
  { id: "miaomiao-realskin", name: "MiaoMiao RealSkin", civitaiModelId: "2026594" },
  { id: "cat-tower", name: "Cat Tower", civitaiModelId: "920709" },
];

export const ALL_STUDIO_MODELS: StudioModel[] = [...STUDIO_MODELS, ...STUDIO_EXTRA_MODELS];

export const ASPECT_RATIOS: AspectRatioOption[] = [
  { id: "1:1", ratioLabel: "1:1", label: "Квадрат" },
  { id: "2:3", ratioLabel: "2:3", label: "Портрет" },
  { id: "3:2", ratioLabel: "3:2", label: "Альбом" },
];

export const STUDIO_PROMPT_MAX = 500;
export const STUDIO_GENERATION_COST = 5;

export const STUDIO_PROMPT_PLACEHOLDER =
  "Пример: Девушка с розовыми волосами в неоновом городе под дождём";
