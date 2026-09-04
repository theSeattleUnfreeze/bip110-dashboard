"use client";

type Point = { height: number; share: number };

export function MomentumChart({ points }: { points: Point[] }) {
  if (!points.length) return <p className="text-sm text-muted">No momentum data</p>;
  const w = 600;
  const h = 120;
  const max = Math.max(...points.map((p) => p.share), 55);
  const path = points
    .map((p, i) => {
      const x = (i / (points.length - 1 || 1)) * w;
      const y = h - (p.share / max) * h;
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full rounded border border-border bg-card">
      <line x1="0" y1={h - (55 / max) * h} x2={w} y2={h - (55 / max) * h} stroke="#71717a" strokeDasharray="4" />
      <path d={path} fill="none" stroke="#f59e0b" strokeWidth="2" />
      <text x="4" y="14" className="fill-muted text-[10px]">55% threshold</text>
    </svg>
  );
}
