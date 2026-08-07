"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8110";

export default function ProfitabilityPage() {
  const [hashrate, setHashrate] = useState(100);
  const [power, setPower] = useState(3000);
  const [elec, setElec] = useState(0.12);
  const [fee, setFee] = useState(2);
  const [price, setPrice] = useState(100000);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  async function calc() {
    const q = new URLSearchParams({
      hashrate: String(hashrate),
      power_w: String(power),
      elec_kwh: String(elec),
      pool_fee: String(fee),
      btc_price: String(price),
    });
    const res = await fetch(`${API}/api/profitability?${q}`);
    setResult(await res.json());
  }

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-bold">Mining profitability</h1>
      <p className="mt-2 text-muted">Estimate revenue per chain at current difficulty (label: estimate).</p>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {[
          ["Hashrate (TH/s)", hashrate, setHashrate],
          ["Power (W)", power, setPower],
          ["Electricity ($/kWh)", elec, setElec],
          ["Pool fee (%)", fee, setFee],
          ["BTC price ($)", price, setPrice],
        ].map(([label, val, set]) => (
          <label key={label as string} className="block text-sm">
            <span className="text-muted">{label}</span>
            <input
              type="number"
              className="mt-1 w-full rounded border border-border bg-card p-2"
              value={val as number}
              onChange={(e) => (set as (n: number) => void)(Number(e.target.value))}
            />
          </label>
        ))}
      </div>

      <button
        onClick={calc}
        className="mt-6 rounded-md bg-primary px-4 py-2 text-sm font-medium text-black"
      >
        Calculate
      </button>

      {result && (
        <pre className="mt-8 overflow-x-auto rounded-xl border border-border bg-card p-4 text-sm">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </DashboardLayout>
  );
}
