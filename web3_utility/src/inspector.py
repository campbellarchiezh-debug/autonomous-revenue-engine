"""
Multi-Chain Address Safety Inspector & Cryptographic Verification Engine.

Pure Python 3.9 standard library implementation with zero external dependencies.
Supports:
- Base / EVM: Pure-Python Keccak-256 and EIP-55 checksum validation.
- Bitcoin: BIP-350 Bech32m Taproot (bc1p...), BIP-173 Bech32 SegWit (bc1q...),
  and Legacy Base58Check (P2PKH '1...', P2SH '3...').
- Solana: Base58 public key decoding to 32 bytes (Ed25519).
- Stellar: RFC 4648 Base32 StrKey decoding, version byte (0x30), and CRC16-XMODEM.
- Security Checks: Zero-width invisible unicode exploit detection, Cyrillic/Greek
  homoglyph detection, and vanity address poisoning heuristics.
"""

import base64
import hashlib
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

# ==============================================================================
# 1. PURE-PYTHON KECCAK-256 (XKCP / FIPS-202 Reference Implementation)
# ==============================================================================

def _rol64(a: int, n: int) -> int:
    """Rotate 64-bit integer left by n bits."""
    n %= 64
    return ((a >> (64 - n)) + (a << n)) & 0xFFFFFFFFFFFFFFFF

