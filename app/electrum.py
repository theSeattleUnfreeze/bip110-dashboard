"""
Electrum protocol client for block headers (blockchain.block.headers).

Used when a node exposes Electrum on clearnet/Tor instead of or alongside RPC.
RPC remains required for chainwork, difficulty, and full block fetches.
"""

import json
import itertools
import socket
import ssl
import struct

import requests


class ElectrumError(Exception):
    pass


class ElectrumClient:
  def __init__(self, url, timeout=60, tor_proxy=None):
    self.url = (url or "").strip()
    self.timeout = timeout
    self._id = itertools.count(1)
    self._use_http = self.url.startswith(("http://", "https://"))
    if self._use_http:
      self.session = requests.Session()
      is_onion = ".onion" in self.url
      if is_onion and tor_proxy:
        self.session.proxies = {"http": tor_proxy, "https": tor_proxy}
      self.session.headers.update({"Content-Type": "application/json"})
    else:
      self.session = None

  def _call(self, method, params):
    payload = {
      "jsonrpc": "2.0",
      "id": next(self._id),
      "method": method,
      "params": params,
    }
    if self._use_http:
      r = self.session.post(self.url, data=json.dumps(payload), timeout=self.timeout)
      r.raise_for_status()
      data = r.json()
      if data.get("error"):
        raise ElectrumError(data["error"])
      return data["result"]

    host, port = self._parse_host_port()
    raw = json.dumps(payload).encode()
    with socket.create_connection((host, port), timeout=self.timeout) as sock:
      if self.url.startswith("ssl:"):
        ctx = ssl.create_default_context()
        sock = ctx.wrap_socket(sock, server_hostname=host)
      sock.sendall(struct.pack("!I", len(raw)) + raw)
      hdr = self._read_exact(sock, 4)
      n = struct.unpack("!I", hdr)[0]
      body = self._read_exact(sock, n)
    data = json.loads(body.decode())
    if data.get("error"):
      raise ElectrumError(data["error"])
    return data["result"]

  def _parse_host_port(self):
    u = self.url
    if u.startswith("ssl:"):
      u = u[4:]
    elif u.startswith("tcp:"):
      u = u[4:]
    if "@" in u:
      u = u.split("@", 1)[1]
    host, _, port = u.partition(":")
    return host, int(port or 50002)

  def _read_exact(self, sock, n):
    buf = b""
    while len(buf) < n:
      chunk = sock.recv(n - len(buf))
      if not chunk:
        raise ElectrumError("electrum connection closed")
      buf += chunk
    return buf

  def block_headers(self, start_height, count):
    """Returns hex blob: 80 bytes per header (little-endian fields)."""
    return self._call("blockchain.block.headers", [start_height, count])

  def headers_for_range(self, start_height, end_height, chunk=2016):
    """[{height, version, time}] — parity with BitcoinRPC.headers_for_range."""
    out = []
    h = start_height
    while h <= end_height:
      n = min(chunk, end_height - h + 1)
      blob = self.block_headers(h, n)
      raw = bytes.fromhex(blob)
      for i in range(n):
        off = i * 80
        if off + 80 > len(raw):
          break
        version = struct.unpack_from("<i", raw, off)[0]
        time = struct.unpack_from("<I", raw, off + 68)[0]
        out.append({"height": h + i, "hash": None, "version": version, "time": time})
      h += n
    return out
