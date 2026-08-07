"use client";

import { useEffect, useRef } from "react";

type Props = {
  bitsBase64?: string;
  opReturn?: number[];
  from?: number;
};

export function BlockFilmExplorer({ bitsBase64, opReturn, from = 0 }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !bitsBase64) return;
    const raw = Uint8Array.from(atob(bitsBase64), (c) => c.charCodeAt(0));
    const bits: number[] = [];
    for (const byte of raw) {
      for (let i = 0; i < 8; i++) {
        bits.push((byte >> (7 - i)) & 1);
      }
    }
    const w = Math.min(bits.length, 1200);
    const h = 48;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#18181b";
    ctx.fillRect(0, 0, w, h);
    for (let i = 0; i < w; i++) {
      if (bits[i]) {
        ctx.fillStyle = "#f59e0b";
        ctx.fillRect(i, 0, 1, h);
      }
      if (opReturn && opReturn[i] > 83) {
        ctx.fillStyle = `rgba(239,68,68,${Math.min(1, opReturn[i] / 500)})`;
        ctx.fillRect(i, 0, 1, h);
      }
    }
  }, [bitsBase64, opReturn, from]);

  return (
    <div>
      <canvas ref={ref} className="w-full rounded border border-border" />
      <p className="mt-2 text-xs text-muted">Gold = bit-4 signal · red = large OP_RETURN (from {from})</p>
    </div>
  );
}