def _keccak_f1600_on_lanes(lanes: List[List[int]]) -> List[List[int]]:
    """Execute Keccak-f[1600] permutation across 5x5 array of 64-bit lanes."""
    R = 1
    for _ in range(24):
        # 1. Theta Step
        C = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
        D = [C[(x + 4) % 5] ^ _rol64(C[(x + 1) % 5], 1) for x in range(5)]
        lanes = [[lanes[x][y] ^ D[x] for y in range(5)] for x in range(5)]

        # 2. Rho and Pi Steps
        x, y = 1, 0
        current = lanes[x][y]
        for t in range(24):
            x, y = y, (2 * x + 3 * y) % 5
            current, lanes[x][y] = lanes[x][y], _rol64(current, (t + 1) * (t + 2) // 2)

        # 3. Chi Step
        for y_idx in range(5):
            T = [lanes[x_idx][y_idx] for x_idx in range(5)]
            for x_idx in range(5):
                lanes[x_idx][y_idx] = T[x_idx] ^ ((~T[(x_idx + 1) % 5]) & T[(x_idx + 2) % 5]) & 0xFFFFFFFFFFFFFFFF

        # 4. Iota Step
        for j in range(7):
            R = ((R << 1) ^ ((R >> 7) * 0x71)) % 256
            if R & 2:
                lanes[0][0] ^= (1 << ((1 << j) - 1))

    return lanes

def _load64(b: bytes) -> int:
    return sum(b[i] << (8 * i) for i in range(8))

def _store64(a: int) -> bytearray:
    return bytearray((a >> (8 * i)) & 0xFF for i in range(8))

def keccak_sponge(rate: int, capacity: int, input_bytes: bytes, delimited_suffix: int, output_len: int) -> bytes:
    """Pure-Python Keccak sponge function."""
    output_bytes = bytearray()
    state = bytearray(200)
    rate_in_bytes = rate // 8
    block_size = 0
    input_offset = 0

    # Absorb
    while input_offset < len(input_bytes):
        block_size = min(len(input_bytes) - input_offset, rate_in_bytes)
        for i in range(block_size):
            state[i] ^= input_bytes[input_offset + i]
        input_offset += block_size
        if block_size == rate_in_bytes:
            lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
            lanes = _keccak_f1600_on_lanes(lanes)
            state = bytearray()
            for y in range(5):
                for x in range(5):
                    state.extend(_store64(lanes[x][y]))
            block_size = 0

    # Padding
    state[block_size] ^= delimited_suffix
    if (delimited_suffix & 0x80) != 0 and block_size == (rate_in_bytes - 1):
        lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
        lanes = _keccak_f1600_on_lanes(lanes)
        state = bytearray()
        for y in range(5):
            for x in range(5):
                state.extend(_store64(lanes[x][y]))

    state[rate_in_bytes - 1] ^= 0x80
    lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
    lanes = _keccak_f1600_on_lanes(lanes)
    state = bytearray()
    for y in range(5):
        for x in range(5):
            state.extend(_store64(lanes[x][y]))

    # Squeeze
    while output_len > 0:
        block_size = min(output_len, rate_in_bytes)
        output_bytes.extend(state[:block_size])
        output_len -= block_size
        if output_len > 0:
            lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
            lanes = _keccak_f1600_on_lanes(lanes)
            state = bytearray()
            for y in range(5):
                for x in range(5):
                    state.extend(_store64(lanes[x][y]))

    return bytes(output_bytes)

def keccak256(data: bytes) -> bytes:
    """
    Compute Ethereum-standard Keccak-256 hash (rate=1088, capacity=512, delimitedSuffix=0x01).
    """
    return keccak_sponge(1088, 512, data, 0x01, 32)


# ==============================================================================
# 2. EVM / BASE (EIP-55 CHECKSUM VALIDATION)
# ==============================================================================

def to_checksum_address(address: str) -> str:
    """
    Convert 20-byte EVM address to canonical EIP-55 checksum format.
    """
    clean = address.strip()
    if clean.startswith("0x") or clean.startswith("0X"):
        clean = clean[2:]
    clean = clean.lower()
    if len(clean) != 40 or not all(c in "0123456789abcdef" for c in clean):
        raise ValueError(f"Invalid EVM address format: '{address}'")

    h = keccak256(clean.encode("ascii")).hex()
    return "0x" + "".join(
        c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(clean)
    )

def check_evm_address(address: str) -> Dict[str, Any]:
    """Validate EVM/Base address and verify EIP-55 checksum."""
    clean = address.strip()
    if not (clean.startswith("0x") or clean.startswith("0X")):
        return {
            "valid": False,
            "chain": "base",
            "address_type": "evm",
            "error": "Address must begin with '0x'",
        }
    body = clean[2:]
    if len(body) != 40 or not all(c in "0123456789abcdefABCDEF" for c in body):
        return {
            "valid": False,
            "chain": "base",
            "address_type": "evm",
            "error": f"Address must contain exactly 40 hex digits (found {len(body)})",
        }

    canonical = to_checksum_address(clean)
    if clean == canonical:
        status = "checksum_valid"
        checksum_valid = True
    elif clean == clean.lower() or clean == clean.upper():
        status = "unchecksummed"
        checksum_valid = False
    else:
        status = "checksum_invalid"
        checksum_valid = False

    return {
        "valid": True,
        "chain": "base",
        "address_type": "evm_eoa_or_contract",
        "status": status,
        "checksum_valid": checksum_valid,
        "canonical_address": canonical,
        "original_address": clean,
        "error": None,
    }


# ==============================================================================
# 3. BASE58 ENCODING/DECODING (BITCOIN LEGACY & SOLANA)
# ==============================================================================

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58decode(s: str) -> bytes:
    """Decode a Base58 string to raw bytes."""
    num = 0
    for char in s:
        idx = B58_ALPHABET.find(char)
        if idx == -1:
            raise ValueError(f"Invalid Base58 character: '{char}'")
        num = num * 58 + idx
    res = []
    while num > 0:
        res.append(num % 256)
        num //= 256
    pad = 0
    for c in s:
        if c == "1":
            pad += 1
        else:
            break
    return b"\x00" * pad + bytes(reversed(res))


# ==============================================================================
# 4. BITCOIN VALIDATION (BECH32 / BECH32M / BASE58CHECK)
# ==============================================================================

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def _bech32_polymod(values: List[int]) -> int:
    GEN = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk

def _bech32_hrp_expand(hrp: str) -> List[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def check_bitcoin_address(address: str) -> Dict[str, Any]:
    """Validate Bitcoin address (Taproot Bech32m, SegWit Bech32, or Base58Check)."""
    addr = address.strip()

    # Case 1: Bech32 / Bech32m (bc1... or tb1...)
    if addr.lower().startswith("bc1") or addr.lower().startswith("tb1"):
        if len(addr) > 90 or len(addr) < 8:
            return {"valid": False, "chain": "bitcoin", "error": "Bech32 address length out of range (8-90)"}
        # Check mixed case violation
        if addr.lower() != addr and addr.upper() != addr:
            return {"valid": False, "chain": "bitcoin", "error": "Bech32 address cannot contain mixed uppercase and lowercase"}

        lower = addr.lower()
        pos = lower.rfind("1")
        hrp = lower[:pos]
        if hrp not in ("bc", "tb"):
            return {"valid": False, "chain": "bitcoin", "error": f"Invalid HRP: '{hrp}'"}

        data = []
        for c in lower[pos + 1 :]:
            idx = BECH32_CHARSET.find(c)
            if idx == -1:
                return {"valid": False, "chain": "bitcoin", "error": f"Invalid Bech32 character: '{c}'"}
            data.append(idx)

        if len(data) < 6:
            return {"valid": False, "chain": "bitcoin", "error": "Bech32 data component too short"}

        polymod = _bech32_polymod(_bech32_hrp_expand(hrp) + data)
        witness_version = data[0]

        if polymod == 0x2BC830A3:
            # BIP-350 Bech32m
            if witness_version == 0:
                return {"valid": False, "chain": "bitcoin", "error": "Witness v0 cannot use Bech32m"}
            addr_type = "taproot_v1" if witness_version == 1 else f"witness_v{witness_version}"
            return {
                "valid": True,
                "chain": "bitcoin",
                "address_type": addr_type,
                "spec": "bech32m",
                "witness_version": witness_version,
                "hrp": hrp,
                "canonical_address": lower,
                "error": None,
            }
        elif polymod == 1:
            # BIP-173 Bech32
            if witness_version != 0:
                return {"valid": False, "chain": "bitcoin", "error": "Witness version >0 must use Bech32m, not Bech32"}
            return {
                "valid": True,
                "chain": "bitcoin",
                "address_type": "segwit_v0",
                "spec": "bech32",
                "witness_version": 0,
                "hrp": hrp,
                "canonical_address": lower,
                "error": None,
            }
        else:
            return {"valid": False, "chain": "bitcoin", "error": "Invalid Bech32/Bech32m checksum"}

    # Case 2: Base58Check (P2PKH '1...', P2SH '3...')
    if len(addr) >= 26 and len(addr) <= 35 and (addr.startswith("1") or addr.startswith("3")):
        try:
            raw = b58decode(addr)
            if len(raw) != 25:
                return {"valid": False, "chain": "bitcoin", "error": f"Base58 decoded byte length {len(raw)} != 25"}
            payload, chk = raw[:-4], raw[-4:]
            computed_chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
            if chk != computed_chk:
                return {"valid": False, "chain": "bitcoin", "error": "Base58Check checksum mismatch"}
            addr_type = "legacy_p2pkh" if raw[0] == 0x00 else "legacy_p2sh"
            return {
                "valid": True,
                "chain": "bitcoin",
                "address_type": addr_type,
                "spec": "base58check",
                "canonical_address": addr,
                "error": None,
            }
        except Exception as e:
            return {"valid": False, "chain": "bitcoin", "error": str(e)}

    return {"valid": False, "chain": "bitcoin", "error": "Unrecognized Bitcoin address format"}


# ==============================================================================
# 5. SOLANA VALIDATION (BASE58 ED25519)
# ==============================================================================

def check_solana_address(address: str) -> Dict[str, Any]:
    """Validate Solana public key (32-byte Ed25519 encoded in Base58)."""
    addr = address.strip()
    if len(addr) < 32 or len(addr) > 44:
        return {
            "valid": False,
            "chain": "solana",
            "error": f"Solana address length must be 32-44 characters (found {len(addr)})",
        }
    try:
        raw = b58decode(addr)
        if len(raw) != 32:
            return {
                "valid": False,
                "chain": "solana",
                "error": f"Decoded Base58 payload is {len(raw)} bytes, expected 32 bytes (Ed25519)",
            }
        return {
            "valid": True,
            "chain": "solana",
            "address_type": "ed25519_public_key",
            "spec": "base58",
            "canonical_address": addr,
            "error": None,
        }
    except Exception as e:
        return {"valid": False, "chain": "solana", "error": str(e)}


# ==============================================================================
# 6. STELLAR VALIDATION (STRKEY RFC4648 BASE32 + CRC16-XMODEM)
# ==============================================================================

def crc16_xmodem(data: bytes) -> int:
    """Calculate 16-bit CRC-XMODEM checksum."""
    crc = 0x0000
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def check_stellar_address(address: str) -> Dict[str, Any]:
    """Validate Stellar account address (StrKey G... with verified CRC16-XMODEM)."""
    addr = address.strip()
    if len(addr) != 56 or not addr.startswith("G"):
        return {
            "valid": False,
            "chain": "stellar",
            "error": f"Stellar public key must be 56 characters starting with 'G' (found length {len(addr)})",
        }
    try:
        pad_len = (8 - (len(addr) % 8)) % 8
        padded = addr + ("=" * pad_len)
        raw = base64.b32decode(padded.encode("ascii"))
        if len(raw) != 35:
            return {
                "valid": False,
                "chain": "stellar",
                "error": f"Decoded StrKey length {len(raw)} bytes != 35 bytes",
            }
        # Version byte: 0x30 = 6 << 3 ('G' in Base32)
        if raw[0] != 0x30:
            return {
                "valid": False,
                "chain": "stellar",
                "error": f"Invalid Stellar version byte: 0x{raw[0]:02x} (expected 0x30)",
            }
        payload = raw[:-2]
        checksum = raw[-2:]
        computed_crc = crc16_xmodem(payload)
        expected_chk = computed_crc.to_bytes(2, byteorder="little")
        if checksum != expected_chk:
            return {
                "valid": False,
                "chain": "stellar",
                "error": f"CRC16 checksum mismatch: expected {expected_chk.hex()}, got {checksum.hex()}",
            }
        return {
            "valid": True,
            "chain": "stellar",
            "address_type": "strkey_account_id",
            "spec": "base32_crc16",
            "canonical_address": addr,
            "error": None,
        }
    except Exception as e:
        return {"valid": False, "chain": "stellar", "error": str(e)}


# ==============================================================================
# 7. SECURITY CHECKS: ZERO-WIDTH, HOMOGLYPHS & VANITY POISONING
# ==============================================================================

ZERO_WIDTH_CODEPOINTS = {
    0x200B: "Zero-Width Space (ZWSP)",
    0x200C: "Zero-Width Non-Joiner (ZWNJ)",
    0x200D: "Zero-Width Joiner (ZWJ)",
    0x200E: "Left-to-Right Mark (LRM)",
    0x200F: "Right-to-Left Mark (RLM)",
    0x2028: "Line Separator (LS)",
    0x2029: "Paragraph Separator (PS)",
    0x202A: "Left-to-Right Embedding (LRE)",
    0x202B: "Right-to-Left Embedding (RLE)",
    0x202C: "Pop Directional Formatting (PDF)",
    0x202D: "Left-to-Right Override (LRO)",
    0x202E: "Right-to-Left Override (RLO)",
    0x2060: "Word Joiner (WJ)",
    0xFEFF: "Zero-Width No-Break Space (BOM)",
    0x00AD: "Soft Hyphen (SHY)",
}

HOMOGLYPH_MAP = {
    # Cyrillic lowercase
    "\u0430": "a", "\u0441": "c", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0445": "x", "\u0443": "y",
    "\u0456": "i", "\u0458": "j",
    # Cyrillic uppercase
    "\u0410": "A", "\u0412": "B", "\u0421": "C", "\u0415": "E", "\u041d": "H", "\u041a": "K", "\u041c": "M",
    "\u041e": "O", "\u0420": "P", "\u0422": "T", "\u0425": "X",
    # Greek
    "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H", "\u0399": "I", "\u039a": "K",
    "\u039c": "M", "\u039d": "N", "\u039f": "O", "\u03a1": "P", "\u03a4": "T", "\u03a5": "Y", "\u03a7": "X",
    "\u03bf": "o", "\u03bd": "v", "\u03c1": "p",
}

def detect_zero_width_chars(text: str) -> List[Dict[str, Any]]:
    """Scan string for zero-width and invisible unicode characters."""
    findings = []
    for idx, char in enumerate(text):
        cp = ord(char)
        if cp in ZERO_WIDTH_CODEPOINTS:
            findings.append({
                "position": idx,
                "codepoint": f"U+{cp:04X}",
                "name": ZERO_WIDTH_CODEPOINTS[cp],
                "char": char,
            })
        elif unicodedata.category(char) in ("Cf", "Cc") and cp not in (9, 10, 13):
            findings.append({
                "position": idx,
                "codepoint": f"U+{cp:04X}",
                "name": unicodedata.name(char, "CONTROL/FORMAT"),
                "char": char,
            })
    return findings

def detect_homoglyphs(text: str) -> List[Dict[str, Any]]:
    """Scan string for homoglyphic characters (mixed-script lookalike exploit)."""
    findings = []
    for idx, char in enumerate(text):
        if char in HOMOGLYPH_MAP:
            target = HOMOGLYPH_MAP[char]
            findings.append({
                "position": idx,
                "char": char,
                "codepoint": f"U+{ord(char):04X}",
                "mimics": target,
                "unicode_name": unicodedata.name(char, "UNKNOWN"),
                "risk": f"Character '{char}' (U+{ord(char):04X}) visually mimics ASCII '{target}'",
            })
        elif ord(char) > 127:
            findings.append({
                "position": idx,
                "char": char,
                "codepoint": f"U+{ord(char):04X}",
                "mimics": "?",
                "unicode_name": unicodedata.name(char, "NON-ASCII"),
                "risk": f"Non-ASCII character '{char}' (U+{ord(char):04X}) detected in address",
            })
    return findings

def check_poisoning_heuristic(
    candidate: str,
    known_addresses: Optional[List[str]] = None,
    prefix_len: int = 5,
    suffix_len: int = 5,
) -> List[Dict[str, Any]]:
    """
    Evaluate if candidate address mimics a known address prefix and suffix
    while differing in middle characters (classic vanity address poisoning attack).
    """
    if not known_addresses:
        return []

    c_clean = candidate.strip().lower()
    alerts = []
    for known in known_addresses:
        k_clean = known.strip().lower()
        if c_clean == k_clean:
            continue
        if len(c_clean) < prefix_len + suffix_len or len(k_clean) < prefix_len + suffix_len:
            continue

        c_prefix, c_suffix = c_clean[:prefix_len], c_clean[-suffix_len:]
        k_prefix, k_suffix = k_clean[:prefix_len], k_clean[-suffix_len:]

        if c_prefix == k_prefix and c_suffix == k_suffix:
            alerts.append({
                "severity": "CRITICAL",
                "attack_type": "VANITY_ADDRESS_POISONING",
                "candidate": candidate,
                "mimicked_known_address": known,
                "matched_prefix": c_prefix,
                "matched_suffix": c_suffix,
                "message": (
                    f"Address poisoning detected! Address begins with '{c_prefix}' "
                    f"and ends with '{c_suffix}', identical to known address '{known}', "
                    "but intermediate bytes differ."
                ),
            })

    return alerts


# ==============================================================================
# 8. MASTER INSPECTION DISPATCHER
# ==============================================================================

def inspect_address(
    address: str,
    chain: Optional[str] = None,
    known_addresses: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Inspect cryptocurrency address across Base/EVM, Bitcoin, Solana, and Stellar.
    Performs security audits including zero-width characters, homoglyphs, and vanity poisoning.
    """
    # 1. Run security audits on raw input before stripping
    zero_width_findings = detect_zero_width_chars(address)
    homoglyph_findings = detect_homoglyphs(address)

    # Strip invisible characters for format analysis
    sanitized = "".join(c for c in address if ord(c) not in ZERO_WIDTH_CODEPOINTS and unicodedata.category(c) not in ("Cf",))
    sanitized = sanitized.strip()

    # 2. Poisoning scan against known addresses
    poisoning_alerts = check_poisoning_heuristic(sanitized, known_addresses)

    warnings: List[str] = []
    security_risks: List[str] = []

    if zero_width_findings:
        security_risks.append(
            f"Detected {len(zero_width_findings)} zero-width invisible character(s)! Malicious copy-paste injection risk."
        )
    if homoglyph_findings:
        security_risks.append(
            f"Detected {len(homoglyph_findings)} homoglyph/non-ASCII character(s)! Visual spoofing risk."
        )
    if poisoning_alerts:
        for alert in poisoning_alerts:
            security_risks.append(alert["message"])

    # 3. Address format validation
    target_chain = chain.lower().strip() if chain else None
    result: Dict[str, Any] = {}

    if target_chain in ("base", "ethereum", "evm", "eth"):
        result = check_evm_address(sanitized)
    elif target_chain in ("bitcoin", "btc"):
        result = check_bitcoin_address(sanitized)
    elif target_chain in ("solana", "sol"):
        result = check_solana_address(sanitized)
    elif target_chain in ("stellar", "xlm"):
        result = check_stellar_address(sanitized)
    else:
        # Auto-detect chain
        if sanitized.startswith("0x") or sanitized.startswith("0X"):
            result = check_evm_address(sanitized)
        elif sanitized.startswith("bc1") or sanitized.startswith("tb1"):
            result = check_bitcoin_address(sanitized)
        else:
            # Check Bitcoin legacy (1... or 3...)
            if sanitized.startswith("1") or sanitized.startswith("3"):
                res_btc = check_bitcoin_address(sanitized)
                if res_btc["valid"]:
                    result = res_btc

            # If not detected as Bitcoin, check Stellar (G... 56 chars)
            if not result and sanitized.startswith("G") and len(sanitized) == 56:
                res_xlm = check_stellar_address(sanitized)
                if res_xlm["valid"]:
                    result = res_xlm

            # If not detected, check Solana (32-44 Base58 chars decoding to 32 bytes)
            if not result:
                res_sol = check_solana_address(sanitized)
                if res_sol["valid"]:
                    result = res_sol

            # If still not detected, check EVM without 0x (40 hex chars)
            if not result and len(sanitized) == 40 and all(c in "0123456789abcdefABCDEF" for c in sanitized):
                result = check_evm_address("0x" + sanitized)
                warnings.append("Missing '0x' prefix auto-corrected.")

            # If still not matched, report failure
            if not result:
                result = {
                    "valid": False,
                    "chain": "unknown",
                    "error": "Address does not match any recognized chain format (Base/EVM, Bitcoin, Solana, Stellar)",
                }

    # Add warnings for unchecksummed EVM addresses
    if result.get("valid") and result.get("chain") == "base":
        if result.get("status") == "unchecksummed":
            warnings.append(
                f"Address is not checksummed (all lowercase/uppercase). Recommended EIP-55 checksum: {result['canonical_address']}"
            )
        elif result.get("status") == "checksum_invalid":
            security_risks.append(
                f"Address has INVALID EIP-55 checksum capitalization! Expected: {result['canonical_address']}"
            )

    return {
        "is_valid": result.get("valid", False) and len(zero_width_findings) == 0 and len(homoglyph_findings) == 0,
        "format_valid": result.get("valid", False),
        "chain": result.get("chain", "unknown"),
        "address_type": result.get("address_type", "unknown"),
        "canonical_address": result.get("canonical_address", sanitized),
        "original_input": address,
        "sanitized_input": sanitized,
        "has_zero_width": len(zero_width_findings) > 0,
        "has_homoglyphs": len(homoglyph_findings) > 0,
        "is_poisoned": len(poisoning_alerts) > 0,
        "zero_width_findings": zero_width_findings,
        "homoglyph_findings": homoglyph_findings,
        "poisoning_alerts": poisoning_alerts,
        "warnings": warnings,
        "security_risks": security_risks,
        "details": result,
    }
