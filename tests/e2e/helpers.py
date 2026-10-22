"""
E2E Test Suite Helpers & Reference Oracles.
Provides canonical paths, test vectors, reference algorithms, and validation utilities.
"""

import os
import sys
import re
import json
import base64
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CANONICAL_WALLETS = {
    "base": "0xef5766253e2d92e530e301ac22dcb8de78e89c55",
    "base_checksum": "0xeF5766253e2D92E530e301aC22dcB8DE78E89C55",
    "solana": "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp",
    "bitcoin": "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e",
    "stellar": "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA"
}

def get_path(*subpaths):
    return os.path.join(PROJECT_ROOT, *subpaths)

# Common project paths
PATH_B2B_DATASET_JSON = get_path("data", "b2b_leads", "leads_dataset.json")
PATH_B2B_DATASET_CSV = get_path("data", "b2b_leads", "leads_dataset.csv")
PATH_B2B_SCHEMA_JSON = get_path("data", "b2b_leads", "schema", "b2b_leads_schema.json")
PATH_B2B_PITCHES_DIR = get_path("data", "b2b_leads", "pitches")
PATH_B2B_AUDITS_DIR = get_path("data", "b2b_leads", "audits")
PATH_B2B_SRC_DIR = get_path("src", "b2b_pipeline")

PATH_WEB3_CLI = get_path("web3_utility", "run_cli.py")
PATH_WEB3_SRC_DIR = get_path("web3_utility", "src")
PATH_WEB3_WEB_SPA = get_path("web3_utility", "src", "web", "index.html")
PATH_WEB3_TESTS_DIR = get_path("web3_utility", "tests")

PATH_CALCULATOR_SPA = get_path("digital_assets", "web3_saas_calculator", "index.html")
PATH_RPC_TEMPLATE = get_path("templates", "rpc_client_template.py")
PATH_VALIDATOR_TEMPLATE = get_path("templates", "address_validator.js")

PATH_README = get_path("README.md")
PATH_LICENSE = get_path("LICENSE")
PATH_SETUP = get_path("SETUP.md")
PATH_CONTRIBUTING = get_path("CONTRIBUTING.md")
PATH_CHANGELOG = get_path("CHANGELOG.md")
PATH_DOCS_PREVIEW = get_path("docs", "PREVIEW.md")
PATH_DOCS_ARCH = get_path("docs", "ARCHITECTURE.md")
PATH_DOCS_SPONSOR = get_path("docs", "SPONSORSHIP.md")
PATH_FUNDING_YML = get_path(".github", "FUNDING.yml")

PATH_VERIFY_BALANCES = get_path("verify_balances.py")
PATH_AUDIT_PIPELINE = get_path("audit_pipeline.py")

# Reference Cryptographic Algorithms (Oracles for validation)

def reference_keccak256(data: bytes) -> bytes:
    RC = [
        0x0000000000000001, 0x0000000000008082, 0x800000000000808a, 0x8000000080008000,
        0x000000000000808b, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008a, 0x0000000000000088, 0x0000000080008009, 0x000000008000000a,
        0x000000008000808b, 0x800000000000008b, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800a, 0x800000008000000a,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008
    ]
    r = [
        [0, 36, 3, 41, 18],
        [1, 44, 10, 45, 2],
        [62, 6, 43, 15, 61],
        [28, 55, 25, 21, 56],
        [27, 20, 39, 8, 14]
    ]
    def rot(x, n):
        n %= 64
        return ((x << n) & 0xffffffffffffffff) | (x >> (64 - n) if n else 0)

    rate = 136
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != rate - 1:
        padded.append(0x00)
    padded.append(0x80)

    A = [[0]*5 for _ in range(5)]
    for block in range(0, len(padded), rate):
        for i in range(rate // 8):
            x = i % 5
            y = i // 5
            A[x][y] ^= int.from_bytes(padded[block + i*8: block + (i+1)*8], 'little')
        for round_idx in range(24):
            C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
            D = [C[(x-1)%5] ^ rot(C[(x+1)%5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    A[x][y] ^= D[x]
            B = [[0]*5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    B[y][(2*x + 3*y)%5] = rot(A[x][y], r[x][y])
            for x in range(5):
                for y in range(5):
                    A[x][y] = B[x][y] ^ ((~B[(x+1)%5][y]) & B[(x+2)%5][y])
            A[0][0] ^= RC[round_idx]
    out = bytearray()
    for y in range(5):
        for x in range(5):
            out.extend(A[x][y].to_bytes(8, 'little'))
            if len(out) >= 32:
                return bytes(out[:32])

def reference_to_checksum_address(addr: str) -> str:
    clean = addr.lower().replace('0x', '')
    if len(clean) != 40 or not all(c in '0123456789abcdef' for c in clean):
        raise ValueError("Invalid hex address")
    h = reference_keccak256(clean.encode('ascii')).hex()
    return '0x' + ''.join(c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(clean))

def reference_verify_bech32m(address: str) -> bool:
    CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    pos = address.rfind('1')
    if pos < 1 or pos + 7 > len(address) or len(address) > 90:
        return False
    hrp = address[:pos].lower()
    if hrp not in ('bc', 'tb'):
        return False
    data = []
    for c in address[pos+1:].lower():
        idx = CHARSET.find(c)
        if idx == -1:
            return False
        data.append(idx)
    
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    expanded_hrp = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]
    for v in expanded_hrp + data:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    # BIP-350 bech32m returns 0x2bc830a3
    return chk == 0x2bc830a3

def reference_verify_solana_address(address: str) -> bool:
    ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    if len(address) < 32 or len(address) > 44:
        return False
    num = 0
    for char in address:
        idx = ALPHABET.find(char)
        if idx == -1:
            return False
        num = num * 58 + idx
    res = []
    while num > 0:
        res.append(num % 256)
        num //= 256
    pad = 0
    for c in address:
        if c == '1':
            pad += 1
        else:
            break
    decoded = b'\x00' * pad + bytes(reversed(res))
    return len(decoded) == 32

def reference_verify_stellar_address(address: str) -> bool:
    if len(address) != 56 or not address.startswith('G'):
        return False
    try:
        raw = base64.b32decode(address)
        if len(raw) != 35 or raw[0] != 0x30:
            return False
        payload, checksum = raw[:-2], raw[-2:]
        crc = 0x0000
        for b in payload:
            crc ^= (b << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xffff
                else:
                    crc = (crc << 1) & 0xffff
        expected_chk = crc.to_bytes(2, 'little')
        return checksum == expected_chk
    except Exception:
        return False

def count_words(text: str) -> int:
    # Filter out markdown formatting headers/links and count spoken words
    clean = re.sub(r'#.*', '', text)
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)
    clean = re.sub(r'[*_`>]', '', clean)
    tokens = re.findall(r"\b[A-Za-z0-9'-]+\b", clean)
    return len(tokens)

def run_command_in_project(args, timeout=10):
    try:
        proc = subprocess.run(
            [sys.executable] + args,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", f"TimeoutExpired after {timeout}s: {e}"
    except Exception as e:
        return -2, "", str(e)
