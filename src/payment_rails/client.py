"""
Multi-Chain RPC & REST Client with Adaptive SSL and Failover.

Queries Base EVM, Solana, Bitcoin, and Stellar live networks with resilient failover,
adaptive SSL negotiation, Stellar 404 unfunded handling, and deterministic mock fallback.
Pure Python 3.9+ standard library.
"""

import json
import ssl
import time
import urllib.error
import urllib.request
from decimal import Decimal
from typing import Any, Dict, Optional

from src.payment_rails.constants import (
    ASSET_INFO,
    BENEFICIARY_WALLETS,
    MOCK_BALANCES,
    PUBLIC_RPC_ENDPOINTS,
)


class MultiChainBalanceClient:
    """Resilient balance fetcher across Base, Solana, Bitcoin, and Stellar."""

    def __init__(self, timeout: float = 5.0, simulate: bool = False):
        self.timeout = max(timeout, 0.000001)
        self.simulate = simulate
        self._ssl_ctx = self._create_adaptive_ssl_context()

    @staticmethod
    def _create_adaptive_ssl_context() -> ssl.SSLContext:
        """Create an SSL context adaptable to proxies and sandboxed environments."""
        try:
            return ssl.create_default_context()
        except Exception:
            return ssl._create_unverified_context()

    def get_base_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Fetch Base EVM balance via eth_getBalance."""
        addr = address or BENEFICIARY_WALLETS["base"]
        if self.simulate:
            return self._mock_result("base", addr)

        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [addr, "latest"],
            "id": 1,
        }).encode("utf-8")
        headers = {"Content-Type": "application/json", "User-Agent": "AutonomousRevenueEngine/1.0"}

        for ep in PUBLIC_RPC_ENDPOINTS["base"]:
            try:
                req = urllib.request.Request(ep, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ssl_ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    hex_wei = data.get("result", "0x0")
                    wei = int(hex_wei, 16)
                    eth = Decimal(wei) / Decimal(10**18)
                    return {
                        "address": addr,
                        "chain": "base",
                        "symbol": "ETH",
                        "balance": float(eth),
                        "balance_formatted": f"{eth:.8f} ETH",
                        "raw_balance": hex_wei,
                        "status": "verified",
                        "endpoint": ep,
                    }
            except Exception:
                continue

        # All live endpoints failed, return deterministic mock with fallback notice
        res = self._mock_result("base", addr)
        res["status"] = "simulated_fallback"
        return res

    def get_solana_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Fetch Solana balance via getBalance."""
        addr = address or BENEFICIARY_WALLETS["solana"]
        if self.simulate:
            return self._mock_result("solana", addr)

        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": "getBalance",
            "params": [addr],
            "id": 1,
        }).encode("utf-8")
        headers = {"Content-Type": "application/json", "User-Agent": "AutonomousRevenueEngine/1.0"}

        for ep in PUBLIC_RPC_ENDPOINTS["solana"]:
            try:
                req = urllib.request.Request(ep, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ssl_ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    val = data.get("result", {})
                    lamports = val.get("value", 0) if isinstance(val, dict) else int(val)
                    sol = Decimal(lamports) / Decimal(10**9)
                    return {
                        "address": addr,
                        "chain": "solana",
                        "symbol": "SOL",
                        "balance": float(sol),
                        "balance_formatted": f"{sol:.9f} SOL",
                        "raw_balance": lamports,
                        "status": "verified",
                        "endpoint": ep,
                    }
            except Exception:
                continue

        res = self._mock_result("solana", addr)
        res["status"] = "simulated_fallback"
        return res

    def get_bitcoin_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Fetch Bitcoin balance from public REST APIs."""
        addr = address or BENEFICIARY_WALLETS["bitcoin"]
        if self.simulate:
            return self._mock_result("bitcoin", addr)

        headers = {"User-Agent": "AutonomousRevenueEngine/1.0"}

        for ep in PUBLIC_RPC_ENDPOINTS["bitcoin"]:
            try:
                if "mempool.space" in ep or "blockstream.info" in ep:
                    url = f"{ep}/address/{addr}"
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=self.timeout, context=self._ssl_ctx) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        chain_stats = data.get("chain_stats", {})
                        mempool_stats = data.get("mempool_stats", {})
                        funded = chain_stats.get("funded_txo_sum", 0) + mempool_stats.get("funded_txo_sum", 0)
                        spent = chain_stats.get("spent_txo_sum", 0) + mempool_stats.get("spent_txo_sum", 0)
                        sats = funded - spent
                        btc = Decimal(sats) / Decimal(10**8)
                        return {
                            "address": addr,
                            "chain": "bitcoin",
                            "symbol": "BTC",
                            "balance": float(btc),
                            "balance_formatted": f"{btc:.8f} BTC",
                            "raw_balance": sats,
                            "status": "verified",
                            "endpoint": ep,
                        }
                elif "blockchain.info" in ep:
                    url = f"{ep}/{addr}"
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=self.timeout, context=self._ssl_ctx) as resp:
                        sats = int(resp.read().decode("utf-8").strip())
                        btc = Decimal(sats) / Decimal(10**8)
                        return {
                            "address": addr,
                            "chain": "bitcoin",
                            "symbol": "BTC",
                            "balance": float(btc),
                            "balance_formatted": f"{btc:.8f} BTC",
                            "raw_balance": sats,
                            "status": "verified",
                            "endpoint": ep,
                        }
            except Exception:
                continue

        res = self._mock_result("bitcoin", addr)
        res["status"] = "simulated_fallback"
        return res

    def get_stellar_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Fetch Stellar balance via Horizon REST API with 404 unfunded resilience."""
        addr = address or BENEFICIARY_WALLETS["stellar"]
        if self.simulate:
            return self._mock_result("stellar", addr)

        headers = {"User-Agent": "AutonomousRevenueEngine/1.0", "Accept": "application/json"}

        for ep in PUBLIC_RPC_ENDPOINTS["stellar"]:
            url = f"{ep}/accounts/{addr}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ssl_ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    native_balance = "0.0000000"
                    for item in data.get("balances", []):
                        if item.get("asset_type") == "native":
                            native_balance = item.get("balance", "0.0000000")
                            break
                    xlm = Decimal(native_balance)
                    return {
                        "address": addr,
                        "chain": "stellar",
                        "symbol": "XLM",
                        "balance": float(xlm),
                        "balance_formatted": f"{xlm:.7f} XLM",
                        "raw_balance": native_balance,
                        "status": "verified",
                        "endpoint": ep,
                    }
            except urllib.error.HTTPError as e:
                # Intercept 404 Resource Missing: Unfunded / unactivated account
                if e.code == 404:
                    return {
                        "address": addr,
                        "chain": "stellar",
                        "symbol": "XLM",
                        "balance": 0.0,
                        "balance_formatted": "0.0000000 XLM",
                        "raw_balance": "0.0000000",
                        "status": "unfunded",
                        "endpoint": ep,
                        "note": "Account not yet created on ledger (unfunded / resource_missing)",
                    }
                continue
            except Exception:
                continue

        res = self._mock_result("stellar", addr)
        res["status"] = "simulated_fallback"
        return res

    def _mock_result(self, chain: str, address: str) -> Dict[str, Any]:
        mock = MOCK_BALANCES[chain]
        info = ASSET_INFO[chain]
        return {
            "address": address,
            "chain": chain,
            "symbol": info["symbol"],
            "balance": mock["balance"],
            "balance_formatted": mock["formatted"],
            "raw_balance": mock["raw"],
            "status": mock["status"],
            "endpoint": "offline://deterministic_mock",
        }
