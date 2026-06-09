"use client";

import { useState } from "react";

export function ProfileAvatar({
  photoUrl,
  name,
  className = "h-16 w-16",
}: {
  photoUrl?: string | null;
  name: string;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  const src = photoUrl && !failed ? photoUrl : null;
  const initial = name.trim().charAt(0).toUpperCase();

  if (!src) {
    return (
      <div
        className={`flex items-center justify-center overflow-hidden rounded-full bg-bg-elevated ring-2 ring-accent/30 ${className}`}
      >
        <span className="text-2xl font-semibold text-text-muted">{initial || "👤"}</span>
      </div>
    );
  }

  return (
    <div
      className={`overflow-hidden rounded-full bg-bg-elevated ring-2 ring-accent/30 ${className}`}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt=""
        className="h-full w-full object-cover"
        draggable={false}
        onError={() => setFailed(true)}
      />
    </div>
  );
}
