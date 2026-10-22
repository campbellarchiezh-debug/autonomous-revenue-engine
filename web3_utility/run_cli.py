#!/usr/bin/env python3
"""
Web3 Developer Micro-Utility CLI Suite.

Standalone CLI tool providing:
- Address Safety & Cryptographic Inspector (Base/EVM, Bitcoin, Solana, Stellar)
- Multi-Chain RPC Health & Latency Monitor
- Cryptocurrency Unit & Gas Fee Calculator
- Direct Multi-Chain Payment & Tip Hub
"""

import argparse
import json
import os
import sys
from decimal import Decimal
from typing import Any, List, Optional

# Ensure project root is in sys.path for direct execution
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from web3_utility.src.inspector import (
    inspect_address,
    to_checksum_address,
)
from web3_utility.src.rpc_monitor import (
    RPCMonitor,
    benchmark_all,
    benchmark_chain,
)
from web3_utility.src.converter import (
    calculate_gas_cost,
    convert_units,
    format_decimal,
    GAS_PRESETS,
)

# Canonical beneficiary wallet addresses for autonomous revenue deposition
BENEFICIARY_WALLETS = {
    "Base EVM": "0xef5766253e2d92e530e301ac22dcb8de78e89c55",
    "Solana": "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp",
    "Bitcoin": "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e",
    "Stellar": "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA",
}

# ANSI Colors for terminal output
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
MAGENTA = "\033[35m"
DIM = "\033[2m"

