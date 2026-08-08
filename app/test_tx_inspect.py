"""Tests for fork-aware transaction classification."""

import unittest

import tx_inspect as mod


class TestTxInspect(unittest.TestCase):
    def test_normalize_txid(self):
        self.assertEqual(mod.normalize_txid("a" * 64), "a" * 64)
        self.assertEqual(mod.normalize_txid("  " + "b" * 64 + "  "), "b" * 64)
        self.assertIsNone(mod.normalize_txid("short"))
        self.assertIsNone(mod.normalize_txid(""))

    def test_classify_timing(self):
        state = {"split_height": 100, "reunified_height": 200}
        chain_pre = {"state": "pre_split"}
        chain_split = {"state": "split"}
        chain_reun = {"state": "reunified"}

        self.assertEqual(mod.classify_timing(None, state, chain_pre), "unconfirmed")
        self.assertEqual(mod.classify_timing(50, state, chain_pre), "pre_split")
        self.assertEqual(mod.classify_timing(100, state, chain_split), "pre_split")
        self.assertEqual(mod.classify_timing(150, state, chain_split), "post_split")
        self.assertEqual(mod.classify_timing(250, state, chain_reun), "post_reunify")
        self.assertEqual(
            mod.classify_timing(150, {"split_height": None}, chain_pre), "pre_split"
        )

    def test_summary_pre_split_replay(self):
        outputs = [{"replay_exposed": True}, {"replay_exposed": False}]
        text = mod.summary_text("pre_split", ["core", "knots"], outputs)
        self.assertIn("both branches", text)


if __name__ == "__main__":
    unittest.main()
