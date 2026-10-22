"""
Multi-Chain Balance Auditor Engine.

Coordinates multi-chain ledger polling across Base, Solana, Bitcoin, and Stellar,
aggregating verified receipts and mock simulations into structured telemetry reports.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.payment_rails.client import MultiChainBalanceClient
from src.payment_rails.constants import BENEFICIARY_WALLETS


class BalanceAuditor:
    """Audits on-chain wallet balances across all supported rails."""

    def __init__(self, timeout: float = 5.0, simulate: bool = False):
        self.client = MultiChainBalanceClient(timeout=timeout, simulate=simulate)

    def audit_chain(self, chain: str) -> Dict[str, Any]:
        """Audit balance for a specific chain."""
        chain_lower = chain.lower().strip()
        if chain_lower == "base":
            return self.client.get_base_balance()
        elif chain_lower == "solana":
            return self.client.get_solana_balance()
        elif chain_lower == "bitcoin":
            return self.client.get_bitcoin_balance()
        elif chain_lower == "stellar":
            return self.client.get_stellar_balance()
        else:
            raise ValueError(f"Unsupported chain: {chain}")

    def audit_all(self) -> Dict[str, Dict[str, Any]]:
        """Audit balances across all canonical chains."""
        return {
            "base": self.audit_chain("base"),
            "solana": self.audit_chain("solana"),
            "bitcoin": self.audit_chain("bitcoin"),
            "stellar": self.audit_chain("stellar"),
        }

    def generate_report(self, chain: str = "all") -> Dict[str, Any]:
        """Generate structured audit report dict."""
        if chain == "all":
            balances = self.audit_all()
        else:
            balances = {chain.lower(): self.audit_chain(chain)}

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "chain_filter": chain,
            "balances": balances,
            "total_chains_audited": len(balances),
        }
