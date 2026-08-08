const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8110";

export async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

export type ChainResponse = {
  state: string;
  nodes: Record<string, { ok: boolean; tip?: number; subversion?: string; enforces?: boolean; error?: string }>;
  majority?: { tip?: number; avg_interval_sec?: number };
  minority?: { tip?: number; avg_interval_sec?: number };
  split_height?: number;
  reunified_height?: number;
  note?: string;
};

export type TxInspectOutput = {
  n: number;
  value_btc?: number;
  address?: string;
  script_type?: string;
  coin_on_chains: string[];
  spent_on_chains: string[];
  replay_exposed: boolean;
};

export type TxInspectResponse = {
  ok: boolean;
  error?: string;
  tier?: string;
  txid?: string;
  timing?: string;
  height?: number | null;
  blockhash?: string;
  block_time?: number;
  tx_on_chains?: string[];
  chain_state?: string;
  split_height?: number | null;
  reunified_height?: number | null;
  summary?: string;
  outputs?: TxInspectOutput[];
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
