"""
Unit tests for Web3 Multi-Chain Address Inspector & Cryptographic Verification.
"""

import unittest
from web3_utility.src.inspector import (
    b58decode,
    check_bitcoin_address,
    check_evm_address,
    check_poisoning_heuristic,
    check_solana_address,
    check_stellar_address,
    crc16_xmodem,
    detect_homoglyphs,
    detect_zero_width_chars,
    inspect_address,
    keccak256,
    to_checksum_address,
)

class TestKeccak256(unittest.TestCase):
    def test_empty_string(self):
        """Keccak-256 of empty bytes matches NIST/Ethereum test vector."""
        expected = "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
        self.assertEqual(keccak256(b"").hex(), expected)

    def test_standard_ascii_string(self):
        """Keccak-256 of 'The quick brown fox jumps over the lazy dog'."""
        expected = "4d741b6f1eb29cb2a9b9911c82f56fa8d73b04959d3d9d222895df6c0b28aa15"
        self.assertEqual(keccak256(b"The quick brown fox jumps over the lazy dog").hex(), expected)


class TestEVMChecksum(unittest.TestCase):
    def test_eip55_official_test_vectors(self):
        """Test standard EIP-55 vectors."""
        vectors = [
            ("0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed", "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"),
            ("0xfb6916095ca1df60bb79ce92ce3ea74c37c5d359", "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359"),
            ("0xdbf03b407c01e7cd3cbea99509d93f8dddc8c6fb", "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB"),
            ("0xd1220a0cf47c7b9be7a2e6ba89f429762e7b9adb", "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb"),
        ]
        for unchecksummed, expected in vectors:
            with self.subTest(addr=unchecksummed):
                self.assertEqual(to_checksum_address(unchecksummed), expected)

    def test_beneficiary_base_wallet(self):
        """Test user's canonical Base EVM beneficiary wallet."""
        base_addr = "0xef5766253e2d92e530e301ac22dcb8de78e89c55"
        expected = "0xeF5766253e2D92E530e301aC22dcB8DE78E89C55"
        self.assertEqual(to_checksum_address(base_addr), expected)
        res = check_evm_address(base_addr)
        self.assertTrue(res["valid"])
        self.assertEqual(res["canonical_address"], expected)
        self.assertEqual(res["status"], "unchecksummed")

    def test_invalid_evm_address(self):
        """Invalid hex length or characters."""
        res_short = check_evm_address("0x1234")
        self.assertFalse(res_short["valid"])
        res_nonhex = check_evm_address("0xef5766253e2d92e530e301ac22dcb8de78e89cZZ")
        self.assertFalse(res_nonhex["valid"])


class TestBitcoinValidation(unittest.TestCase):
    def test_taproot_beneficiary_wallet(self):
        """User's canonical Bitcoin Taproot wallet (bc1p... Bech32m)."""
        btc_addr = "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e"
        res = check_bitcoin_address(btc_addr)
        self.assertTrue(res["valid"])
        self.assertEqual(res["spec"], "bech32m")
        self.assertEqual(res["address_type"], "taproot_v1")
        self.assertEqual(res["witness_version"], 1)

    def test_native_segwit_address(self):
        """Standard Bech32 SegWit v0 address (bc1q...)."""
        segwit_addr = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        res = check_bitcoin_address(segwit_addr)
        self.assertTrue(res["valid"])
        self.assertEqual(res["spec"], "bech32")
        self.assertEqual(res["address_type"], "segwit_v0")
        self.assertEqual(res["witness_version"], 0)

    def test_legacy_base58check_address(self):
        """Standard Bitcoin legacy P2PKH address."""
        legacy_addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        res = check_bitcoin_address(legacy_addr)
        self.assertTrue(res["valid"])
        self.assertEqual(res["address_type"], "legacy_p2pkh")

    def test_invalid_bitcoin_checksum(self):
        """Corrupted Bech32 checksum fails validation."""
        corrupted = "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk8099"
        res = check_bitcoin_address(corrupted)
        self.assertFalse(res["valid"])


class TestSolanaValidation(unittest.TestCase):
    def test_solana_beneficiary_wallet(self):
        """User's canonical Solana wallet (3HLD... 32-byte Ed25519)."""
        sol_addr = "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp"
        res = check_solana_address(sol_addr)
        self.assertTrue(res["valid"])
        self.assertEqual(res["address_type"], "ed25519_public_key")
        self.assertEqual(len(b58decode(sol_addr)), 32)

    def test_invalid_solana_address(self):
        """Invalid Base58 character or length."""
        res_char = check_solana_address("3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMys00") # '0' is not in Base58
        self.assertFalse(res_char["valid"])
        res_short = check_solana_address("123456789")
        self.assertFalse(res_short["valid"])


class TestStellarValidation(unittest.TestCase):
    def test_stellar_beneficiary_wallet(self):
        """User's canonical Stellar StrKey wallet (GBS2... with CRC16-XMODEM)."""
        xlm_addr = "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA"
        res = check_stellar_address(xlm_addr)
        self.assertTrue(res["valid"])
        self.assertEqual(res["address_type"], "strkey_account_id")
        self.assertEqual(res["spec"], "base32_crc16")

    def test_invalid_stellar_address(self):
        """Corrupted Base32 or checksum."""
        corrupted = "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2ZZ"
        res = check_stellar_address(corrupted)
        self.assertFalse(res["valid"])


class TestSecurityAudits(unittest.TestCase):
    def test_zero_width_detection(self):
        """Scan for zero-width characters."""
        clean = "0xef5766253e2d92e530e301ac22dcb8de78e89c55"
        poisoned = clean[:10] + "\u200b" + clean[10:] + "\ufeff"
        findings = detect_zero_width_chars(poisoned)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["codepoint"], "U+200B")
        self.assertEqual(findings[1]["codepoint"], "U+FEFF")

    def test_homoglyph_detection(self):
        """Scan for Cyrillic and Greek homoglyphs."""
        text = "0x" + "\u0430" + "f5766253e2d92e530e301ac22dcb8de78e89c55" # Cyrillic 'a'
        findings = detect_homoglyphs(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["mimics"], "a")
        self.assertEqual(findings[0]["codepoint"], "U+0430")

    def test_vanity_address_poisoning(self):
        """Scan for vanity address poisoning matching prefix and suffix."""
        known = "0xef5766253e2d92e530e301ac22dcb8de78e89c55"
        attacker = "0xef57000000000000000000000000000078e89c55" # starts with 0xef57, ends with e89c55
        alerts = check_poisoning_heuristic(attacker, known_addresses=[known], prefix_len=5, suffix_len=5)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["severity"], "CRITICAL")
        self.assertEqual(alerts[0]["attack_type"], "VANITY_ADDRESS_POISONING")

    def test_master_inspect_integration(self):
        """Integration test on inspect_address dispatcher."""
        # Valid address
        res_valid = inspect_address("0xeF5766253e2D92E530e301aC22dcB8DE78E89C55")
        self.assertTrue(res_valid["is_valid"])
        self.assertTrue(res_valid["format_valid"])
        self.assertFalse(res_valid["has_zero_width"])
        self.assertFalse(res_valid["has_homoglyphs"])

        # Poisoned address with zero-width character
        zw_addr = "0xeF5766253e2D92E530e301aC22dcB8DE78E89C55" + "\u200c"
        res_zw = inspect_address(zw_addr)
        self.assertFalse(res_zw["is_valid"])
        self.assertTrue(res_zw["has_zero_width"])

if __name__ == "__main__":
    unittest.main()
