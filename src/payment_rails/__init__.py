"""
Payment Rails Package: Multi-Chain Balance Auditing & Telemetry.

Provides programmatic querying and auditing of on-chain cryptocurrency wallet
balances across Base EVM, Solana, Bitcoin, and Stellar.
"""

from src.payment_rails.auditor import BalanceAuditor
from src.payment_rails.client import MultiChainBalanceClient
from src.payment_rails.constants import (
    ASSET_INFO,
    BENEFICIARY_WALLETS,
    MOCK_BALANCES,
    PUBLIC_RPC_ENDPOINTS,
)

__all__ = [
    "BENEFICIARY_WALLETS",
    "PUBLIC_RPC_ENDPOINTS",
    "ASSET_INFO",
    "MOCK_BALANCES",
    "MultiChainBalanceClient",
    "BalanceAuditor",
]
