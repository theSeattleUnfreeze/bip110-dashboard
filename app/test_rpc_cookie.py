"""Unit tests for BitcoinRPC cookie auth (no live node)."""

import os
import tempfile
import unittest

import rpc


class TestCookieAuth(unittest.TestCase):
    def test_read_cookie_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("__cookie__:s3cret-value\n")
            path = f.name
        try:
            user, password = rpc._read_cookie_file(path)
            self.assertEqual(user, "__cookie__")
            self.assertEqual(password, "s3cret-value")
        finally:
            os.unlink(path)

    def test_missing_cookie_raises_clear_error(self):
        with self.assertRaises(rpc.RPCError) as ctx:
            rpc._read_cookie_file("/tmp/does-not-exist-bip110-cookie")
        self.assertIn("missing", str(ctx.exception).lower())

    def test_cookie_preferred_over_password(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("__cookie__:from-file\n")
            path = f.name
        try:
            client = rpc.BitcoinRPC(
                url="http://127.0.0.1:18443",
                user="envuser",
                password="envpass",
                cookie_path=path,
            )
            self.assertEqual(client.user, "__cookie__")
            self.assertEqual(client.password, "from-file")
            self.assertEqual(client.session.auth, ("__cookie__", "from-file"))
        finally:
            os.unlink(path)

    def test_401_reloads_cookie_and_retries(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("__cookie__:old\n")
            path = f.name

        class FakeResp:
            def __init__(self, status_code, body):
                self.status_code = status_code
                self._body = body

            def json(self):
                return self._body

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise Exception(f"HTTP {self.status_code}")

        def fake_post(url, data=None, timeout=None):
            calls.append(1)
            # First call: 401; after reload cookie becomes "new"
            if len(calls) == 1:
                with open(path, "w", encoding="utf-8") as wf:
                    wf.write("__cookie__:new\n")
                return FakeResp(401, {})
            return FakeResp(200, {"result": 42, "error": None})

        try:
            client = rpc.BitcoinRPC(
                url="http://127.0.0.1:18443",
                cookie_path=path,
            )
            calls = []
            client.session.post = fake_post
            result = client.call("getblockcount")
            self.assertEqual(result, 42)
            self.assertEqual(client.password, "new")
            self.assertEqual(len(calls), 2)
        finally:
            os.unlink(path)


class TestRegnetBlocksHelpers(unittest.TestCase):
    def test_yours_badge_matches_tag(self):
        os.environ["REGNET_COINBASE_TAG"] = "myworker"
        try:
            import importlib
            import regnet_blocks as rb
            importlib.reload(rb)
            self.assertTrue(rb._is_yours("DATUM/myworker/cpu"))
            self.assertFalse(rb._is_yours("someone-else"))
        finally:
            os.environ.pop("REGNET_COINBASE_TAG", None)
            import importlib
            import regnet_blocks as rb
            importlib.reload(rb)

    def test_warn_main_chain(self):
        import regnet_blocks as rb
        self.assertIsNotNone(rb._warn_chain("main"))
        self.assertIsNone(rb._warn_chain("regtest"))

    def test_blocks_payload_with_fake_rpc(self):
        import regnet_blocks as rb

        class FakeRPC:
            def get_block_count(self):
                return 2

            def batch(self, calls):
                out = []
                for method, params in calls:
                    if method == "getblockhash":
                        out.append(f"hash{params[0]}")
                    elif method == "getblockheader":
                        h = int(str(params[0]).replace("hash", "") or "0")
                        out.append({"version": 0x20000000, "time": 1700000000 + h})
                    elif method == "getblock":
                        out.append({"tx": [f"txid{params[0]}"]})
                    elif method == "getrawtransaction":
                        # coinbase with printable ASCII
                        tag = b"DATUM/myworker"
                        out.append({"vin": [{"coinbase": tag.hex()}]})
                    else:
                        raise AssertionError(method)
                return out

        os.environ["REGNET_COINBASE_TAG"] = "myworker"
        try:
            import importlib
            importlib.reload(rb)
            payload = rb.blocks_payload(limit=2, rpc=FakeRPC())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["tip"], 2)
            self.assertEqual(len(payload["blocks"]), 2)
            self.assertTrue(payload["blocks"][0]["yours"])
            self.assertIn("DATUM", payload["blocks"][0]["coinbase_ascii"])
            self.assertEqual(payload["blocks"][0]["nTx"], 1)
        finally:
            os.environ.pop("REGNET_COINBASE_TAG", None)
            import importlib
            importlib.reload(rb)


if __name__ == "__main__":
    unittest.main()
