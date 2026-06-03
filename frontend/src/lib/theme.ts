/** Dark purple borders for chat UI (no white/light outlines) */
export const CHAT_BORDER = "rgba(90, 50, 130, 0.45)";

export const chatBorderStyle = { border: `1px solid ${CHAT_BORDER}` } as const;

export const chatSeparatorStyle = { borderBottom: `1px solid ${CHAT_BORDER}` } as const;

export const chatSeparatorTopStyle = { borderTop: `1px solid ${CHAT_BORDER}` } as const;

export const chatSeparatorVerticalStyle = { borderLeft: `1px solid ${CHAT_BORDER}` } as const;
