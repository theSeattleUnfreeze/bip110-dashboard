"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import {
  fetchApiSoft,
  type RegnetBlocksResponse,
  type RegnetTipResponse,
} from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

const POLL_MS = 2000;

function formatTime(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function shortHash(h?: string) {
  if (!h) return "—";
  return `${h.slice(0, 10)}…${h.slice(-8)}`;
}

export default function RegnetPage() {
  const tipQ = useQuery({
    queryKey: ["regnet", "tip"],
    queryFn: () => fetchApiSoft<RegnetTipResponse>("/api/regnet/tip"),
    refetchInterval: POLL_MS,
  });
  const blocksQ = useQuery({
    queryKey: ["regnet", "blocks"],
    queryFn: () => fetchApiSoft<RegnetBlocksResponse>("/api/regnet/blocks?limit=25"),
    refetchInterval: POLL_MS,
  });

  const tip = tipQ.data;
  const blocks = blocksQ.data;
  const errHint =
    (!tip?.ok && tip?.hint) ||
    (!blocks?.ok && blocks?.hint) ||
    (tipQ.isError && "Tip request failed") ||
    (blocksQ.isError && "Blocks request failed") ||
    "";

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Regnet miner</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Live tip and recent blocks from your Blake2b / BIP-110 Knots regnet node.
          Coinbase tags are voluntary — the &quot;yours&quot; badge matches{" "}
          <code className="font-mono text-xs">REGNET_COINBASE_TAG</code>.
        </p>
      </div>

      {errHint && (
        <p className="mb-6 rounded-lg border border-amber-600/40 bg-amber-950/30 p-4 text-sm">
          {errHint}
          {(tip?.error === "regnet_disabled" || tip?.error === "regnet_not_configured") && (
            <>
              {" "}
              See <code className="font-mono text-xs">docs/regnet-miner-view.md</code>.
            </>
          )}
        </p>
      )}

      {tip?.warning && (
        <p className="mb-6 rounded-lg border border-rose-600/40 bg-rose-950/30 p-4 text-sm">
          {tip.warning}
        </p>
      )}

      <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-muted">Tip height</h2>
          <p className="mt-2 font-mono text-3xl font-bold tabular-nums">
            {tip?.ok ? tip.blocks ?? "—" : "—"}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-muted">Chain</h2>
          <p className="mt-2 font-mono text-xl">{tip?.ok ? tip.chain ?? "—" : "—"}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-muted">Best hash</h2>
          <p className="mt-2 break-all font-mono text-xs">
            {tip?.ok ? shortHash(tip.bestblockhash) : "—"}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-muted">IBD</h2>
          <p className="mt-2 text-xl">
            {tip?.ok ? (tip.initialblockdownload ? "syncing" : "caught up") : "—"}
          </p>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-card p-4">
        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-lg font-medium">Recent blocks</h2>
          <p className="text-xs text-muted">
            Polling every {POLL_MS / 1000}s
            {tip?.coinbase_tag_expected
              ? ` · yours tag: ${tip.coinbase_tag_expected}`
              : " · set REGNET_COINBASE_TAG to highlight your miner"}
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-muted">
                <th className="py-2 pr-3 font-medium">Height</th>
                <th className="py-2 pr-3 font-medium">Time</th>
                <th className="py-2 pr-3 font-medium">Tx</th>
                <th className="py-2 pr-3 font-medium">Miner</th>
                <th className="py-2 pr-3 font-medium">Coinbase</th>
                <th className="py-2 font-medium">Hash</th>
              </tr>
            </thead>
            <tbody>
              {(blocks?.blocks ?? []).map((b) => (
                <tr
                  key={b.hash}
                  className={`border-b border-border/60 ${
                    b.yours ? "bg-emerald-950/40" : ""
                  }`}
                >
                  <td className="py-2 pr-3 font-mono tabular-nums">
                    {b.height}
                    {b.yours && (
                      <span className="ml-2 text-xs font-sans text-emerald-400">yours</span>
                    )}
                  </td>
                  <td className="py-2 pr-3 text-muted">{formatTime(b.time)}</td>
                  <td className="py-2 pr-3 font-mono tabular-nums">{b.nTx ?? "—"}</td>
                  <td className="py-2 pr-3">{b.miner_label || "—"}</td>
                  <td className="max-w-xs truncate py-2 pr-3 font-mono text-xs text-muted" title={b.coinbase_ascii}>
                    {b.coinbase_ascii || "—"}
                  </td>
                  <td className="py-2 font-mono text-xs">{shortHash(b.hash)}</td>
                </tr>
              ))}
              {blocks?.ok && (blocks.blocks?.length ?? 0) === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-muted">
                    No blocks yet on this chain.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </DashboardLayout>
  );
}
