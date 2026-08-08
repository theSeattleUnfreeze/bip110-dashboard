type OutputCoin = {
  n: number;
  value_btc?: number;
  address?: string;
  script_type?: string;
  coin_on_chains: string[];
  spent_on_chains: string[];
  replay_exposed: boolean;
};

type Props = {
  splitHeight?: number | null;
  reunifiedHeight?: number | null;
  txHeight?: number | null;
  chainState?: string;
  txOnChains: string[];
  outputs: OutputCoin[];
  coreTip?: number;
  knotsTip?: number;
};

const NODE_COLOR: Record<string, string> = {
  core: "#f59e0b",
  knots: "#38bdf8",
};

export function ChainForkChart({
  splitHeight,
  reunifiedHeight,
  txHeight,
  chainState,
  txOnChains,
  outputs,
  coreTip = 0,
  knotsTip = 0,
}: Props) {
  const split = splitHeight ?? null;
  const reunify = reunifiedHeight ?? null;
  const txH = txHeight ?? null;
  const maxTip = Math.max(coreTip, knotsTip, txH ?? 0, split ?? 0) + 20;
  const w = 640;
  const h = 200;
  const pad = 48;

  const x = (height: number) =>
    pad + ((height / maxTip) * (w - pad * 2));

  const trunkEnd = split ?? maxTip;
  const showFork = chainState === "split" || (split !== null && reunify === null);
  const showReunify = reunify !== null && chainState === "reunified";

  const replayOutputs = outputs.filter((o) => o.replay_exposed);

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs uppercase tracking-wide text-muted">Chain map</p>
      <svg viewBox={`0 0 ${w} ${h}`} className="mt-2 w-full max-w-2xl" role="img">
        {/* shared trunk */}
        <line
          x1={x(0)}
          y1={h / 2}
          x2={x(trunkEnd)}
          y2={h / 2}
          stroke="#94a3b8"
          strokeWidth={4}
        />
        <text x={x(trunkEnd / 2)} y={h / 2 - 14} className="fill-muted text-[10px]">
          shared history
        </text>

        {showFork && split !== null && (
          <>
            <line
              x1={x(split)}
              y1={h / 2}
              x2={x(coreTip)}
              y2={h / 2 - 36}
              stroke={NODE_COLOR.core}
              strokeWidth={3}
            />
            <line
              x1={x(split)}
              y1={h / 2}
              x2={x(knotsTip)}
              y2={h / 2 + 36}
              stroke={NODE_COLOR.knots}
              strokeWidth={3}
            />
            <text x={x(coreTip) - 8} y={h / 2 - 44} className="fill-amber-500 text-[10px]">
              core {coreTip}
            </text>
            <text x={x(knotsTip) - 8} y={h / 2 + 52} className="fill-sky-400 text-[10px]">
              knots {knotsTip}
            </text>
            <circle cx={x(split)} cy={h / 2} r={5} fill="#f97316" />
            <text x={x(split) - 20} y={h / 2 + 16} className="fill-orange-400 text-[10px]">
              split {split}
            </text>
          </>
        )}

        {showReunify && reunify !== null && (
          <>
            <line
              x1={x(split ?? reunify)}
              y1={h / 2 - 20}
              x2={x(reunify)}
              y2={h / 2 - 20}
              stroke={NODE_COLOR.core}
              strokeWidth={2}
              strokeDasharray="4 3"
            />
            <line
              x1={x(split ?? reunify)}
              y1={h / 2 + 20}
              x2={x(reunify)}
              y2={h / 2 + 20}
              stroke={NODE_COLOR.knots}
              strokeWidth={2}
              strokeDasharray="4 3"
            />
            <line
              x1={x(reunify)}
              y1={h / 2}
              x2={x(coreTip)}
              y2={h / 2}
              stroke="#94a3b8"
              strokeWidth={4}
            />
            <text x={x(reunify) - 16} y={h / 2 - 28} className="fill-emerald-400 text-[10px]">
              reunify {reunify}
            </text>
          </>
        )}

        {txH !== null && (
          <>
            <line
              x1={x(txH)}
              y1={pad}
              x2={x(txH)}
              y2={h - pad}
              stroke="#e2e8f0"
              strokeWidth={1}
              strokeDasharray="3 3"
            />
            <circle cx={x(txH)} cy={h / 2} r={6} fill="#f8fafc" stroke="#e2e8f0" strokeWidth={2} />
            <text x={x(txH) - 24} y={pad + 4} className="fill-foreground text-[10px]">
              tx {txH}
            </text>
            {replayOutputs.map((o, idx) => (
              <g key={o.n}>
                <line
                  x1={x(txH)}
                  y1={h / 2}
                  x2={x(coreTip)}
                  y2={h / 2 - 28 - idx * 10}
                  stroke={NODE_COLOR.core}
                  strokeWidth={1.5}
                  opacity={0.7}
                />
                <line
                  x1={x(txH)}
                  y1={h / 2}
                  x2={x(knotsTip)}
                  y2={h / 2 + 28 + idx * 10}
                  stroke={NODE_COLOR.knots}
                  strokeWidth={1.5}
                  opacity={0.7}
                />
              </g>
            ))}
          </>
        )}
      </svg>
      <p className="mt-2 text-xs text-muted">
        {txOnChains.length
          ? `On chain: ${txOnChains.join(", ")}`
          : "Transaction chain placement unknown"}
        {replayOutputs.length > 0 && (
          <span className="text-amber-400">
            {" "}
            · {replayOutputs.length} output(s) still on both branches
          </span>
        )}
      </p>
    </div>
  );
}
