import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { fetchApi, type ChainResponse, type MandatoryClock, type SignalingResponse } from "@/lib/api";
import Link from "next/link";

const MILESTONES = [
  { height: 961632, label: "Mandatory signaling" },
  { height: 963648, label: "Forced lock-in" },
  { height: 965664, label: "Data rules active" },
];

function formatEta(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

export default async function LivePage() {
  let chain: ChainResponse | null = null;
  let clock: MandatoryClock | null = null;
  let signaling: SignalingResponse | null = null;
  let err = "";

  try {
    chain = await fetchApi<ChainResponse>("/api/chain");
    clock = await fetchApi<MandatoryClock>("/api/mandatory-clock");
    signaling = await fetchApi<SignalingResponse>("/api/signaling");
  } catch (e) {
    err = e instanceof Error ? e.message : "API unreachable";
  }

  const state = chain?.state ?? "unknown";
  const banner =
    state === "split"
      ? "Chains have diverged — compare nodes below."
      : state === "pre_split"
        ? "Both nodes follow the same chain."
        : "Chain status unknown.";

  return (
    <DashboardLayout>
      {err && (
        <p className="mb-6 rounded-lg border border-amber-600/40 bg-amber-950/30 p-4 text-sm">
          {err}. Start API with <code className="font-mono">docker compose up</code>.
        </p>
      )}

      <div className="mb-6 rounded-xl border border-border bg-card p-4">
        <p className="text-lg font-medium">{banner}</p>
        {chain?.note && <p className="mt-2 text-sm text-muted">{chain.note}</p>}
        <Link href="/prepare" className="mt-3 text-sm text-primary hover:underline">
          Fork preparation advisories →
        </Link>
      </div>

      <section className="mb-8 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-muted">Mandatory block clock</h2>
          <p className="mt-2 text-2xl font-bold">Block {clock?.mandatory_height ?? 961632}</p>
          <p className="text-sm text-muted">Estimate · {clock?.blocks_remaining ?? "—"} blocks remaining</p>
          <p className="mt-2">ETA: {formatEta(clock?.eta_time)}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-muted">Activation timeline</h2>
          <ol className="mt-2 space-y-2 text-sm">
            {MILESTONES.map((m) => (
              <li key={m.height}>
                <span className="font-mono">{m.height}</span> — {m.label}
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mb-8 rounded-xl border border-border bg-card p-4">
        <h2 className="mb-4 text-lg font-medium">Node comparison</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted">
              <th className="pb-2">Node</th>
              <th>Tip</th>
              <th>BIP-110</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(chain?.nodes ?? {}).map(([name, n]) => (
              <tr key={name} className="border-t border-border">
                <td className="py-2 font-mono">{name}</td>
                <td>{n.tip ?? "—"}</td>
                <td>{n.enforces ? "enforces" : "—"}</td>
                <td>{n.ok ? "ok" : n.error ?? "down"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {signaling && (
        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-4 text-lg font-medium">Signaling heatmap (current period)</h2>
          <p className="mb-3 text-sm text-muted">
            {signaling.summary.count} / {signaling.summary.threshold} signals · {signaling.summary.remaining} blocks left in period
          </p>
          <div className="flex flex-wrap gap-px">
            {signaling.blocks.map((b) => (
              <div
                key={b.height}
                title={`${b.height}`}
                className="h-3 w-1"
                style={{ background: b.signals_bip110 ? "#f59e0b" : "#3f3f46" }}
              />
            ))}
          </div>
        </section>
      )}
    </DashboardLayout>
  );
}
