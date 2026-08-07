"""Mining revenue estimate per chain (simplified model)."""

import time

BLOCKS_PER_DAY = 144
SECONDS_PER_DAY = 86400


def estimate(hashrate_th, difficulty, power_w, elec_kwh, pool_fee_pct, btc_price):
  if difficulty <= 0 or hashrate_th <= 0:
    return {"error": "hashrate and difficulty required"}

  # TH/s to H/s
  hashrate = hashrate_th * 1e12
  network_hps = difficulty * (2 ** 32) / 600  # assume 10 min blocks for network baseline
  share = hashrate / network_hps if network_hps > 0 else 0
  btc_per_day = share * BLOCKS_PER_DAY * 3.125 * (1 - pool_fee_pct / 100)
  revenue_usd = btc_per_day * btc_price
  power_kwh_day = (power_w / 1000) * (SECONDS_PER_DAY / 3600) if power_w > 0 else 0
  cost_usd = power_kwh_day * elec_kwh
  profit_usd = revenue_usd - cost_usd

  return {
    "label": "estimate",
    "hashrate_th": hashrate_th,
    "difficulty": difficulty,
    "pool_fee_pct": pool_fee_pct,
    "btc_price": btc_price,
    "btc_per_day": round(btc_per_day, 8),
    "revenue_usd_per_day": round(revenue_usd, 2),
    "cost_usd_per_day": round(cost_usd, 2),
    "profit_usd_per_day": round(profit_usd, 2),
    "network_share_pct": round(share * 100, 6),
    "updated": int(time.time()),
  }


def compare_chains(core_diff, knots_diff, hashrate_th, power_w, elec_kwh, pool_fee_pct, btc_price):
  return {
    "core": estimate(hashrate_th, core_diff, power_w, elec_kwh, pool_fee_pct, btc_price),
    "knots": estimate(hashrate_th, knots_diff, power_w, elec_kwh, pool_fee_pct, btc_price),
  }
