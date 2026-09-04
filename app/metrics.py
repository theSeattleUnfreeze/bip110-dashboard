"""Difficulty and ETA metrics per chain node."""

import time

import signaling


def next_retarget_height(tip, period=2016):
  start = (tip // period) * period
  return start + period


def chain_metrics(rpc, tip=None, suelo=None):
  tip = tip or rpc.get_block_count()
  info = rpc.get_blockchain_info()
  difficulty = float(info.get("difficulty") or 0)
  retarget_h = next_retarget_height(tip)
  blocks_to_retarget = max(0, retarget_h - tip)

  lo = max(0, tip - 144)
  if suelo is not None:
    lo = max(lo, suelo)
  try:
    t_hi = rpc.call("getblockheader", rpc.call("getblockhash", tip))["time"]
    t_lo = rpc.call("getblockheader", rpc.call("getblockhash", lo))["time"] if lo < tip else t_hi
    span = max(0, t_hi - t_lo)
    n = max(1, tip - lo)
    mean_iv = span / n if span > 0 else None
  except Exception:
    mean_iv = None
    t_hi = None

  eta_block = int(mean_iv) if mean_iv else None
  eta_retarget = int(mean_iv * blocks_to_retarget) if mean_iv else None

  return {
    "difficulty": difficulty,
    "next_retarget_height": retarget_h,
    "blocks_to_retarget": blocks_to_retarget,
    "eta_next_block_sec": eta_block,
    "eta_retarget_sec": eta_retarget,
    "mean_interval_sec": round(mean_iv, 1) if mean_iv else None,
    "tip_height": tip,
    "tip_time": t_hi,
    "updated": int(time.time()),
  }


def for_nodes(rpcs, tips, suelos=None):
  suelos = suelos or {}
  out = {}
  for name, rpc in rpcs.items():
    try:
      out[name] = chain_metrics(rpc, tip=tips.get(name), suelo=suelos.get(name))
    except Exception as e:
      out[name] = {"error": str(e)}
  return out
