const GENERATION_STATUS: Record<string, string> = {
  pending: "В очереди",
  processing: "Генерация…",
  completed: "Готово",
  failed: "Ошибка",
  moderated: "Модерация",
};

export function translateGenerationStatus(status: string): string {
  return GENERATION_STATUS[status] ?? status;
}

export function translateApiError(message: string): string {
  const map: Record<string, string> = {
    "Unknown error": "Неизвестная ошибка",
    "Network Error": "Ошибка сети",
    "Request failed with status code 401": "Сессия истекла",
    "Request failed with status code 403": "Доступ запрещён",
    "Request failed with status code 404": "Не найдено",
    "Request failed with status code 429": "Слишком много запросов",
  };
  return map[message] ?? message;
}
