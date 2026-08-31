"""
Regnet (Blake2b / BIP-110 Knots) tip and recent-block helpers for the miner live view.

Trusts Knots for consensus; does not reimplement Blake2b PoW.
Coinbase tags are voluntary text — useful for "your miner" badges, not proof.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

from rpc import BitcoinRPC, RPCError
import pools as poolsmod

REGNET_CACHE_TTL = float(os.environ.get("REGNET_CACHE_TTL", "1.5"))
DEFAULT_BLOCK_LIMIT = 25
MAX_BLOCK_LIMIT = 100

# Chains that mean the URL is almost certainly not a Blake2b regnet.
_WRONG_CHAINS = frozenset({"main", "test", "signet"})

_cache: dict[str, tuple[float, Any]] = {}


def enabled() -> bool:
    return os.environ.get("REGNET_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def coinbase_tag_expected() -> str:
    return (os.environ.get("REGNET_COINBASE_TAG") or "").strip()


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url.rstrip("/")


def configured() -> bool:
    return bool(_normalize_url(os.environ.get("BTC_RPC_URL_REGNET", "")))


def make_rpc(timeout: int = 30) -> BitcoinRPC:
    url = _normalize_url(os.environ.get("BTC_RPC_URL_REGNET", ""))
    if not url:
        raise RuntimeError("BTC_RPC_URL_REGNET is not set")

    cookie = (os.environ.get("BTC_RPC_COOKIE_REGNET") or "").strip()
    if cookie:
        return BitcoinRPC(url=url, cookie_path=cookie, timeout=timeout)

    user = os.environ.get("BTC_RPC_USER_REGNET") or ""
    password = os.environ.get("BTC_RPC_PASSWORD_REGNET") or ""
    if not user and not password:
        # Fall back to shared creds only when no cookie path is configured.
        user = os.environ.get("BTC_RPC_USER", "")
        password = os.environ.get("BTC_RPC_PASSWORD", "")
    return BitcoinRPC(url=url, user=user, password=password, cookie_path="", timeout=timeout)


def _cached(key: str, builder):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < REGNET_CACHE_TTL:
        return hit[1]
    value = builder()
    _cache[key] = (now, value)
    return value


def clear_cache():
    _cache.clear()


def _ascii_from_coinbase_hex(coinbase_hex: str) -> str:
    try:
        raw = bytes.fromhex(coinbase_hex or "")
    except (ValueError, TypeError):
        return ""
    return poolsmod._printable(raw)


def _miner_label(coinbase_ascii: str, coinbase_hex: str) -> str:
    """Best-effort DATUM / pool-ish label from coinbase text."""
    text = coinbase_ascii or ""
    low = text.lower()
    for needle, label in (
        ("datum", "DATUM"),
        ("ocean", "Ocean"),
        ("ckpool", "ckpool"),
        ("public-pool", "Public Pool"),
    ):
        if needle in low:
            return label
    pool, _tag = poolsmod.identify(coinbase_hex or "")
    if pool not in ("Desconocido", "Sin etiqueta", "Unknown", ""):
        return pool
    # First printable chunk as a short label.
    chunks = re.findall(r"[\x20-\x7e]{4,}", text)
    return chunks[0][:40] if chunks else ""


def _is_yours(coinbase_ascii: str) -> bool:
    expected = coinbase_tag_expected()
    if not expected:
        return False
    return expected.lower() in (coinbase_ascii or "").lower()


def _block_details(rpc: BitcoinRPC, blockhashes: list[str]) -> dict[str, dict]:
    """Map blockhash → {coinbase_hex, nTx} via getblock + getrawtransaction."""
    if not blockhashes:
        return {}
    out: dict[str, dict] = {}
    blocks = rpc.batch([("getblock", [bh, 1]) for bh in blockhashes])
    first_txids = []
    valid = []
    for bh, blk in zip(blockhashes, blocks):
        txs = (blk or {}).get("tx") or []
        out[bh] = {"coinbase_hex": "", "nTx": len(txs)}
        if txs:
            first_txids.append(txs[0])
            valid.append(bh)
    if not first_txids:
        return out
    raws = rpc.batch([
        ("getrawtransaction", [txid, True, bh])
        for txid, bh in zip(first_txids, valid)
    ])
    for bh, raw in zip(valid, raws):
        try:
            out[bh]["coinbase_hex"] = raw["vin"][0]["coinbase"]
        except (KeyError, IndexError, TypeError):
            out[bh]["coinbase_hex"] = ""
    return out


def _warn_chain(chain: str) -> str | None:
    c = (chain or "").lower()
    if c in _WRONG_CHAINS:
        return (
            f"Connected node reports chain={chain!r}; expected a regtest/regnet "
            "Blake2b node. Check BTC_RPC_URL_REGNET."
        )
    return None


def tip_payload(rpc: BitcoinRPC | None = None) -> dict:
    rpc = rpc or make_rpc()
    info = rpc.get_blockchain_info()
    chain = info.get("chain") or ""
    return {
        "ok": True,
        "tier": "verifiable",
        "chain": chain,
        "blocks": info.get("blocks"),
        "headers": info.get("headers"),
        "bestblockhash": info.get("bestblockhash"),
        "initialblockdownload": bool(info.get("initialblockdownload")),
        "warning": _warn_chain(chain),
        "coinbase_tag_expected": coinbase_tag_expected() or None,
    }


def blocks_payload(limit: int = DEFAULT_BLOCK_LIMIT, rpc: BitcoinRPC | None = None) -> dict:
    limit = max(1, min(int(limit), MAX_BLOCK_LIMIT))
    rpc = rpc or make_rpc()
    tip = rpc.get_block_count()
    start = max(0, tip - limit + 1)
    heights = list(range(tip, start - 1, -1))  # newest first
    if not heights:
        return {
            "ok": True,
            "tier": "verifiable",
            "tip": tip,
            "blocks": [],
            "coinbase_tag_expected": coinbase_tag_expected() or None,
        }

    hashes = rpc.batch([("getblockhash", [h]) for h in heights])
    headers = rpc.batch([("getblockheader", [bh, True]) for bh in hashes])
    details = _block_details(rpc, hashes)

    rows = []
    for height, bh, hdr in zip(heights, hashes, headers):
        detail = details.get(bh) or {}
        cb_hex = detail.get("coinbase_hex") or ""
        cb_ascii = _ascii_from_coinbase_hex(cb_hex)
        version = hdr.get("version")
        rows.append({
            "height": height,
            "hash": bh,
            "time": hdr.get("time"),
            "nTx": detail.get("nTx", 0),
            "version": version,
            "version_hex": f"0x{version:08x}" if isinstance(version, int) else None,
            "coinbase_hex": cb_hex[:200] if cb_hex else "",
            "coinbase_ascii": cb_ascii,
            "miner_label": _miner_label(cb_ascii, cb_hex),
            "yours": _is_yours(cb_ascii),
        })

    return {
        "ok": True,
        "tier": "verifiable",
        "tip": tip,
        "blocks": rows,
        "coinbase_tag_expected": coinbase_tag_expected() or None,
    }


def get_tip() -> dict:
    return _cached("tip", tip_payload)


def get_blocks(limit: int = DEFAULT_BLOCK_LIMIT) -> dict:
    return _cached(f"blocks:{limit}", lambda: blocks_payload(limit))
