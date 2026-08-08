import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { TxInspector } from "@/components/TxInspector";
import { fetchApi, type ChainResponse } from "@/lib/api";

export default async function AnalyzerPage() {
  let chain: ChainResponse | null = null;
  try {
    chain = await fetchApi<ChainResponse>("/api/chain");
  } catch {
    chain = null;
  }

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-bold">Chain analyzer</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Inspect how a transaction sits relative to a chain split. Pre-split coins can
        appear on both branches after a fork; post-split transactions exist on only
        the branch that mined them until chains reconverge.
      </p>

      <div className="mt-6 rounded-lg border border-border bg-card/50 p-4 text-sm">
        <p>
          Chain state: <strong>{chain?.state ?? "unknown"}</strong>
          {chain?.split_height != null && (
            <> · split at {chain.split_height}</>
          )}
          {chain?.reunified_height != null && (
            <> · reunified at {chain.reunified_height}</>
          )}
        </p>
      </div>

      <div className="mt-8">
        <TxInspector chain={chain} />
      </div>
    </DashboardLayout>
  );
}
