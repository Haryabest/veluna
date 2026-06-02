"use client";

import { useId } from "react";

export function AnimeGemIcon({ className = "h-5 w-5" }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  const body = `gem-body-${id}`;
  const shine = `gem-shine-${id}`;

  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <defs>
        <linearGradient id={body} x1="4" y1="2" x2="20" y2="22" gradientUnits="userSpaceOnUse">
          <stop stopColor="#e0c3ff" />
          <stop offset="0.45" stopColor="#a855f7" />
          <stop offset="1" stopColor="#6b21a8" />
        </linearGradient>
        <linearGradient id={shine} x1="8" y1="4" x2="14" y2="14" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fff" stopOpacity="0.85" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d="M12 2.5L3.5 9.5 12 21.5 20.5 9.5 12 2.5z"
        fill={`url(#${body})`}
        stroke="#c77dff"
        strokeWidth="0.75"
        strokeLinejoin="round"
      />
      <path d="M3.5 9.5h17" stroke="#d8b4fe" strokeWidth="0.6" strokeOpacity="0.7" />
      <path
        d="M12 2.5L8 9.5 12 21.5 16 9.5 12 2.5z"
        fill={`url(#${shine})`}
        opacity="0.55"
      />
      <path
        d="M9.5 9.5L12 6l2.5 3.5"
        stroke="#fff"
        strokeWidth="0.5"
        strokeLinecap="round"
        strokeOpacity="0.5"
      />
    </svg>
  );
}

export function AnimeHeartIcon({ className = "h-5 w-5" }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  const body = `heart-body-${id}`;
  const shine = `heart-shine-${id}`;

  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <defs>
        <linearGradient id={body} x1="4" y1="4" x2="20" y2="20" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f0abfc" />
          <stop offset="0.5" stopColor="#e879f9" />
          <stop offset="1" stopColor="#a855f7" />
        </linearGradient>
        <linearGradient id={shine} x1="6" y1="5" x2="12" y2="12" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fff" stopOpacity="0.7" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d="M12 20.5s-7.5-4.8-7.5-10.2C4.5 7.2 6.8 5 9.5 5c1.6 0 2.9.8 3.5 2 0.6-1.2 1.9-2 3.5-2 2.7 0 5 2.2 5 5.3 0 5.4-7.5 10.2-7.5 10.2z"
        fill={`url(#${body})`}
        stroke="#f0abfc"
        strokeWidth="0.75"
        strokeLinejoin="round"
      />
      <ellipse cx="9" cy="9.5" rx="2.2" ry="1.6" fill={`url(#${shine})`} opacity="0.65" />
    </svg>
  );
}
