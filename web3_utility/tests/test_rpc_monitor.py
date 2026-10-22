"""
Unit tests for Multi-Chain RPC Health Monitor & Latency Benchmarking.
"""

import io
import json
import unittest
from unittest.mock import MagicMock, patch
from web3_utility.src.rpc_monitor import (
    RPCMonitor,
    benchmark_all,
    benchmark_chain,
    DEFAULT_ENDPOINTS,
    DETERMINISTIC_MOCK_DATA,
)

class TestRPCMonitorMockMode(unittest.TestCase):
    def setUp(self):
        self.monitor = RPCMonitor(force_offline=True)

    def test_offline_mode_base(self):
        """Offline benchmark for Base returns valid deterministic telemetry."""
        res = self.monitor.benchmark_chain("base", offline=True)
        self.assertTrue(res["healthy"])
        self.assertEqual(res["chain"], "base")
        self.assertEqual(res["chain_id"], 8453)
        self.assertEqual(res["mode"], "offline_mock")
        self.assertGreater(res["block_height"], 20000000)
        self.assertGreater(res["latency_ms"], 0.0)

    def test_offline_mode_all_chains(self):
        """All supported chains return deterministic mock metrics."""
        for chain_key in ["base", "ethereum", "solana", "bitcoin", "stellar"]:
            with self.subTest(chain=chain_key):
                res = self.monitor.benchmark_chain(chain_key, offline=True)
                self.assertTrue(res["healthy"])
                self.assertEqual(res["chain"], chain_key)
                self.assertIsNotNone(res["block_height"])
                self.assertIsNotNone(res["latency_ms"])
                self.assertEqual(res["sync_status"], "synced")

    def test_benchmark_all_helper(self):
        """Test benchmark_all returns all 5 chains."""
        results = benchmark_all(offline=True)
        self.assertEqual(len(results), 5)
        for expected in ["base", "ethereum", "solana", "bitcoin", "stellar"]:
            self.assertIn(expected, results)
            self.assertTrue(results[expected]["healthy"])

    def test_unsupported_chain_error(self):
        """Querying an unknown chain returns informative error."""
        res = self.monitor.benchmark_chain("dogecoin", offline=True)
        self.assertFalse(res["healthy"])
        self.assertIn("Unsupported chain", res["error"])


class TestRPCMonitorNetworkSimulation(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_evm_query_live_mocked(self, mock_urlopen):
        """Simulate successful live EVM RPC response."""
        mock_response = io.BytesIO(json.dumps([
            {"jsonrpc": "2.0", "result": "0x148c2b0", "id": 1}, # block 21545648
            {"jsonrpc": "2.0", "result": "0x2105", "id": 2},    # chainId 8453
        ]).encode("utf-8"))

        cm = MagicMock()
        cm.__enter__.return_value = mock_response
        mock_urlopen.return_value = cm

        monitor = RPCMonitor(force_offline=False)
        res = monitor.benchmark_chain("base", custom_endpoints=["https://mainnet.base.org"])

        self.assertTrue(res["healthy"])
        self.assertEqual(res["chain_id"], 8453)
        self.assertEqual(res["block_height"], 21545648)
        self.assertEqual(res["mode"], "live_remote")

    @patch("urllib.request.urlopen")
    def test_fallback_on_network_failure(self, mock_urlopen):
        """When network endpoints throw URLError, fall back to offline simulation."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        monitor = RPCMonitor(force_offline=False)
        res = monitor.benchmark_chain("ethereum", custom_endpoints=["https://broken.rpc.io"])

        self.assertTrue(res["healthy"])
        self.assertEqual(res["mode"], "offline_fallback")
        self.assertEqual(res["chain_id"], 1)
        self.assertTrue(len(res.get("warnings", [])) > 0)


class TestAdaptiveSSLContext(unittest.TestCase):
    def test_ssl_context_creation(self):
        """Ensure adaptive SSL context initializes without error."""
        ctx = RPCMonitor._build_adaptive_ssl_context()
        self.assertIsNotNone(ctx)

if __name__ == "__main__":
    unittest.main()
