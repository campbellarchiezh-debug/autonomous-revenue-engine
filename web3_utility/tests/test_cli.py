"""
Unit & Integration tests for Web3 Micro-Utility CLI Suite.
"""

import json
import subprocess
import sys
import unittest

PYTHON_EXE = sys.executable
CLI_PATH = "web3_utility/run_cli.py"

class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        cmd = [PYTHON_EXE, CLI_PATH] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc

    def test_help_flag(self):
        """CLI --help outputs usage and exits 0."""
        p = self.run_cli("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("Web3 Micro-Utility & Developer Tools Suite", p.stdout)
        self.assertIn("inspect", p.stdout)
        self.assertIn("monitor", p.stdout)
        self.assertIn("convert", p.stdout)
        self.assertIn("gas", p.stdout)

    def test_tip_flag(self):
        """CLI --tip and --sponsor output beneficiary wallets."""
        p = self.run_cli("--tip")
        self.assertEqual(p.returncode, 0)
        self.assertIn("0xeF5766253e2D92E530e301aC22dcB8DE78E89C55", p.stdout)
        self.assertIn("3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp", p.stdout)
        self.assertIn("bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e", p.stdout)
        self.assertIn("GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA", p.stdout)

    def test_tip_json(self):
        """CLI --tip --json outputs valid JSON payload."""
        p = self.run_cli("--tip", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertIn("wallets", data)
        self.assertEqual(data["wallets"]["Base EVM"], "0xef5766253e2d92e530e301ac22dcb8de78e89c55")
        self.assertEqual(data["wallets"]["Solana"], "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp")

    def test_inspect_base_wallet(self):
        """Inspect Base EVM address."""
        p = self.run_cli("inspect", "0xef5766253e2d92e530e301ac22dcb8de78e89c55", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["chain"], "base")
        self.assertEqual(data["canonical_address"], "0xeF5766253e2D92E530e301aC22dcB8DE78E89C55")

    def test_inspect_solana_wallet(self):
        """Inspect Solana address."""
        p = self.run_cli("inspect", "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["chain"], "solana")

    def test_inspect_bitcoin_wallet(self):
        """Inspect Bitcoin Taproot address."""
        p = self.run_cli("inspect", "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["chain"], "bitcoin")
        self.assertEqual(data["address_type"], "taproot_v1")

    def test_inspect_stellar_wallet(self):
        """Inspect Stellar StrKey address."""
        p = self.run_cli("inspect", "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["chain"], "stellar")

    def test_inspect_invalid_address(self):
        """Inspect invalid address returns exit code 1."""
        p = self.run_cli("inspect", "0xInvalidHexAddress")
        self.assertEqual(p.returncode, 1)

    def test_monitor_offline(self):
        """Monitor --offline returns health metrics in JSON."""
        p = self.run_cli("monitor", "--offline", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        for expected in ["base", "ethereum", "solana", "bitcoin", "stellar"]:
            self.assertIn(expected, data)
            self.assertTrue(data[expected]["healthy"])

    def test_convert_command(self):
        """Convert command computes correct units."""
        p = self.run_cli("convert", "1", "eth", "gwei", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertEqual(data["result"], "1000000000")

    def test_gas_command(self):
        """Gas command calculates presets."""
        p = self.run_cli("gas", "eth_transfer", "20", "--eth-price", "2500", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertEqual(data["gas_limit"], 21000)
        self.assertEqual(data["total_cost_usd"], "1.0500")

if __name__ == "__main__":
    unittest.main()
