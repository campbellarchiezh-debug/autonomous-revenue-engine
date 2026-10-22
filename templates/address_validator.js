/**
 * Drop-In Multi-Chain Web3 Address Validator & Safety Scanner
 * Standalone, zero-dependency vanilla JavaScript module.
 *
 * Supported Chains:
 * - Base / EVM: Regex, Pure-JS Keccak-256 EIP-55 checksum validation & generation
 * - Solana: Base58 alphabet verification and 32-byte Ed25519 pubkey decoding
 * - Bitcoin: BIP-173 (SegWit v0) & BIP-350 (Taproot v1 Bech32m polymod), Legacy P2PKH/P2SH
 * - Stellar: StrKey RFC 4648 Base32 decoding, version byte 0x30, CRC16-XMODEM checksum
 *
 * Security Scanning:
 * - Invisible Zero-Width character injection scanner
 * - Homoglyph / Mixed-script phishing detector
 * - Vanity address poisoning heuristic analyzer
 *
 * Embedded Beneficiary Rails:
 * - Base EVM: 0xef5766253e2d92e530e301ac22dcb8de78e89c55
 * - Solana:   3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp
 * - Bitcoin:  bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e
 * - Stellar:  GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.AddressValidator = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // --- 1. Pure JavaScript Keccak-256 Implementation (for EIP-55 EVM Checksumming) ---
  const RC = [
    0x0000000000000001n, 0x0000000000008082n, 0x800000000000808an, 0x8000000080008000n,
    0x000000000000808bn, 0x0000000080000001n, 0x8000000080008081n, 0x8000000000008009n,
    0x000000000000008an, 0x0000000000000088n, 0x0000000080008009n, 0x000000008000000an,
    0x000000008000808bn, 0x800000000000008bn, 0x8000000000008089n, 0x8000000000008003n,
    0x8000000000008002n, 0x8000000000000080n, 0x000000000000800an, 0x800000008000000an,
    0x8000000080008081n, 0x8000000080008080n, 0x0000000080000001n, 0x8000000080008008n
  ];

  const r = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14]
  ];

  function rot(x, n) {
    n = BigInt(n % 64);
    const mask = 0xffffffffffffffffn;
    return ((x << n) & mask) | (n > 0n ? (x >> (64n - n)) & mask : 0n);
  }

  function keccak256Hex(asciiStr) {
    const rate = 136; // bytes for Keccak-256
    const padded = [];
    for (let i = 0; i < asciiStr.length; i++) {
      padded.push(asciiStr.charCodeAt(i));
    }

    padded.push(0x01);
    while (padded.length % rate !== rate - 1) {
      padded.push(0x00);
    }
    padded.push(0x80);

    const A = Array.from({ length: 5 }, () => Array(5).fill(0n));

    for (let block = 0; block < padded.length; block += rate) {
      for (let i = 0; i < rate / 8; i++) {
        const x = i % 5;
        const y = Math.floor(i / 5);
        let word = 0n;
        for (let j = 0; j < 8; j++) {
          word |= BigInt(padded[block + i * 8 + j]) << BigInt(j * 8);
        }
        A[x][y] ^= word;
      }

      for (let round_idx = 0; round_idx < 24; round_idx++) {
        const C = Array(5).fill(0n);
        for (let x = 0; x < 5; x++) {
          C[x] = A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4];
        }
        const D = Array(5).fill(0n);
        for (let x = 0; x < 5; x++) {
          D[x] = C[(x + 4) % 5] ^ rot(C[(x + 1) % 5], 1);
        }
        for (let x = 0; x < 5; x++) {
          for (let y = 0; y < 5; y++) {
            A[x][y] ^= D[x];
          }
        }

        const B = Array.from({ length: 5 }, () => Array(5).fill(0n));
        for (let x = 0; x < 5; x++) {
          for (let y = 0; y < 5; y++) {
            B[y][(2 * x + 3 * y) % 5] = rot(A[x][y], r[x][y]);
          }
        }

        for (let x = 0; x < 5; x++) {
          for (let y = 0; y < 5; y++) {
            A[x][y] = B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]);
          }
        }

        A[0][0] ^= RC[round_idx];
      }
    }

    let hex = '';
    for (let y = 0; y < 5; y++) {
      for (let x = 0; x < 5; x++) {
        let word = A[x][y];
        for (let byte = 0; byte < 8; byte++) {
          if (hex.length >= 64) break;
          const b = Number((word >> BigInt(byte * 8)) & 0xffn);
          hex += b.toString(16).padStart(2, '0');
        }
      }
    }
    return hex.slice(0, 64);
  }

  // --- 2. EVM / Base Validator & EIP-55 Checksum ---
  function toChecksumAddress(address) {
    if (typeof address !== 'string') return '';
    const clean = address.trim().toLowerCase().replace(/^0x/, '');
    if (!/^[0-9a-f]{40}$/.test(clean)) {
      throw new Error('Invalid EVM address format for checksumming');
    }
    const hash = keccak256Hex(clean);
    let ret = '0x';
    for (let i = 0; i < clean.length; i++) {
      if (parseInt(hash[i], 16) >= 8) {
        ret += clean[i].toUpperCase();
      } else {
        ret += clean[i];
      }
    }
    return ret;
  }

  function validateEvmAddress(address) {
    if (typeof address !== 'string') {
      return { valid: false, error: 'Input must be a string' };
    }
    const trimmed = address.trim();
    if (!/^0x[0-9a-fA-F]{40}$/.test(trimmed)) {
      return { valid: false, error: 'EVM address must be 42 characters starting with 0x and 40 hex digits' };
    }

    const clean = trimmed.slice(2);
    const isAllLower = clean === clean.toLowerCase();
    const isAllUpper = clean === clean.toUpperCase();
    const expectedChecksum = toChecksumAddress(trimmed);
    const hasValidChecksum = trimmed === expectedChecksum;

    return {
      valid: true,
      chain: 'base_evm',
      address: trimmed,
      checksumAddress: expectedChecksum,
      isChecksummed: hasValidChecksum,
      isUnchecksummed: isAllLower || isAllUpper,
      format: hasValidChecksum ? 'EIP-55 Checksummed' : 'Unchecksummed Hex'
    };
  }

  // --- 3. Solana Base58 Validator ---
  const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

  function decodeBase58(str) {
    const bytes = [];
    for (let i = 0; i < str.length; i++) {
      const c = str[i];
      const val = BASE58_ALPHABET.indexOf(c);
      if (val === -1) return null; // Invalid character

      let carry = val;
      for (let j = 0; j < bytes.length; j++) {
        carry += bytes[j] * 58;
        bytes[j] = carry & 0xff;
        carry >>= 8;
      }
      while (carry > 0) {
        bytes.push(carry & 0xff);
        carry >>= 8;
      }
    }

    // Leading zeros
    let leadingZeros = 0;
    while (leadingZeros < str.length && str[leadingZeros] === '1') {
      leadingZeros++;
    }

    const result = new Uint8Array(leadingZeros + bytes.length);
    for (let i = 0; i < bytes.length; i++) {
      result[result.length - 1 - i] = bytes[i];
    }
    return result;
  }

  function validateSolanaAddress(address) {
    if (typeof address !== 'string') {
      return { valid: false, error: 'Input must be a string' };
    }
    const trimmed = address.trim();
    if (trimmed.length < 32 || trimmed.length > 44) {
      return { valid: false, error: 'Solana address must be between 32 and 44 Base58 characters' };
    }

    const decoded = decodeBase58(trimmed);
    if (!decoded || decoded.length !== 32) {
      return { valid: false, error: 'Invalid Solana address: Must decode to exactly 32-byte Ed25519 public key' };
    }

    return {
      valid: true,
      chain: 'solana',
      address: trimmed,
      byteLength: decoded.length,
      format: 'Solana Base58 Public Key'
    };
  }

  // --- 4. Bitcoin Bech32 / Bech32m (Taproot & SegWit) & Legacy Validator ---
  const BECH32_CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l';
  const BECH32_GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];

  function polymodBech32(values) {
    let chk = 1;
    for (let p = 0; p < values.length; ++p) {
      const top = chk >> 25;
      chk = ((chk & 0x1ffffff) << 5) ^ values[p];
      for (let i = 0; i < 5; ++i) {
        if ((top >> i) & 1) {
          chk ^= BECH32_GEN[i];
        }
      }
    }
    return chk;
  }

  function hrpExpand(hrp) {
    const ret = [];
    for (let p = 0; p < hrp.length; ++p) {
      ret.push(hrp.charCodeAt(p) >> 5);
    }
    ret.push(0);
    for (let p = 0; p < hrp.length; ++p) {
      ret.push(hrp.charCodeAt(p) & 31);
    }
    return ret;
  }

  function verifyBech32Checksum(address) {
    const sep = address.lastIndexOf('1');
    if (sep < 1 || sep + 7 > address.length || address.length > 90) return null;

    const hrp = address.slice(0, sep).toLowerCase();
    if (hrp !== 'bc' && hrp !== 'tb') return null;

    const data = [];
    for (let p = sep + 1; p < address.length; ++p) {
      const d = BECH32_CHARSET.indexOf(address[p].toLowerCase());
      if (d === -1) return null;
      data.push(d);
    }

    const check = polymodBech32(hrpExpand(hrp).concat(data));
    if (check === 1) {
      return { type: 'bech32', witnessVersion: data[0] }; // SegWit v0
    }
    if (check === 0x2bc830a3) {
      return { type: 'bech32m', witnessVersion: data[0] }; // Taproot v1
    }
    return null;
  }

  function validateBitcoinAddress(address) {
    if (typeof address !== 'string') {
      return { valid: false, error: 'Input must be a string' };
    }
    const trimmed = address.trim();

    // Check Bech32 / Bech32m (bc1...)
    if (trimmed.toLowerCase().startsWith('bc1') || trimmed.toLowerCase().startsWith('tb1')) {
      const bechRes = verifyBech32Checksum(trimmed);
      if (bechRes) {
        const isTaproot = trimmed.toLowerCase().startsWith('bc1p') || bechRes.type === 'bech32m';
        return {
          valid: true,
          chain: 'bitcoin',
          address: trimmed,
          encoding: bechRes.type,
          format: isTaproot ? 'Bitcoin Taproot (BIP-341/350 Bech32m)' : 'Bitcoin Native SegWit (BIP-173 Bech32)'
        };
      }
      return { valid: false, error: 'Invalid Bech32/Bech32m Bitcoin checksum' };
    }

    // Check Legacy Base58 (1... or 3...)
    if (/^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(trimmed)) {
      const decoded = decodeBase58(trimmed);
      if (decoded && decoded.length === 25) {
        return {
          valid: true,
          chain: 'bitcoin',
          address: trimmed,
          encoding: 'base58check',
          format: trimmed.startsWith('1') ? 'Bitcoin Legacy P2PKH' : 'Bitcoin Script Hash P2SH'
        };
      }
    }

    return { valid: false, error: 'Unrecognized Bitcoin address format' };
  }

  // --- 5. Stellar StrKey (RFC 4648 Base32 + CRC16) Validator ---
  const BASE32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

  function decodeBase32(str) {
    let bits = 0;
    let value = 0;
    const output = [];

    for (let i = 0; i < str.length; i++) {
      const idx = BASE32_ALPHABET.indexOf(str[i].toUpperCase());
      if (idx === -1) return null;
      value = (value << 5) | idx;
      bits += 5;

      if (bits >= 8) {
        output.push((value >>> (bits - 8)) & 255);
        bits -= 8;
      }
    }
    return new Uint8Array(output);
  }

  function crc16Xmodem(bytes) {
    let crc = 0x0000;
    for (let i = 0; i < bytes.length; i++) {
      crc ^= bytes[i] << 8;
      for (let j = 0; j < 8; j++) {
        if (crc & 0x8000) {
          crc = ((crc << 1) ^ 0x1021) & 0xffff;
        } else {
          crc = (crc << 1) & 0xffff;
        }
      }
    }
    return crc;
  }

  function validateStellarAddress(address) {
    if (typeof address !== 'string') {
      return { valid: false, error: 'Input must be a string' };
    }
    const trimmed = address.trim();
    if (!/^G[2-7A-Z]{55}$/.test(trimmed)) {
      return { valid: false, error: 'Stellar public address must start with G and be 56 characters Base32' };
    }

    const raw = decodeBase32(trimmed);
    if (!raw || raw.length !== 35) {
      return { valid: false, error: 'Decoded Stellar key must be exactly 35 bytes' };
    }

    // Version byte must be 0x30 (account ID)
    if (raw[0] !== 0x30) {
      return { valid: false, error: `Invalid Stellar version byte: 0x${raw[0].toString(16)} (expected 0x30)` };
    }

    const payload = raw.slice(0, 33);
    const expectedChecksum = raw[33] | (raw[34] << 8); // little-endian
    const calculatedChecksum = crc16Xmodem(payload);

    if (expectedChecksum !== calculatedChecksum) {
      return { valid: false, error: 'Stellar CRC16-XMODEM checksum mismatch' };
    }

    return {
      valid: true,
      chain: 'stellar',
      address: trimmed,
      format: 'Stellar StrKey Account ID (ed25519 public key)'
    };
  }

  // --- 6. Security Scanner: Invisible Characters, Homoglyphs, Poisoning ---
  const ZERO_WIDTH_REGEX = /[\u200B\u200C\u200D\uFEFF\u200E\u200F\u202A-\u202E]/;
  const HOMOGLYPH_CYRILLIC_REGEX = /[\u0400-\u04FF]/;
  const HOMOGLYPH_GREEK_REGEX = /[\u0370-\u03FF]/;

  function scanSecurity(address, referenceAddress) {
    const issues = [];
    let isPoisoningRisk = false;

    // Check for zero-width invisible characters
    if (ZERO_WIDTH_REGEX.test(address)) {
      issues.push({
        severity: 'CRITICAL',
        type: 'ZERO_WIDTH_INJECTION',
        message: 'Hidden zero-width Unicode characters detected! Possible copy-paste clipboard hijacking attack.'
      });
    }

    // Check for mixed-script homoglyphs
    if (HOMOGLYPH_CYRILLIC_REGEX.test(address)) {
      issues.push({
        severity: 'HIGH',
        type: 'CYRILLIC_HOMOGLYPH',
        message: 'Cyrillic lookalike characters detected in address! Visual spoofing phishing attempt.'
      });
    }

    if (HOMOGLYPH_GREEK_REGEX.test(address)) {
      issues.push({
        severity: 'HIGH',
        type: 'GREEK_HOMOGLYPH',
        message: 'Greek lookalike characters detected in address! Visual spoofing phishing attempt.'
      });
    }

    // Check for vanity address poisoning attack against a reference address
    if (referenceAddress && typeof referenceAddress === 'string') {
      const ref = referenceAddress.trim().toLowerCase();
      const target = address.trim().toLowerCase();
      if (ref !== target && ref.length >= 10 && target.length >= 10) {
        const prefixLen = 4;
        const suffixLen = 4;
        const samePrefix = ref.slice(0, prefixLen) === target.slice(0, prefixLen);
        const sameSuffix = ref.slice(-suffixLen) === target.slice(-suffixLen);

        if (samePrefix && sameSuffix) {
          isPoisoningRisk = true;
          issues.push({
            severity: 'CRITICAL',
            type: 'ADDRESS_POISONING_ATTACK',
            message: `Address poisoning heuristic alert: First ${prefixLen} and last ${suffixLen} chars match legitimate address, but internal bytes differ!`
          });
        }
      }
    }

    return {
      safe: issues.length === 0,
      issues: issues,
      isPoisoningRisk: isPoisoningRisk
    };
  }

  // --- 7. Master Unified Multi-Chain Validator ---
  function validate(address, options = {}) {
    if (!address || typeof address !== 'string') {
      return {
        valid: false,
        chain: 'unknown',
        error: 'Address string required',
        security: { safe: false, issues: [] }
      };
    }

    const security = scanSecurity(address, options.referenceAddress);

    // Auto-detect chain
    const clean = address.trim();

    // EVM
    if (clean.startsWith('0x') || clean.length === 42) {
      const evmRes = validateEvmAddress(clean);
      return { ...evmRes, security };
    }

    // Bitcoin Bech32 / Bech32m
    if (clean.toLowerCase().startsWith('bc1') || clean.toLowerCase().startsWith('tb1') || /^[13]/.test(clean)) {
      const btcRes = validateBitcoinAddress(clean);
      if (btcRes.valid) return { ...btcRes, security };
    }

    // Stellar
    if (clean.startsWith('G') && clean.length === 56) {
      const xlmRes = validateStellarAddress(clean);
      if (xlmRes.valid) return { ...xlmRes, security };
    }

    // Solana
    if (clean.length >= 32 && clean.length <= 44) {
      const solRes = validateSolanaAddress(clean);
      if (solRes.valid) return { ...solRes, security };
    }

    return {
      valid: false,
      chain: 'unknown',
      error: 'Unrecognized blockchain address format or failed checksum verification',
      security
    };
  }

  // Public API
  return {
    validate,
    validateEvmAddress,
    validateSolanaAddress,
    validateBitcoinAddress,
    validateStellarAddress,
    toChecksumAddress,
    scanSecurity,
    beneficiaryWallets: {
      base: '0xef5766253e2d92e530e301ac22dcb8de78e89c55',
      solana: '3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp',
      bitcoin: 'bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e',
      stellar: 'GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA'
    }
  };
});
