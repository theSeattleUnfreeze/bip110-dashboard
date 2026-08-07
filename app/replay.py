"""Post-fork divergence walk with mandatory-signaling rejection (v1)."""

import signaling

MANDATORY_START = signaling.BIP110["mandatory_start"]
MANDATORY_END = signaling.BIP110["mandatory_end"]


def classify_mandatory(version, height):
  if height < MANDATORY_START or height > MANDATORY_END:
    return None
  if not signaling.signals_bit(version):
    return "mandatory_signaling"
  return None


def walk(core_rpc, knots_rpc, from_height=None, to_height=None):
  core_tip = core_rpc.get_block_count()
  knots_tip = knots_rpc.get_block_count()
  lo = from_height or 0
  hi = to_height or max(core_tip, knots_tip)
  blocks = []

  for height in range(lo, hi + 1):
    legacy_hash = None
    bip110_hash = None
    status = "both"
    rejection = None
    version = None
    block_time = None

    try:
      legacy_hash = core_rpc.call("getblockhash", height)
      hdr = core_rpc.call("getblockheader", legacy_hash)
      version = hdr.get("version")
      block_time = hdr.get("time")
    except Exception:
      status = "missing_core"

    try:
      bip110_hash = knots_rpc.call("getblockhash", height)
    except Exception:
      if legacy_hash:
        status = "legacy_only"
      else:
        status = "missing_both"

    if legacy_hash and bip110_hash and legacy_hash != bip110_hash:
      status = "diverged"
    elif legacy_hash and bip110_hash:
      status = "both"

    if status == "legacy_only" and version is not None:
      rejection = classify_mandatory(version, height)

    blocks.append({
      "height": height,
      "legacy_hash": legacy_hash,
      "bip110_hash": bip110_hash,
      "status": status,
      "rejection_reason": rejection,
      "version": version,
      "signals_bip110": signaling.signals_bit(version) if version else None,
      "time": block_time,
    })

  return {
    "label": "verifiable",
    "from": lo,
    "to": hi,
    "core_tip": core_tip,
    "knots_tip": knots_tip,
    "blocks": blocks,
  }
