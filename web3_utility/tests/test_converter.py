"""
Unit tests for Cryptocurrency Unit Converter & Gas Fee Calculator.
"""

import unittest
from decimal import Decimal
from web3_utility.src.converter import (
    calculate_gas_cost,
    convert_units,
    get_supported_units,
    GAS_PRESETS,
)

class TestUnitConversions(unittest.TestCase):
    def test_evm_conversions(self):
        """Test exact EVM conversions."""
        # 1 ETH to Wei
        self.assertEqual(convert_units(1, "eth", "wei"), Decimal("1000000000000000000"))
        # 1 ETH to Gwei
        self.assertEqual(convert_units(1, "eth", "gwei"), Decimal("1000000000"))
        # 1 Gwei to Wei
        self.assertEqual(convert_units(1, "gwei", "wei"), Decimal("1000000000"))
        # Fractional ETH
        self.assertEqual(convert_units("0.05", "eth", "gwei"), Decimal("50000000"))
        # 1 Wei to ETH (high precision)
        self.assertEqual(convert_units(1, "wei", "eth"), Decimal("0.000000000000000001"))

    def test_solana_conversions(self):
        """Test Solana Lamport to SOL conversions."""
        # 1 SOL to Lamports
        self.assertEqual(convert_units(1, "sol", "lamports"), Decimal("1000000000"))
        # 1,500,000,000 Lamports to SOL
        self.assertEqual(convert_units(1500000000, "lamports", "sol"), Decimal("1.5"))

    def test_bitcoin_conversions(self):
        """Test Bitcoin Satoshi to BTC conversions."""
        # 1 BTC to Sats
        self.assertEqual(convert_units(1, "btc", "sats"), Decimal("100000000"))
        # 50,000,000 Sats to BTC
        self.assertEqual(convert_units(50000000, "sats", "btc"), Decimal("0.5"))
        # Sats to Bits
        self.assertEqual(convert_units(100, "sats", "bits"), Decimal("1"))

    def test_stellar_conversions(self):
        """Test Stellar Stroop to XLM conversions."""
        # 1 XLM to Stroops
        self.assertEqual(convert_units(1, "xlm", "stroops"), Decimal("10000000"))
        # 25,000,000 Stroops to XLM
        self.assertEqual(convert_units(25000000, "stroops", "xlm"), Decimal("2.5"))

    def test_incompatible_cross_chain_units(self):
        """Attempting to convert across different chains raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            convert_units(1, "wei", "sats")
        self.assertIn("Cannot cross-convert", str(ctx.exception))

    def test_invalid_and_negative_amounts(self):
        """Negative amounts and malformed numeric strings raise ValueError."""
        with self.assertRaises(ValueError):
            convert_units(-10, "eth", "wei")
        with self.assertRaises(ValueError):
            convert_units("not-a-number", "eth", "wei")


class TestGasFeeCalculator(unittest.TestCase):
    def test_eth_transfer_preset(self):
        """Standard 21,000 gas transfer calculation."""
        res = calculate_gas_cost(preset="eth_transfer", gas_price_gwei=20, token_price_usd=2500)
        self.assertEqual(res["gas_limit"], 21000)
        self.assertEqual(res["total_cost_wei"], 420000000000000)
        self.assertEqual(res["total_cost_native"], Decimal("0.00042"))
        self.assertEqual(res["total_cost_usd"], Decimal("1.0500"))

    def test_uniswap_swap_preset(self):
        """DEX swap preset (150,000 gas units)."""
        res = calculate_gas_cost(preset="uniswap_swap", gas_price_gwei=30, token_price_usd=3000)
        self.assertEqual(res["gas_limit"], 150000)
        # 150,000 * 30 Gwei = 4,500,000 Gwei = 0.0045 ETH * 3000 = $13.50
        self.assertEqual(res["total_cost_native"], Decimal("0.0045"))
        self.assertEqual(res["total_cost_usd"], Decimal("13.5000"))

    def test_custom_gas_limit_and_priority_fee(self):
        """EIP-1559 base + priority fee calculation."""
        res = calculate_gas_cost(
            gas_limit=100000,
            gas_price_gwei="25.5",
            priority_fee_gwei="2.0",
            token_price_usd="2000",
        )
        # Total price = 27.5 Gwei
        self.assertEqual(res["total_gas_price_gwei"], Decimal("27.5"))
        self.assertEqual(res["total_cost_native"], Decimal("0.00275"))
        self.assertEqual(res["total_cost_usd"], Decimal("5.5000"))

    def test_invalid_gas_limit(self):
        """Invalid limit raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_gas_cost(gas_limit=-500)
        with self.assertRaises(ValueError):
            calculate_gas_cost(preset="non_existent_preset")

    def test_get_supported_units(self):
        """Check all 4 chains are included in supported units dictionary."""
        units = get_supported_units()
        for chain in ["evm", "solana", "bitcoin", "stellar"]:
            self.assertIn(chain, units)

if __name__ == "__main__":
    unittest.main()
