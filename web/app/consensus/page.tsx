import { DocsLayout } from "@/components/layout/DocsLayout";
import Link from "next/link";

const scenarios = [
  { id: "signal", title: "Signal bit 4", outcome: "Miner includes versionbits header; counts toward 55% threshold." },
  { id: "omit", title: "Omit signal", outcome: "Before mandatory height: valid on both chains. After 961,632 on BIP-110 chain: rejected." },
  { id: "return", title: "Chains reunify", outcome: "If majority never enforces split, tips can match again — reunified state." },
];

export default function ConsensusPage() {
  return (
    <DocsLayout>
      <h1 className="text-4xl font-bold">Consensus paths</h1>
      <p className="mt-4 text-xl text-muted">
        Educational fork scenarios — not a prediction of which path the network takes.
      </p>

      <div className="mt-12 space-y-4">
        {scenarios.map((s) => (
          <section key={s.id} className="rounded-xl border border-border bg-card p-6">
            <h2 className="text-lg font-medium">{s.title}</h2>
            <p className="mt-2 text-muted">{s.outcome}</p>
          </section>
        ))}
      </div>

      <p className="mt-12 text-sm text-muted">
        See also <Link href="/prepare" className="text-primary hover:underline">fork preparation advisories</Link>.
      </p>
    </DocsLayout>
  );
}
