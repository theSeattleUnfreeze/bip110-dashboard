"""Inspect a transaction across core and knots chains after a split."""

import re

_TXID_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def normalize_txid(txid):
    if not txid:
        return None
    txid = txid.strip()
    return txid if _TXID_RE.match(txid) else None


def classify_timing(height, chain_state, chain_out):
    """When was the tx mined relative to split / reunification?"""
    if height is None:
        return "unconfirmed"
    split_h = chain_state.get("split_height")
    reunified_h = chain_state.get("reunified_height")
    state = chain_out.get("state") or chain_state.get("state") or "pre_split"

    if split_h is None or height <= split_h:
        return "pre_split"
    if state == "reunified" and reunified_h is not None and height >= reunified_h:
        return "post_reunify"
    return "post_split"


def summary_text(timing, tx_on_chains, outputs):
    if timing == "unconfirmed":
        return "Unconfirmed — not yet in either node's main chain."
    if timing == "pre_split":
        replay = sum(1 for o in outputs if o.get("replay_exposed"))
        if replay:
            return (
                "Mined on the shared chain before any split. Unspent outputs "
                "still exist on both branches and can be replayed after a fork."
            )
        return (
            "Mined on the shared chain before any split. Outputs are spent or "
            "only traceable on one branch now."
        )
    if timing == "post_split":
        sides = ", ".join(tx_on_chains) or "unknown"
        return f"Mined after the split — exists only on: {sides}."
    if timing == "post_reunify":
        return (
            "Mined after chains reconverged. The transaction lives on the "
            "reunified chain only (both nodes agree again)."
        )
    return ""


def _vout_row(vout):
    spk = vout.get("scriptPubKey") or {}
    addresses = spk.get("addresses") or []
    addr = spk.get("address") or (addresses[0] if addresses else None)
    return {
        "value_btc": vout.get("value"),
        "script_type": spk.get("type"),
        "address": addr,
    }


def _fetch_tx(rpc, txid):
    try:
        return rpc.call("getrawtransaction", txid, True)
    except Exception:
        return None


def _coin_on_chains(rpc_map, txid, vout_index):
    on = []
    for name, rpc in rpc_map.items():
        if not rpc:
            continue
        try:
            if rpc.call("gettxout", txid, vout_index, False) is not None:
                on.append(name)
        except Exception:
            pass
    return on


def inspect(txid, rpc_map, chain_state, chain_out):
    """
    rpc_map: {"core": BitcoinRPC|None, "knots": BitcoinRPC|None}
    """
    txid = normalize_txid(txid)
    if not txid:
        return {"ok": False, "error": "invalid txid — expected 64 hex characters"}

    available = {k: v for k, v in rpc_map.items() if v is not None}
    if not available:
        return {"ok": False, "error": "no RPC nodes available"}

    by_node = {name: _fetch_tx(rpc, txid) for name, rpc in available.items()}
    tx_on_chains = [n for n, tx in by_node.items() if tx is not None]
    if not tx_on_chains:
        return {
            "ok": False,
            "error": "transaction not found on configured nodes (needs txindex or wallet)",
            "txid": txid,
        }

    ref_name = tx_on_chains[0]
    tx = by_node[ref_name]
    height = tx.get("blockheight")
    blockhash = tx.get("blockhash")
    block_time = tx.get("blocktime")
    timing = classify_timing(height, chain_state, chain_out)

    outputs = []
    for i, vout in enumerate(tx.get("vout") or []):
        row = _vout_row(vout)
        coin_on = _coin_on_chains(available, txid, i)
        replay_exposed = timing == "pre_split" and len(coin_on) >= 2
        spent_hint = []
        for name in tx_on_chains:
            if name not in coin_on:
                spent_hint.append(name)
        outputs.append({
            "n": i,
            **row,
            "coin_on_chains": coin_on,
            "spent_on_chains": spent_hint,
            "replay_exposed": replay_exposed,
        })

    return {
        "ok": True,
        "tier": "verifiable",
        "txid": txid,
        "timing": timing,
        "height": height,
        "blockhash": blockhash,
        "block_time": block_time,
        "tx_on_chains": tx_on_chains,
        "chain_state": chain_out.get("state"),
        "split_height": chain_state.get("split_height"),
        "reunified_height": chain_state.get("reunified_height"),
        "summary": summary_text(timing, tx_on_chains, outputs),
        "outputs": outputs,
    }
