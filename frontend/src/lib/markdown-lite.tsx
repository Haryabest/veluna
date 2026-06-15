import type { ReactNode } from "react";

const IMAGE_RE = /!\[([^\]]*)\]\(([^)]+)\)/g;

/** Minimal inline markdown: **bold**, *italic*, ![alt](url) images */
export function renderMarkdownLite(text: string, photoAlt = "photo"): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  const pushText = (chunk: string) => {
    if (!chunk) return;
    nodes.push(...renderInlineStyles(chunk, key));
    key += chunk.length;
  };

  while ((match = IMAGE_RE.exec(text)) !== null) {
    pushText(text.slice(lastIndex, match.index));
    const alt = match[1];
    const url = match[2];
    nodes.push(
      <span key={`img-${key++}`} className="mt-1 block">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={url} alt={alt || photoAlt} className="max-w-full rounded-xl object-contain" />
      </span>
    );
    lastIndex = match.index + match[0].length;
  }

  pushText(text.slice(lastIndex));
  return nodes.length ? nodes : [<span key="empty">{text}</span>];
}

function renderInlineStyles(text: string, baseKey: number): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={baseKey + i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2 && !part.startsWith("**")) {
      return <em key={baseKey + i}>{part.slice(1, -1)}</em>;
    }
    return <span key={baseKey + i}>{part}</span>;
  });
}
