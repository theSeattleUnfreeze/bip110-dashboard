"""
Unified chain client: Electrum for headers when configured, RPC for everything else.
"""

import os

from rpc import BitcoinRPC
from electrum import ElectrumClient


class ChainClient:
  """Minimum surface used by signaling and signal-map builders."""

  def __init__(self, rpc: BitcoinRPC, electrum_url=None, tor_proxy=None):
    self.rpc = rpc
    url = electrum_url or os.environ.get("ELECTRUM_URL", "")
    self.electrum = ElectrumClient(url, tor_proxy=tor_proxy) if url else None

  def get_block_count(self):
    return self.rpc.get_block_count()

  def get_blockchain_info(self):
    return self.rpc.get_blockchain_info()

  def get_network_info(self):
    return self.rpc.get_network_info()

  def call(self, method, *params):
    return self.rpc.call(method, *params)

  def batch(self, calls):
    return self.rpc.batch(calls)

  def headers_for_range(self, start_height, end_height, chunk=250):
    if self.electrum:
      try:
        return self.electrum.headers_for_range(start_height, end_height, chunk=min(chunk, 2016))
      except Exception:
        pass
    return self.rpc.headers_for_range(start_height, end_height, chunk=chunk)
