"use client";

import type { FC, SVGProps } from "react";

type DoodleSpec = {
  Icon: FC<SVGProps<SVGSVGElement>>;
  top: string;
  left: string;
  size: number;
  rotate: number;
  opacity?: number;
};

const stroke = "currentColor";

function StarIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M12 3l2.2 5.5L20 9.5l-4.5 3.8 1.4 5.7L12 16.2 7.1 19l1.4-5.7L4 9.5l5.8-1L12 3z" />
    </svg>
  );
}

function HeartIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M12 20s-6.5-4.2-8.5-8.2C1.8 8.2 4.2 5 7.5 5c1.8 0 3.2 1 4.5 2.4C13.3 6 14.7 5 16.5 5 19.8 5 22.2 8.2 20.5 11.8 18.5 15.8 12 20 12 20z" />
    </svg>
  );
}

function MoonIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M20 14.5A8.5 8.5 0 019.5 4 10 10 0 1020 14.5z" />
    </svg>
  );
}

function CloudIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M7 18h11a4 4 0 000-8 5 5 0 00-9.6-1.2A3.5 3.5 0 007 18z" />
    </svg>
  );
}

function PlaneIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M3 12l18-7-7 18-2-7-7-2z" strokeLinejoin="round" />
    </svg>
  );
}

function SparkleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8" strokeLinecap="round" />
    </svg>
  );
}

function FlowerIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.3" {...props}>
      <circle cx="12" cy="12" r="2" />
      <path d="M12 4v3M12 17v3M4 12h3M17 12h3M6.3 6.3l2.1 2.1M15.6 15.6l2.1 2.1M6.3 17.7l2.1-2.1M15.6 8.4l2.1-2.1" strokeLinecap="round" />
    </svg>
  );
}

function CatIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M6 10V7l2-3 2 2 2-2 2 3v3M5 14a7 7 0 1014 0 7 7 0 00-14 0z" />
      <circle cx="9" cy="13" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="15" cy="13" r="0.8" fill="currentColor" stroke="none" />
    </svg>
  );
}

function GemIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M4 9l8-5 8 5-8 11-8-11zM4 9h16" />
    </svg>
  );
}

function BubbleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M5 18l-2 3 3-1.5A9 9 0 1120 10.5 9 9 0 015 18z" />
    </svg>
  );
}

function MusicIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M9 18V6l10-2v12" />
      <circle cx="7" cy="18" r="2" />
      <circle cx="17" cy="16" r="2" />
    </svg>
  );
}

function PlanetIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <circle cx="12" cy="12" r="5" />
      <path d="M4 14c4-6 12-6 16 0" />
    </svg>
  );
}

function WandIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.4" {...props}>
      <path d="M4 20L16 8M14 6l4-2 2 4-2 2-4 2 2-4-2-2 4z" strokeLinejoin="round" />
    </svg>
  );
}

const DOODLES: DoodleSpec[] = [
  { Icon: StarIcon, top: "6%", left: "8%", size: 34, rotate: -15, opacity: 0.09 },
  { Icon: HeartIcon, top: "12%", left: "78%", size: 30, rotate: 12, opacity: 0.08 },
  { Icon: MoonIcon, top: "22%", left: "52%", size: 36, rotate: -8, opacity: 0.07 },
  { Icon: CloudIcon, top: "34%", left: "12%", size: 40, rotate: 6, opacity: 0.075 },
  { Icon: PlaneIcon, top: "28%", left: "88%", size: 32, rotate: -22, opacity: 0.085 },
  { Icon: SparkleIcon, top: "45%", left: "68%", size: 28, rotate: 10, opacity: 0.08 },
  { Icon: FlowerIcon, top: "52%", left: "22%", size: 32, rotate: -18, opacity: 0.07 },
  { Icon: CatIcon, top: "58%", left: "84%", size: 38, rotate: 14, opacity: 0.075 },
  { Icon: GemIcon, top: "68%", left: "6%", size: 30, rotate: 8, opacity: 0.08 },
  { Icon: BubbleIcon, top: "72%", left: "44%", size: 36, rotate: -6, opacity: 0.07 },
  { Icon: MusicIcon, top: "78%", left: "72%", size: 34, rotate: -12, opacity: 0.085 },
  { Icon: PlanetIcon, top: "84%", left: "18%", size: 32, rotate: 20, opacity: 0.075 },
  { Icon: WandIcon, top: "38%", left: "36%", size: 28, rotate: -25, opacity: 0.065 },
  { Icon: StarIcon, top: "88%", left: "56%", size: 26, rotate: 5, opacity: 0.07 },
  { Icon: HeartIcon, top: "4%", left: "42%", size: 24, rotate: 18, opacity: 0.065 },
  { Icon: SparkleIcon, top: "48%", left: "4%", size: 26, rotate: -10, opacity: 0.075 },
];

/** Telegram-style outline doodles over the app gradient (non-interactive). */
export function AppBackground() {
  return (
    <div
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden text-accent-light"
      aria-hidden
    >
      {DOODLES.map(({ Icon, top, left, size, rotate, opacity }, i) => (
        <div
          key={i}
          className="absolute"
          style={{
            top,
            left,
            width: size,
            height: size,
            opacity: opacity ?? 0.08,
            transform: `rotate(${rotate}deg)`,
          }}
        >
          <Icon width={size} height={size} />
        </div>
      ))}
    </div>
  );
}
