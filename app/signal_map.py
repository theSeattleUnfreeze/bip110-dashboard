"""Build compact per-block signaling map (bit-4 layer). Label: verifiable on own node."""

import base64
import os
import time

import signaling
import pools as poolsmod

FIRST_SCAN_HEIGHT = int(os.environ.get("SIGNAL_MAP_FROM", "900000"))
CACHE_NAME = "signal_map.json"
REFRESH_SEC = int(os.environ.get("SIGNAL_MAP_TTL", "600"))


def _bits_base64(headers):
  bits = bytearray()
  for h in headers:
    bits.append(1 if signaling.signals_bit(h["version"]) else 0)
  # pack bits into bytes MSB-first per byte
  out = bytearray()
  for i in range(0, len(bits), 8):
    chunk = bits[i:i + 8]
    b = 0
    for j, bit in enumerate(chunk):
      b |= (bit << (7 - j))
    out.append(b)
  return base64.b64encode(bytes(out)).decode("ascii")


def build(client, cache_dir=None, op_return=False):
  tip = client.get_block_count()
  start = max(FIRST_SCAN_HEIGHT, signaling.BIP110["mandatory_start"] - 25000)
  start = max(start, FIRST_SCAN_HEIGHT)
  headers = client.headers_for_range(start, tip, chunk=500)
  signaling_blocks = [h for h in headers if signaling.signals_bit(h["version"])]
  bits_b64 = _bits_base64(headers)

  recent = []
  for h in signaling_blocks[-40:]:
    recent.append({
      "h": h["height"],
      "ts": h["time"],
      "pool": None,
      "miners": [],
    })

  heroes = []
  try:
    sample = signaling_blocks[-500:] if len(signaling_blocks) > 500 else signaling_blocks
    if sample:
      heights = [h["height"] for h in sample]
      hashes = client.batch([("getblockhash", [ht]) for ht in heights])
      enriched = []
      for h, bh in zip(sample, hashes):
        enriched.append({
          "height": h["height"],
          "hash": bh,
          "version": h["version"],
          "time": h["time"],
        })
      attributed = poolsmod.attribute_blocks(client.rpc, enriched)
      counts = {}
      for row in attributed:
        tag = row.get("pool") or "unknown"
        counts[tag] = counts.get(tag, 0) + 1
      total = sum(counts.values()) or 1
      heroes = [
        {"name": k, "n": v, "share": round(100 * v / total, 1)}
        for k, v in sorted(counts.items(), key=lambda x: -x[1])[:12]
      ]
  except Exception:
    pass

  info = client.get_blockchain_info()
  period_start = (tip // signaling.BIP110["period"]) * signaling.BIP110["period"]
  sig_in_period = sum(
    1 for h in headers
    if h["height"] >= period_start and signaling.signals_bit(h["version"])
  )
  scanned_in_period = sum(1 for h in headers if h["height"] >= period_start)
  share_pct = round(100 * sig_in_period / scanned_in_period, 2) if scanned_in_period else 0

  return {
    "label": "verifiable",
    "from": start,
    "to": tip,
    "count": len(headers),
    "signalingCount": len(signaling_blocks),
    "bitsBase64": bits_b64,
    "signalingRecords": [{"height": h["height"], "time": h["time"]} for h in signaling_blocks[-200:]],
    "recentSignaling": recent,
    "heroes": heroes,
    "chainClock": {
      "tipHeight": tip,
      "tipTime": headers[-1]["time"] if headers else None,
      "difficulty": info.get("difficulty"),
      "periodStartHeight": period_start,
    },
    "bit4HashpowerEstimate": {
      "signalingSharePct": share_pct,
      "networkHashesPerSecond": None,
      "impliedHashesPerSecond": None,
      "sampling95LowHashesPerSecond": None,
      "sampling95HighHashesPerSecond": None,
    },
    "opReturnLayer": _op_return_layer(client, headers) if op_return else None,
    "updated": int(time.time()),
  }


def _op_return_layer(client, headers, chunk=25):
  sizes = []
  for i in range(0, len(headers), chunk):
    batch_h = headers[i:i + chunk]
    heights = [h["height"] for h in batch_h]
    try:
      hashes = client.batch([("getblockhash", [ht]) for ht in heights])
      blocks = client.batch([("getblock", [bh, 2]) for bh in hashes])
    except Exception:
      sizes.extend([0] * len(batch_h))
      continue
    for blk in blocks:
      max_sz = 0
      for tx in blk.get("tx", []):
        for vout in tx.get("vout", []):
          spk = vout.get("scriptPubKey", {})
          if spk.get("type") == "nulldata":
            hexdata = spk.get("hex", "")
            max_sz = max(max_sz, max(0, len(hexdata) // 2 - 1))
      sizes.append(max_sz)
  return sizes


def load_cached(cache_dir):
  path = os.path.join(cache_dir, CACHE_NAME)
  if not os.path.isfile(path):
    return None
  try:
    import json
    with open(path, "r", encoding="utf-8") as f:
      return json.load(f)
  except (OSError, ValueError):
    return None


def save_cached(cache_dir, data):
  if not cache_dir:
    return
  import json
  path = os.path.join(cache_dir, CACHE_NAME)
  tmp = path + ".tmp"
  with open(tmp, "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(",", ":"))
  os.replace(tmp, path)
