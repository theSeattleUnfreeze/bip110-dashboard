import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { fetchApi, type ChainResponse } from "@/lib/api";

export default async function AnalyzerPage() {
  let chain: ChainResponse | null = null;
  try {
    chain = await fetchApi<ChainResponse>("/api/chain");
  } catch {
    chain = null;
  }

  const split = chain?.split_height;
  const coreTip = chain?.nodes?.core?.tip ?? 0;
  const knotsTip = chain?.nodes?.knots?.tip ?? 0;

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-bold">Chain analyzer</h1>
      <p className="mt-2 text-muted">Fork DAG — shared history through split, then parallel tips.</p>

      <div className="mt-8 flex flex-col items-center gap-6">
        <div className="rounded-lg border border-border bg-card px-6 py-3 font-mono text-sm">
          shared → height {split ?? coreTip}
        </div>
        <div className="flex w-full max-w-xl justify-between gap-4">
          <div className="flex-1 rounded-xl border border-amber-600/40 bg-card p-4 text-center">
            <p className="text-sm text-muted">core</p>
            <p className="font-mono text-lg">{coreTip}</p>
          </div>
          <div className="flex-1 rounded-xl border border-amber-600/40 bg-card p-4 text-center">
            <p className="text-sm text-muted">knots</p>
            <p className="font-mono text-lg">{knotsTip}</p>
          </div>
        </div>
        <p className="text-sm text-muted">{chain?.state ?? "unknown"} · React Flow DAG in a follow-up polish pass</p>
      </div>
    </DashboardLayout>
  );
}
