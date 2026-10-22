#!/usr/bin/env python3
"""
Live Programmatic Multi-Chain Balance Auditing Script.

Feature F12: Queries Base EVM, Solana, Bitcoin, and Stellar public RPCs
to report verified wallet receipts for canonical revenue beneficiary addresses.
Pure Python 3.9+ standard library with zero external dependencies.

Includes:
- Multi-endpoint failover lists (mainnet.base.org, base.llamarpc.com, api.mainnet-beta.solana.com, solana.publicnode.com, etc.)
- Adaptive SSL context creation for corporate/sandboxed proxies
- Stellar Horizon 404 unfunded / resource_missing handling
- Deterministic offline mock simulation mode with graceful fallback
"""

import argparse
import ast
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.payment_rails.auditor import BalanceAuditor
from src.payment_rails.constants import BENEFICIARY_WALLETS, PUBLIC_RPC_ENDPOINTS


def format_table(balances: Dict[str, Dict[str, Any]]) -> str:
    """Format balances into clean terminal ledger table."""
    lines = []
    lines.append("╔═════════════════════════════════════════════════════════════════════════════════════════════════╗")
    lines.append("║                           MULTI-CHAIN ON-CHAIN BALANCE AUDIT LEDGER                             ║")
    lines.append("╚═════════════════════════════════════════════════════════════════════════════════════════════════╝")
    header = f"{'CHAIN':<9} {'ASSET':<6} {'BALANCE':<16} {'STATUS':<18} {'ADDRESS'}"
    lines.append(header)
    lines.append("─" * 95)
    for chain, data in balances.items():
        chain_name = chain.upper()
        asset = data.get("symbol", "N/A")
        bal = data.get("balance_formatted", str(data.get("balance", 0.0)))
        status = data.get("status", "unknown")
        addr = data.get("address", "")
        lines.append(f"{chain_name:<9} {asset:<6} {bal:<16} {status:<18} {addr}")
    lines.append("─" * 95)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Verify multi-chain cryptocurrency wallet balances across Base, Solana, Bitcoin, and Stellar."
    )
    parser.add_argument(
        "--chain",
        choices=["base", "solana", "bitcoin", "stellar", "all"],
        default="all",
        help="Target blockchain network to verify (default: all)",
    )
    parser.add_argument(
        "--simulate",
        "--offline",
        action="store_true",
        dest="simulate",
        help="Execute in offline/simulated mode using deterministic ledger mock data",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw structured JSON report to stdout (strict machine-readable format)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP/RPC network socket timeout in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Export JSON balance audit report to specified file path",
    )

    args = parser.parse_args()

    try:
        auditor = BalanceAuditor(timeout=args.timeout, simulate=args.simulate)
        report = auditor.generate_report(chain=args.chain)
    except Exception as e:
        # Fallback in extreme conditions to prevent unhandled crash
        if args.json:
            print(json.dumps({"error": str(e), "balances": {}}))
        else:
            print(f"Error during balance audit: {e}", file=sys.stderr)
        return 1

    if args.export:
        try:
            with open(args.export, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to export report to {args.export}: {e}", file=sys.stderr)

    if args.json:
        # Strict JSON output: only the JSON string on stdout
        print(json.dumps(report, indent=2))
        return 0

    print(format_table(report["balances"]))
    print(f"\nAudit completed at: {report['timestamp']}")
    print(f"Total chains checked: {report['total_chains_audited']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
