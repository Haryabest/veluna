export interface StudioArtItem {
  id: string;
  imageUrl: string;
}

export type StudioProvider = "zimage" | "civitai";

export interface StudioModel {
  id: string;
  /** English identifier used on the wire and in generation metadata. */
  name: string;
  /** Russian label shown in the UI. */
  nameRu: string;
  /** Short RU description / flavor text for the picker. */
  descriptionRu: string;
  imageUrl?: string | null;
  /** Identifier sent to the backend (Civitai version id or Z-Image model slug). */
  civitaiModelId: string;
  /** Backend provider used to actually render this model. */
  provider: StudioProvider;
  /**
   * Full English prompt template. The user's text replaces the {USER_INPUT}
   * placeholder (and is wrapped into the surrounding style description).
   */
  promptTemplate: string;
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

/* ------------------------------------------------------------------ *
 * 10 anime art styles. Each one becomes a selectable model in the UI.
 * The {USER_INPUT} token is where the user's prompt gets spliced in.
 * ------------------------------------------------------------------ */
export const ANIME_STYLE_PROMPTS: Record<string, string> = {
  "cyberpunk-neon":
    "2D anime art style, cyberpunk aesthetic. {USER_INPUT}, neon lighting, glowing cybernetic details, futuristic techwear clothing, holographic interfaces. Flat vector illustrations, sharp line art, vivid high-contrast colors, cell-shading, completely non-photorealistic, digital 2D masterpiece.",
  "ghibli-magic":
    "Classic 2D anime illustration, Studio Ghibli aesthetic, hand-drawn vintage style. {USER_INPUT}, soft watercolor textures, nostalgic pastel colors, detailed hand-painted background, warm natural lighting. Flat coloring, traditional animation look, zero realism, beautiful painted 2D art.",
  "dark-fantasy":
    "Dark shonen anime art style, gothic dark fantasy. {USER_INPUT}, heavy shadows, dramatic high-contrast lighting, ink-sketched lines, gritty atmosphere, magical aura. Flat 2D vector graphic, sharp contours, non-photorealistic textures, classic dark anime aesthetics.",
  "kawaii-pastel":
    "Cute slice-of-life anime art, kawaii aesthetic. {USER_INPUT}, pastel color palette, soft flat shading, thick clean outlines, sparkling big anime eyes, cheerful and bright atmosphere. 2D vector drawing, minimal gradients, absolutely no photo textures, clean 2D pop-art.",
  "mecha-scifi":
    "Gundam and Evangelion mecha anime style, 90s sci-fi aesthetic. {USER_INPUT}, wearing detailed futuristic pilot suit, metallic armor plates with flat reflections, giant robot parts in background. Crisp line art, cel-shaded animation frame, non-photorealistic 2D graphics.",
  "chibi-pop":
    "Super deformed chibi anime character style, 2D sticker art. {USER_INPUT} with oversized head, tiny body, giant expressive eyes. Bold clean outlines, flat vibrant colors, simple minimalist background, playful pop-art style. Pure 2D graphic illustration, no 3D rendering.",
  "vintage-80s":
    "Retro 1980s anime screencap, vintage cel-animation aesthetic. {USER_INPUT}, slight VHS chromatic aberration, hand-drawn imperfections, muted retro color grading, grainy overlay. Old-school anime line art, flat anime shading, absolute zero modern realism.",
  "genshin-celshade":
    "Modern 2D anime game art style, Genshin anime aesthetic. {USER_INPUT}, crisp vector lines, perfect cell-shading, vibrant gradients, detailed fantasy outfit. Clean digital anime illustration, flat colors with soft highlights, non-photorealistic, high-quality 2D render.",
  "vaporwave-lofi":
    "Lo-Fi anime aesthetic, vaporwave art style. {USER_INPUT}, purple and pink neon color scheme, nostalgic retro-futurism background, relaxed mood. Flat 2D anime graphics, clean contours, glitch art elements, non-photorealistic vector drawing.",
  "shojo-romance":
    "Classic shojo manga anime illustration, romantic aesthetic. {USER_INPUT}, sparkling eyes, beautiful flowing hair, floating flower petals, soft glowing background. Delicate line art, flat watercolor-like shading, non-photorealistic, ethereal 2D anime artwork.",
};

export const ANIME_STYLE_NAMES_RU: Record<string, string> = {
  "cyberpunk-neon": "Киберпанк",
  "ghibli-magic": "Уютная классика",
  "dark-fantasy": "Мрачное фэнтези",
  "kawaii-pastel": "Милая повседневность",
  "mecha-scifi": "Роботы и броня",
  "chibi-pop": "Мини-персонажи / Стикеры",
  "vintage-80s": "Ретро-аниме",
  "genshin-celshade": "Игровой стиль",
  "vaporwave-lofi": "Расслабленный ретро-вейв",
  "shojo-romance": "Романтика / Сверкающий стиль",
};

export const ANIME_STYLE_DESCRIPTIONS_RU: Record<string, string> = {
  "cyberpunk-neon": "Неон, кибердетали и техно-одежда будущего",
  "ghibli-magic": "Тёплый ручной рисунок в духе студии Гибли",
  "dark-fantasy": "Готика, тени и мрачная магическая атмосфера",
  "kawaii-pastel": "Пастель, большие глаза и уют каждый день",
  "mecha-scifi": "Пилот, мех-броня и гигантские роботы",
  "chibi-pop": "Мини-персонаж для стикеров и поп-арта",
  "vintage-80s": "VHS-плёнка и старое цел-аниме из 80-х",
  "genshin-celshade": "Современный игровой арт с идеальной шейдингом",
  "vaporwave-lofi": "Розово-фиолетовый вейв и чилл-вайб",
  "shojo-romance": "Сёдзо-романтика с лепестками и сиянием",
};

export const ZIMAGE_MODEL_SLUG = "z-image";

export const STUDIO_MODELS: StudioModel[] = [
  {
    id: "cyberpunk-neon",
    name: "Cyberpunk Neon",
    nameRu: ANIME_STYLE_NAMES_RU["cyberpunk-neon"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["cyberpunk-neon"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["cyberpunk-neon"],
    imageUrl: modelThumb("cyberpunk-neon"),
  },
  {
    id: "ghibli-magic",
    name: "Ghibli Magic",
    nameRu: ANIME_STYLE_NAMES_RU["ghibli-magic"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["ghibli-magic"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["ghibli-magic"],
    imageUrl: modelThumb("ghibli-magic"),
  },
  {
    id: "dark-fantasy",
    name: "Dark Fantasy",
    nameRu: ANIME_STYLE_NAMES_RU["dark-fantasy"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["dark-fantasy"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["dark-fantasy"],
    imageUrl: modelThumb("dark-fantasy"),
  },
  {
    id: "kawaii-pastel",
    name: "Kawaii Pastel",
    nameRu: ANIME_STYLE_NAMES_RU["kawaii-pastel"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["kawaii-pastel"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["kawaii-pastel"],
    imageUrl: modelThumb("kawaii-pastel"),
  },
  {
    id: "mecha-scifi",
    name: "Mecha Sci-Fi",
    nameRu: ANIME_STYLE_NAMES_RU["mecha-scifi"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["mecha-scifi"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["mecha-scifi"],
    imageUrl: modelThumb("mecha-scifi"),
  },
  {
    id: "chibi-pop",
    name: "Chibi Pop",
    nameRu: ANIME_STYLE_NAMES_RU["chibi-pop"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["chibi-pop"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["chibi-pop"],
    imageUrl: modelThumb("chibi-pop"),
  },
  {
    id: "vintage-80s",
    name: "Vintage 80s",
    nameRu: ANIME_STYLE_NAMES_RU["vintage-80s"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["vintage-80s"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["vintage-80s"],
    imageUrl: modelThumb("vintage-80s"),
  },
  {
    id: "genshin-celshade",
    name: "Genshin Cel-Shading",
    nameRu: ANIME_STYLE_NAMES_RU["genshin-celshade"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["genshin-celshade"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["genshin-celshade"],
    imageUrl: modelThumb("genshin-celshade"),
  },
  {
    id: "vaporwave-lofi",
    name: "Vaporwave Lo-Fi",
    nameRu: ANIME_STYLE_NAMES_RU["vaporwave-lofi"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["vaporwave-lofi"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["vaporwave-lofi"],
    imageUrl: modelThumb("vaporwave-lofi"),
  },
  {
    id: "shojo-romance",
    name: "Shojo Romance",
    nameRu: ANIME_STYLE_NAMES_RU["shojo-romance"],
    descriptionRu: ANIME_STYLE_DESCRIPTIONS_RU["shojo-romance"],
    civitaiModelId: ZIMAGE_MODEL_SLUG,
    provider: "zimage",
    promptTemplate: ANIME_STYLE_PROMPTS["shojo-romance"],
    imageUrl: modelThumb("shojo-romance"),
  },
];

/* Legacy entries (kept for backwards compatibility with old generation rows). */
export const STUDIO_EXTRA_MODELS: StudioModel[] = [
  { id: "sagging-breasts", name: "Sagging Breasts", nameRu: "Sagging Breasts", descriptionRu: "", civitaiModelId: "139131", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("sagging-breasts") },
  { id: "hoseki", name: "Hoseki", nameRu: "Hoseki", descriptionRu: "", civitaiModelId: "941345", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("hoseki") },
  { id: "ai-styles-dump", name: "AI styles dump", nameRu: "AI styles dump", descriptionRu: "", civitaiModelId: "723360", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("ai-styles-dump") },
  { id: "perfectdeliberate-anime", name: "PerfectDeliberate-Anime", nameRu: "PerfectDeliberate-Anime", descriptionRu: "", civitaiModelId: "111274", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("perfectdeliberate-anime") },
  { id: "miaomiao-realskin", name: "MiaoMiao RealSkin", nameRu: "MiaoMiao RealSkin", descriptionRu: "", civitaiModelId: "2026594", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("miaomiao-realskin") },
  { id: "cat-tower", name: "Cat Tower", nameRu: "Cat Tower", descriptionRu: "", civitaiModelId: "920709", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("cat-tower") },
  { id: "nova-anime-xl", name: "Nova Anime XL", nameRu: "Nova Anime XL", descriptionRu: "", civitaiModelId: "2741698", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("nova-anime-xl") },
  { id: "miaomiao", name: "MiaoMiao", nameRu: "MiaoMiao", descriptionRu: "", civitaiModelId: "3004063", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("miaomiao") },
  { id: "velvet-mythic", name: "PerfectDeliberate Anime", nameRu: "PerfectDeliberate Anime", descriptionRu: "", civitaiModelId: "2925672", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("velvet-mythic") },
  { id: "nova-orange-xl", name: "Nova Orange XL", nameRu: "Nova Orange XL", descriptionRu: "", civitaiModelId: "2945776", provider: "civitai", promptTemplate: "{USER_INPUT}", imageUrl: modelThumb("nova-orange-xl") },
];

export const ALL_STUDIO_MODELS: StudioModel[] = [...STUDIO_MODELS, ...STUDIO_EXTRA_MODELS];

export function findStudioModel(modelId: string): StudioModel | undefined {
  return ALL_STUDIO_MODELS.find((m) => m.id === modelId);
}

export function buildStudioPrompt(model: StudioModel, userInput: string): string {
  const trimmed = (userInput || "").trim();
  return model.promptTemplate.replace(/\{USER_INPUT\}/g, trimmed);
}

export const ASPECT_RATIOS: AspectRatioOption[] = [
  { id: "1:1", ratioLabel: "1:1", label: "Квадрат" },
  { id: "2:3", ratioLabel: "2:3", label: "Портрет" },
  { id: "3:2", ratioLabel: "3:2", label: "Альбом" },
];

export const STUDIO_PROMPT_MAX = 500;
export const STUDIO_GENERATION_COST = 5;

export const STUDIO_PROMPT_PLACEHOLDER =
  "Опиши, что должно быть на арте. Например: девушка с розовыми волосами в неоновом городе под дождём";
