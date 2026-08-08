"""Project arrival of mandatory signaling block (961,632). Label: Estimate."""

import math
import random
import time

import signaling

MANDATORY_HEIGHT = signaling.BIP110["mandatory_start"]
SAMPLE_WINDOW = 144


def _mean_interval(headers):
  if len(headers) < 2:
    return None
  t0 = headers[0]["time"]
  t1 = headers[-1]["time"]
  if t1 <= t0:
    return None
  return (t1 - t0) / (len(headers) - 1)


def build(client, tip=None):
  tip = tip or client.get_block_count()
  now = int(time.time())
  blocks_remaining = max(0, MANDATORY_HEIGHT - tip)
  lo = max(0, tip - SAMPLE_WINDOW)
  headers = client.headers_for_range(lo, tip)
  mean_iv = _mean_interval(headers)
  info = client.get_blockchain_info()
  difficulty = float(info.get("difficulty") or 0)

  eta_sec = None
  eta_time = None
  low_time = None
  high_time = None
  implied_hps = None

  if mean_iv and mean_iv > 0:
    eta_sec = int(blocks_remaining * mean_iv)
    eta_time = now + eta_sec
    implied_hps = difficulty * (2 ** 32) / mean_iv
    intervals = []
    for i in range(1, len(headers)):
      dt = headers[i]["time"] - headers[i - 1]["time"]
      if dt > 0:
        intervals.append(dt)
    if len(intervals) >= 3:
      mu = sum(intervals) / len(intervals)
      var = sum((x - mu) ** 2 for x in intervals) / len(intervals)
      sigma = math.sqrt(var)
      # 68% window on total time (~1 sigma on sum of iid intervals)
      margin = sigma * math.sqrt(max(1, blocks_remaining))
      low_time = int(now + blocks_remaining * mean_iv - margin)
      high_time = int(now + blocks_remaining * mean_iv + margin)

  return {
    "label": "estimate",
    "mandatory_height": MANDATORY_HEIGHT,
    "tip_height": tip,
    "blocks_remaining": blocks_remaining,
    "sample_window": len(headers),
    "mean_interval_sec": round(mean_iv, 1) if mean_iv else None,
    "difficulty": difficulty,
    "implied_hashes_per_second": round(implied_hps, 2) if implied_hps else None,
    "eta_time": eta_time,
    "eta_sec": eta_sec,
    "range_68_low_time": low_time,
    "range_68_high_time": high_time,
    "updated": now,
  }
