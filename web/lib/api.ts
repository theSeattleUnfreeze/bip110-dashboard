const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8110";

export async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

/** Like fetchApi but returns JSON error bodies (for optional features such as regnet). */
export async function fetchApiSoft<T extends { ok?: boolean; error?: string; hint?: string }>(
  path: string,
): Promise<T> {
  try {
    const res = await fetch(`${API}${path}`, { cache: "no-store" });
    const data = (await res.json().catch(() => ({}))) as T;
    if (!res.ok) {
      return {
        ...data,
        ok: false,
        error: data.error || `http_${res.status}`,
        hint: data.hint || `API ${path}: ${res.status}`,
      };
    }
    return data;
  } catch (e) {
    const msg = e instanceof Error ? e.message : "API unreachable";
    return { ok: false, error: "fetch_failed", hint: msg } as T;
  }
}

export type ChainResponse = {
  state: string;
  nodes: Record<string, { ok: boolean; tip?: number; subversion?: string; enforces?: boolean; error?: string }>;
  majority?: { tip?: number; avg_interval_sec?: number };
  minority?: { tip?: number; avg_interval_sec?: number };
  split_height?: number;
  note?: string;
};

export type MandatoryClock = {
  label: string;
  mandatory_height: number;
  tip_height: number;
  blocks_remaining: number;
  eta_time?: number;
  mean_interval_sec?: number;
};

export type SignalingResponse = {
  period_start: number;
  period_end: number;
  blocks: Array<{ height: number; signals_bip110: boolean }>;
  summary: { count: number; threshold: number; remaining: number };
};

export type RegnetTipResponse = {
  ok: boolean;
  tier?: string;
  chain?: string;
  blocks?: number;
  headers?: number;
  bestblockhash?: string;
  initialblockdownload?: boolean;
  warning?: string | null;
  coinbase_tag_expected?: string | null;
  error?: string;
  hint?: string;
};

export type RegnetBlock = {
  height: number;
  hash: string;
  time?: number;
  nTx?: number;
  version?: number;
  version_hex?: string | null;
  coinbase_hex?: string;
  coinbase_ascii?: string;
  miner_label?: string;
  yours?: boolean;
};

export type RegnetBlocksResponse = {
  ok: boolean;
  tier?: string;
  tip?: number;
  blocks?: RegnetBlock[];
  coinbase_tag_expected?: string | null;
  error?: string;
  hint?: string;
};
