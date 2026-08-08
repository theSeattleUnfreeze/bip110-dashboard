"use client";

import { useState } from "react";
import { ChainForkChart } from "@/components/ChainForkChart";
import type { ChainResponse, TxInspectResponse } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8110";

export function TxInspector({ chain }: { chain: ChainResponse | null }) {
  const [txid, setTxid] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<TxInspectResponse | null>(null);
  const [err, setErr] = useState("");

  async function inspect() {
    const id = txid.trim();
    if (!/^[a-fA-F0-9]{64}$/.test(id)) {
      setErr("Enter a 64-character hex transaction id.");
      setData(null);
      return;
    }
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(`${API}/api/tx-inspect?txid=${id}`, { cache: "no-store" });
      const json = (await res.json()) as TxInspectResponse;
      if (!json.ok) {
        setErr(json.error || "Lookup failed");
        setData(null);
      } else {
        setData(json);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Request failed");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  const coreTip = chain?.nodes?.core?.tip ?? 0;
  const knotsTip = chain?.nodes?.knots?.tip ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <label className="text-sm text-muted" htmlFor="txid">Transaction id</label>
        <div className="mt-2 flex flex-col gap-2 sm:flex-row">
          <input
            id="txid"
            type="text"
            value={txid}
            onChange={(e) => setTxid(e.target.value)}
            placeholder="64-char hex txid"
            className="flex-1 rounded-lg border border-border bg-background px-3 py-2 font-mono text-sm"
          />
          <button
            type="button"
            onClick={inspect}
            disabled={loading}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {loading ? "Inspecting…" : "Inspect"}
          </button>
        </div>
        {err && <p className="mt-2 text-sm text-red-400">{err}</p>}
      </div>

      {data?.ok && (
        <>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="rounded bg-emerald-900/40 px-2 py-0.5 text-emerald-300">
                {data.tier}
              </span>
              <span className="text-muted">timing: {data.timing}</span>
              {data.height != null && <span className="text-muted">height {data.height}</span>}
            </div>
            <p className="mt-3 text-sm">{data.summary}</p>
          </div>

          <ChainForkChart
            splitHeight={data.split_height}
            reunifiedHeight={data.reunified_height}
            txHeight={data.height}
            chainState={data.chain_state}
            txOnChains={data.tx_on_chains}
            outputs={data.outputs}
            coreTip={coreTip}
            knotsTip={knotsTip}
          />

          <div>
            <h2 className="text-lg font-semibold">Outputs</h2>
            <ul className="mt-3 space-y-3">
              {data.outputs.map((o) => (
                <li
                  key={o.n}
                  className="rounded-lg border border-border bg-card p-3 text-sm"
                >
                  <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono">
                    <span>vout {o.n}</span>
                    <span>{o.value_btc?.toFixed(8)} BTC</span>
                    {o.address && <span className="text-muted">{o.address}</span>}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {o.coin_on_chains.map((c) => (
                      <span
                        key={`on-${c}`}
                        className="rounded bg-amber-900/30 px-2 py-0.5 text-xs text-amber-200"
                      >
                        coin on {c}
                      </span>
                    ))}
                    {o.spent_on_chains.map((c) => (
                      <span
                        key={`spent-${c}`}
                        className="rounded bg-slate-800 px-2 py-0.5 text-xs text-muted"
                      >
                        spent on {c}
                      </span>
                    ))}
                    {o.replay_exposed && (
                      <span className="rounded bg-red-900/40 px-2 py-0.5 text-xs text-red-300">
                        replay exposed
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
