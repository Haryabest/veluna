import type { Character } from "@/store/character-store";

export const MOCK_CHARACTERS: Character[] = [
  {
    id: "1",
    name: "Акира",
    slug: "akira",
    subtitle: "Добрая лисичка",
    description:
      "Акира — милая и добрая девушка-лисица, которая всегда рядом, чтобы поддержать тебя и подарить тепло.",
    greeting_message: "Привет! Рада тебя видеть~",
    avatar_url: "https://picsum.photos/seed/akira-avatar/200/200",
    preview_url: "https://picsum.photos/seed/akira/600/800",
    tags: ["Лисичка", "Добрая", "Заботливая"],
    category: "general",
    message_price: 1,
    generation_price: 10,
    is_nsfw: false,
    sort_order: 0,
  },
  {
    id: "2",
    name: "Мирай",
    slug: "mirai",
    subtitle: "Путешественница времени",
    description:
      "Путешественница из будущего. Знает секреты времени и любит рассказывать истории о мирах, которых ещё не существует.",
    greeting_message: "Ночь прекрасна, не правда ли?",
    avatar_url: "https://picsum.photos/seed/mirai-avatar/200/200",
    preview_url: "https://picsum.photos/seed/mirai/600/800",
    tags: ["sci-fi", "загадочная"],
    category: "general",
    message_price: 1,
    generation_price: 10,
    is_nsfw: false,
    sort_order: 1,
  },
  {
    id: "3",
    name: "Луна",
    slug: "luna",
    subtitle: "Лунная принцесса",
    description:
      "Лунная принцесса с мягким голосом и тёплым сердцем. Мечтает о приключениях за пределами своего дворца.",
    greeting_message: "Эй! Погнали тренироваться!",
    avatar_url: "https://picsum.photos/seed/luna-avatar/200/200",
    preview_url: "https://picsum.photos/seed/luna/600/800",
    tags: ["фэнтези", "романтика"],
    category: "general",
    message_price: 1,
    generation_price: 10,
    is_nsfw: false,
    sort_order: 2,
  },
  {
    id: "4",
    name: "Юки",
    slug: "yuki",
    subtitle: "Хранительница тайн",
    description:
      "Тихая библиотекарша с тайной — хранительница древних заклинаний. Открывается только тем, кто умеет слушать.",
    greeting_message: "Шhh... хочешь услышать историю?",
    avatar_url: "https://picsum.photos/seed/yuki-avatar/200/200",
    preview_url: "https://picsum.photos/seed/yuki/600/800",
    tags: ["спокойная", "магия"],
    category: "general",
    message_price: 1,
    generation_price: 10,
    is_nsfw: false,
    sort_order: 3,
  },
];

export interface MockChat {
  id: string;
  characterId: string;
  characterName: string;
  avatarUrl: string;
  /** Full-screen chat background (image or .mp4/.webm video) */
  backgroundUrl?: string;
  preview: string;
  time: string;
  unread?: number;
  isSystem?: boolean;
}

export const MOCK_CHATS: MockChat[] = [
  {
    id: "chat-1",
    characterId: "1",
    characterName: "Акира",
    avatarUrl: "https://picsum.photos/seed/akira-avatar/200/200",
    preview: "Ты сегодня такой милый... 💜",
    time: "12:30",
    unread: 2,
  },
  {
    id: "chat-2",
    characterId: "2",
    characterName: "Мирай",
    avatarUrl: "https://picsum.photos/seed/mirai-avatar/200/200",
    preview: "Я нашла что-то интересное в архивах",
    time: "Вчера",
  },
  {
    id: "chat-3",
    characterId: "3",
    characterName: "Луна",
    avatarUrl: "https://picsum.photos/seed/luna-avatar/200/200",
    preview: "Спокойной ночи ✨",
    time: "Пн",
  },
  {
    id: "chat-4",
    characterId: "0",
    characterName: "Велюна",
    avatarUrl: "https://picsum.photos/seed/veluna-sys/200/200",
    preview: "Добро пожаловать в Veluna!",
    time: "Сб",
    isSystem: true,
  },
];

export interface MockScenario {
  id: string;
  title: string;
  description: string;
  imageUrl: string;
}

export const MOCK_SCENARIOS: MockScenario[] = [
  {
    id: "s1",
    title: "Первая встреча",
    description: "Случайная встреча в академии — начало истории",
    imageUrl: "https://picsum.photos/seed/scenario1/400/240",
  },
  {
    id: "s2",
    title: "Лунная ночь",
    description: "Прогулка под звёздами и откровенный разговор",
    imageUrl: "https://picsum.photos/seed/scenario2/400/240",
  },
  {
    id: "s3",
    title: "Тайное приключение",
    description: "Вместе исследуете забытый храм",
    imageUrl: "https://picsum.photos/seed/scenario3/400/240",
  },
  {
    id: "s4",
    title: "Уютный вечер",
    description: "Чай, книги и тёплая атмосфера",
    imageUrl: "https://picsum.photos/seed/scenario4/400/240",
  },
];

export function getMockCharacter(id: string): Character | undefined {
  return MOCK_CHARACTERS.find((c) => c.id === id || c.slug === id);
}

export function getMockChat(id: string): MockChat | undefined {
  return MOCK_CHATS.find((c) => c.id === id);
}

export interface MockMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  time: string;
}

export const MOCK_MESSAGES: Record<string, MockMessage[]> = {
  "chat-1": [
    { id: "m1", role: "assistant", content: "Привет! Рада тебя видеть~ Как прошёл твой день?", time: "12:28" },
    { id: "m2", role: "user", content: "Привет, Акира! Всё отлично, думал о тебе", time: "12:29" },
    { id: "m3", role: "assistant", content: "Правда?.. Тогда у меня сегодня точно хороший день 💜", time: "12:30" },
    { id: "m4", role: "user", content: "Ты сегодня такой милый...", time: "12:30" },
  ],
  "chat-2": [
    { id: "m1", role: "assistant", content: "Я нашла что-то интересное в архивах времени.", time: "18:00" },
  ],
  "chat-3": [
    { id: "m1", role: "assistant", content: "Спокойной ночи ✨", time: "23:00" },
  ],
  "chat-4": [
    { id: "m1", role: "assistant", content: "Добро пожаловать в Veluna! Выбери персонажа и начни историю.", time: "10:00" },
  ],
};

export function getMockMessages(chatId: string): MockMessage[] {
  return MOCK_MESSAGES[chatId] ?? [];
}
