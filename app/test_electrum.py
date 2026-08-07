"""Tests for Electrum header parsing (no live node required)."""

import struct
import unittest

from electrum import ElectrumClient


class TestElectrumHeaders(unittest.TestCase):
  def test_headers_for_range_parses_blob(self):
    # One header: version=0x20000010 (signals bit 4), time at offset 68
    version = 0x20000010
    time_val = 1700000000
    hdr = bytearray(80)
    struct.pack_into("<i", hdr, 0, version)
    struct.pack_into("<I", hdr, 68, time_val)
    blob = bytes(hdr).hex()

    class FakeElectrum:
      def block_headers(self, start, count):
        assert start == 100
        assert count == 1
        return blob

    client = ElectrumClient("tcp:127.0.0.1:50002")
    client._call = lambda method, params: FakeElectrum().block_headers(*params)

    rows = client.headers_for_range(100, 100)
    self.assertEqual(len(rows), 1)
    self.assertEqual(rows[0]["height"], 100)
    self.assertEqual(rows[0]["version"], version)
    self.assertEqual(rows[0]["time"], time_val)


if __name__ == "__main__":
  unittest.main()
