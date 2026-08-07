"""Profitability model sanity checks."""

import unittest

from profitability import estimate


class TestProfitability(unittest.TestCase):
  def test_estimate_positive_revenue(self):
    r = estimate(100, 1e12, 3000, 0.12, 2, 100000)
    self.assertGreater(r["btc_per_day"], 0)
    self.assertGreater(r["revenue_usd_per_day"], 0)


if __name__ == "__main__":
  unittest.main()
