"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { isProfileAvatarProxy } from "@/lib/profile-avatar";

export function ProfileAvatar({
  photoUrl,
  name,
  className = "h-16 w-16",
}: {
  photoUrl?: string | null;
  name: string;
  className?: string;
}) {
  const [displaySrc, setDisplaySrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    setFailed(false);

    if (!photoUrl) {
      setDisplaySrc(null);
      return;
    }

    if (!isProfileAvatarProxy(photoUrl)) {
      setDisplaySrc(photoUrl);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const { data } = await apiClient.get<Blob>("/users/me/avatar", {
          responseType: "blob",
        });
        if (cancelled) return;
        objectUrl = URL.createObjectURL(data);
        setDisplaySrc(objectUrl);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [photoUrl]);

  const initial = name.trim().charAt(0).toUpperCase();
  const src = displaySrc && !failed ? displaySrc : null;

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
