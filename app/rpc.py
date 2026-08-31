"""
JSON-RPC client for Bitcoin Core / Knots.

Supports:
  - clearnet (http://host:8332)
  - Tor (http://xxxxx.onion:8332) via SOCKS5h (onion resolved by the proxy)
  - cookie-file auth (__cookie__:<secret> from the node datadir)
  - batching (needed: scanning 2016 blocks one-by-one is very slow)
"""

import os
import json
import itertools
import requests


class RPCError(Exception):
    pass


def _read_cookie_file(path):
    """
    Bitcoin Core / Knots writes `.cookie` as `user:password` (no trailing junk
    beyond optional newline). Never log the secret.
    """
    path = (path or "").strip()
    if not path:
        raise RPCError("RPC cookie path is empty")
    if not os.path.isfile(path):
        raise RPCError("RPC cookie file missing or unreadable")
    try:
        with open(path, "r", encoding="utf-8") as f:
            line = f.read().strip()
    except OSError as e:
        raise RPCError("RPC cookie file missing or unreadable") from e
    if ":" not in line:
        raise RPCError("RPC cookie file malformed")
    user, password = line.split(":", 1)
    if not user:
        raise RPCError("RPC cookie file malformed")
    return user, password


class BitcoinRPC:
    def __init__(self, url=None, user=None, password=None,
                 cookie_path=None, tor_proxy=None, timeout=120):
        self.url = url or os.environ.get("BTC_RPC_URL", "http://127.0.0.1:8332")
        self.timeout = timeout
        self._id = itertools.count(1)

        # Cookie auth preferred when a path is set (explicit arg or env).
        env_cookie = os.environ.get("BTC_RPC_COOKIE", "").strip()
        self.cookie_path = (cookie_path if cookie_path is not None else env_cookie) or ""
        self.cookie_path = self.cookie_path.strip()

        if self.cookie_path:
            self.user, self.password = _read_cookie_file(self.cookie_path)
        else:
            self.user = user if user is not None else os.environ.get("BTC_RPC_USER", "")
            self.password = password if password is not None else os.environ.get("BTC_RPC_PASSWORD", "")

        self.session = requests.Session()
        self.session.auth = (self.user, self.password)
        self.session.headers.update({"Content-Type": "application/json"})

        # Onion URLs force SOCKS5h so Tor resolves the hostname, not the container.
        is_onion = ".onion" in self.url
        proxy = tor_proxy or os.environ.get("TOR_SOCKS", "socks5h://127.0.0.1:9050")
        if is_onion:
            self.session.proxies = {"http": proxy, "https": proxy}
            self.timeout = max(self.timeout, 180)
        self.is_onion = is_onion

    def _reload_cookie(self):
        if not self.cookie_path:
            return False
        self.user, self.password = _read_cookie_file(self.cookie_path)
        self.session.auth = (self.user, self.password)
        return True

    def _post(self, payload, *, _cookie_retried=False):
        r = self.session.post(self.url, data=json.dumps(payload), timeout=self.timeout)
        if r.status_code == 401 and self.cookie_path and not _cookie_retried:
            # Node restart regenerates `.cookie`; reload once and retry.
            self._reload_cookie()
            return self._post(payload, _cookie_retried=True)
        return r

    def call(self, method, *params):
        payload = {
            "jsonrpc": "1.0",
            "id": next(self._id),
            "method": method,
            "params": list(params),
        }
        r = self._post(payload)
        # Bitcoin Core answers HTTP 500 on RPC errors with the reason in the
        # body. raise_for_status() first used to drop that and leave a useless
        # "500 Server Error".
        if r.status_code >= 400:
            try:
                err = r.json().get("error")
            except ValueError:
                err = None
            if err:
                raise RPCError(f"{method}: {err}")
            if r.status_code == 401:
                raise RPCError(f"{method}: HTTP 401 (RPC auth failed)")
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RPCError(f"{method}: {data['error']}")
        return data["result"]

    def batch(self, calls, _depth=0):
        """
        calls: list of (method, [params...]) tuples.
        Returns results in the same order.

        If the response truncates mid-download, split the batch and retry.
        getblock verbosity=1 of a full block is ~250 KB of JSON, so a large
        batch can be tens of MB and Tor connections often cannot finish it.
        """
        if not calls:
            return []
        payload = []
        for method, params in calls:
            payload.append({
                "jsonrpc": "1.0",
                "id": next(self._id),
                "method": method,
                "params": list(params),
            })
        try:
            r = self._post(payload)
            if r.status_code == 401:
                raise RPCError(f"batch: HTTP 401 (RPC auth failed)")
            r.raise_for_status()
            data = r.json()
        except (requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                ValueError) as e:
            if len(calls) > 1 and _depth < 8:
                mid = len(calls) // 2
                return (self.batch(calls[:mid], _depth + 1) +
                        self.batch(calls[mid:], _depth + 1))
            raise RPCError(f"batch failed ({len(calls)} calls): {e}") from e

        by_id = {item["id"]: item for item in data}
        out = []
        for req in payload:
            item = by_id.get(req["id"])
            if item is None:
                raise RPCError(f"Incomplete batch response for id {req['id']}")
            if item.get("error"):
                raise RPCError(f"{req['method']}: {item['error']}")
            out.append(item["result"])
        return out

    # --- helpers ---

    def get_block_count(self):
        return self.call("getblockcount")

    def get_blockchain_info(self):
        return self.call("getblockchaininfo")

    def get_network_info(self):
        return self.call("getnetworkinfo")

    def get_peer_info(self):
        return self.call("getpeerinfo")

    def get_node_addresses(self, count=500, network=None):
        """
        Node address book (addrman), not current peers.

        Difference between "who it talks to now" and "who it knows". With
        onlynet=onion the former is a handful of addresses; the latter can
        be thousands, many reachable clearnet IPv4.

        `count` is capped on purpose: 0 returns everything the node knows,
        which over a hidden service is megabytes of JSON for the same goal.

        The `network` argument exists since Bitcoin Core v22.
        """
        # call() is variadic. Passing a list sends [[500]] and the node
        # expects a number → HTTP 500.
        #
        # If `network` fails, do NOT retry without it: that would return the
        # unfiltered list while pretending it was filtered.
        if network:
            return self.call("getnodeaddresses", count, network)
        return self.call("getnodeaddresses", count)

    def headers_for_range(self, start_height, end_height, chunk=250):
        """
        Returns [{height, hash, version, time}] for [start, end] inclusive.
        Two-phase batch: getblockhash → getblockheader.
        """
        out = []
        heights = list(range(start_height, end_height + 1))
        for i in range(0, len(heights), chunk):
            hs = heights[i:i + chunk]
            hashes = self.batch([("getblockhash", [h]) for h in hs])
            headers = self.batch([("getblockheader", [bh, True]) for bh in hashes])
            for h, bh, hdr in zip(hs, hashes, headers):
                out.append({
                    "height": h,
                    "hash": bh,
                    "version": hdr["version"],
                    "time": hdr["time"],
                })
        return out