def print_banner():
    banner = f"""{CYAN}{BOLD}
╔═══════════════════════════════════════════════════════════════════╗
║          WEB3 MICRO-UTILITY & DEVELOPER TOOLS SUITE               ║
║  Zero-Dependency Multi-Chain Security, RPC Telemetry & Calculator ║
╚═══════════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)

def display_tip_info(as_json: bool = False):
    """Display non-custodial multi-chain tipping and sponsorship information."""
    if as_json:
        print(json.dumps({
            "message": "Autonomous Revenue Engine Beneficiary Wallets",
            "wallets": BENEFICIARY_WALLETS,
            "supported_networks": ["Base", "Ethereum", "Solana", "Bitcoin", "Stellar"],
        }, indent=2))
        return

    print(f"\n{GREEN}{BOLD}════════════════ MULTI-CHAIN PAYMENT & SPONSOR RAILS ════════════════{RESET}")
    print(f"{DIM}Direct, non-custodial developer support & micro-grants:{RESET}\n")
    for net, addr in BENEFICIARY_WALLETS.items():
        if net == "Base EVM":
            chk = to_checksum_address(addr)
            print(f"  {CYAN}{BOLD}[{net}]{RESET} {chk}")
        else:
            print(f"  {CYAN}{BOLD}[{net}]{RESET} {addr}")
    print(f"\n{YELLOW}Thank you for supporting autonomous open-source Web3 developer infrastructure!{RESET}\n")

def handle_inspect(args):
    whitelist = [w.strip() for w in args.whitelist.split(",")] if args.whitelist else list(BENEFICIARY_WALLETS.values())
    result = inspect_address(args.address, chain=args.chain, known_addresses=whitelist)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print_banner()
    print(f"\n{BOLD}Target Address:{RESET} {result['original_input']}")
    
    if result["format_valid"]:
        print(f"{BOLD}Detected Chain:{RESET} {GREEN}{result['chain'].upper()}{RESET} ({result['address_type']})")
        print(f"{BOLD}Canonical Address:{RESET} {CYAN}{result['canonical_address']}{RESET}")
    else:
        print(f"{BOLD}Format Status:{RESET} {RED}INVALID FORMAT{RESET}")
        print(f"{RED}Error:{RESET} {result['details'].get('error', 'Unrecognized address format')}")

    # Security Warnings
    if result["has_zero_width"]:
        print(f"\n{RED}{BOLD}🚨 CRITICAL SECURITY ALERT: Zero-Width Unicode Detected!{RESET}")
        for item in result["zero_width_findings"]:
            print(f"   - Position {item['position']}: {item['codepoint']} ({item['name']})")
    
    if result["has_homoglyphs"]:
        print(f"\n{RED}{BOLD}🚨 CRITICAL SECURITY ALERT: Homoglyph Phishing Detected!{RESET}")
        for item in result["homoglyph_findings"]:
            print(f"   - {item['risk']}")

    if result["is_poisoned"]:
        print(f"\n{RED}{BOLD}🚨 CRITICAL SECURITY ALERT: Vanity Poisoning Heuristic Triggered!{RESET}")
        for alert in result["poisoning_alerts"]:
            print(f"   - {alert['message']}")

    if result["warnings"]:
        print(f"\n{YELLOW}{BOLD}⚠️  Warnings:{RESET}")
        for w in result["warnings"]:
            print(f"   - {w}")

    if result["is_valid"]:
        print(f"\n{GREEN}{BOLD}✓ Address is Cryptographically Valid & Free of Injected Exploits.{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}✗ Address Failed Safety Validation! Do NOT Send Funds!{RESET}\n")
        return 1

def handle_monitor(args):
    monitor = RPCMonitor(timeout=args.timeout, force_offline=args.offline)

    if args.chain:
        results = {args.chain: monitor.benchmark_chain(args.chain, offline=args.offline)}
    else:
        results = monitor.benchmark_all(offline=args.offline)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    print_banner()
    mode_str = f"{YELLOW}[Deterministic Mock Mode]{RESET}" if args.offline else f"{GREEN}[Live Benchmark Mode]{RESET}"
    print(f"\n{BOLD}Multi-Chain RPC Telemetry {mode_str}\n")
    print(f"{'CHAIN':<12} {'STATUS':<10} {'LATENCY':<12} {'BLOCK / SLOT':<16} {'CHAIN ID':<16} {'ENDPOINT'}")
    print("─" * 80)

    for chain, data in results.items():
        if data.get("healthy"):
            status = f"{GREEN}ONLINE{RESET}"
            lat = f"{data['latency_ms']:.1f} ms"
            block = str(data.get("block_height", "N/A"))
            cid = str(data.get("chain_id", "N/A"))
            ep = data.get("endpoint_used", "")
            if len(ep) > 28:
                ep = ep[:25] + "..."
            print(f"{chain.upper():<12} {status:<19} {lat:<12} {block:<16} {cid:<16} {DIM}{ep}{RESET}")
        else:
            status = f"{RED}OFFLINE{RESET}"
            err = data.get("error", "Unknown error")
            print(f"{chain.upper():<12} {status:<19} {'--':<12} {'--':<16} {'--':<16} {err}")

    print("\n")
    return 0

def handle_convert(args):
    try:
        converted = convert_units(args.amount, args.from_unit, args.to_unit, chain=args.chain)
        formatted_result = format_decimal(converted)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"{RED}Error: {e}{RESET}")
        return 1

    if args.json:
        print(json.dumps({
            "amount": str(args.amount),
            "from_unit": args.from_unit,
            "to_unit": args.to_unit,
            "result": formatted_result,
        }, indent=2))
        return 0

    print(f"\n{BOLD}{args.amount} {args.from_unit.upper()}{RESET} = {GREEN}{BOLD}{formatted_result} {args.to_unit.upper()}{RESET}\n")
    return 0

def handle_gas(args):
    try:
        # Check if first arg is an integer limit or preset name
        preset = None
        gas_limit = None
        if args.preset_or_limit.isdigit():
            gas_limit = int(args.preset_or_limit)
        else:
            preset = args.preset_or_limit

        cost = calculate_gas_cost(
            gas_limit=gas_limit,
            gas_price_gwei=args.gas_price_gwei,
            token_price_usd=args.eth_price,
            preset=preset,
        )
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"{RED}Error: {e}{RESET}")
        return 1

    if args.json:
        # Convert Decimal objects for json serialization
        serializable = {k: str(v) if isinstance(v, Decimal) else v for k, v in cost.items()}
        print(json.dumps(serializable, indent=2))
        return 0

    print(f"\n{CYAN}{BOLD}Gas Fee Estimate: {cost['preset_name']}{RESET}")
    print(f"  Gas Limit:            {cost['gas_limit']:,} units")
    print(f"  Gas Price:            {cost['total_gas_price_gwei']} Gwei")
    print(f"  Total Cost (Native):  {GREEN}{BOLD}{cost['total_cost_native']} ETH{RESET}")
    print(f"  Total Cost (Wei):     {cost['total_cost_wei']:,} Wei")
    if cost["total_cost_usd"] is not None:
        print(f"  Total Cost (USD):     {GREEN}{BOLD}${cost['total_cost_usd']} USD{RESET} (@ ${cost['token_price_usd']}/ETH)")
    print("")
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Web3 Micro-Utility & Developer Tools Suite (Pure Python Stdlib)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tip", "--sponsor", action="store_true", help="Display multi-chain developer tipping & sponsorship rails")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Command: inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect multi-chain address safety and checksums")
    p_inspect.add_argument("address", help="Cryptocurrency address to inspect")
    p_inspect.add_argument("--chain", help="Explicit chain override (base, bitcoin, solana, stellar)")
    p_inspect.add_argument("--whitelist", help="Comma-separated known addresses to scan for vanity address poisoning")
    p_inspect.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: monitor
    p_monitor = subparsers.add_parser("monitor", help="Benchmark RPC latency, block height, and health")
    p_monitor.add_argument("--chain", help="Specific chain (base, ethereum, solana, bitcoin, stellar)")
    p_monitor.add_argument("--offline", action="store_true", help="Use deterministic offline mock mode (no outbound HTTP)")
    p_monitor.add_argument("--timeout", type=float, default=4.0, help="HTTP request timeout in seconds")
    p_monitor.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: convert
    p_convert = subparsers.add_parser("convert", help="Convert cryptocurrency units with exact decimal precision")
    p_convert.add_argument("amount", help="Amount to convert")
    p_convert.add_argument("from_unit", help="Source unit (wei, gwei, eth, lamports, sol, sats, btc, stroops, xlm)")
    p_convert.add_argument("to_unit", help="Target unit")
    p_convert.add_argument("--chain", help="Explicit chain family (evm, solana, bitcoin, stellar)")
    p_convert.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: gas
    p_gas = subparsers.add_parser("gas", help="Calculate EVM gas cost and USD transaction fee")
    p_gas.add_argument("preset_or_limit", help="Preset (eth_transfer, erc20_transfer, uniswap_swap, contract_deployment) or numeric gas limit")
    p_gas.add_argument("gas_price_gwei", nargs="?", default="20.0", help="Gas price in Gwei (default: 20.0)")
    p_gas.add_argument("--eth-price", type=float, default=2600.0, help="ETH price in USD (default: 2600.0)")
    p_gas.add_argument("--json", action="store_true", help="Output raw JSON")

    # Command: tip / sponsor
    p_tip = subparsers.add_parser("tip", help="Display developer tipping wallets")
    p_tip.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.tip:
        display_tip_info(as_json=args.json)
        return 0

    if not args.command:
        display_tip_info(as_json=args.json)
        parser.print_help()
        return 0

    if args.command == "inspect":
        return handle_inspect(args)
    elif args.command == "monitor":
        return handle_monitor(args)
    elif args.command == "convert":
        return handle_convert(args)
    elif args.command == "gas":
        return handle_gas(args)
    elif args.command == "tip":
        display_tip_info(as_json=args.json)
        return 0

if __name__ == "__main__":
    sys.exit(main())
