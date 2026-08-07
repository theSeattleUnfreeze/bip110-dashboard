import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { fetchApi } from "@/lib/api";

type ReplayBlock = {
  height: number;
  status: string;
  rejection_reason?: string;
  legacy_hash?: string;
};

type ReplayResponse = {
  from: number;
  to: number;
  blocks: ReplayBlock[];
};

export default async function ReplayPage() {
  let data: ReplayResponse | null = null;
  let err = "";
  try {
    data = await fetchApi<ReplayResponse>("/api/replay?from=961630&to=961640");
  } catch (e) {
    err = e instanceof Error ? e.message : "API error";
  }

  const rejected = data?.blocks.filter((b) => b.rejection_reason) ?? [];

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-bold">History replay</h1>
      <p className="mt-2 text-muted">Mandatory-signaling rejections on legacy-only blocks (v1).</p>
      {err && <p className="mt-4 text-sm text-amber-500">{err}</p>}

      <div className="mt-8 overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="text-left text-muted">
            <tr>
              <th className="p-3">Height</th>
              <th>Status</th>
              <th>Rejection</th>
            </tr>
          </thead>
          <tbody>
            {(data?.blocks ?? []).map((b) => (
              <tr key={b.height} className="border-t border-border">
                <td className="p-3 font-mono">{b.height}</td>
                <td>{b.status}</td>
                <td>{b.rejection_reason ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-sm text-muted">{rejected.length} rejection(s) in window</p>
    </DashboardLayout>
  );
}
