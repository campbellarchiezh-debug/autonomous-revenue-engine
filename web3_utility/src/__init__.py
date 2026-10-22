"""
Web3 Micro-Utility & Developer Tools Suite.
Zero-dependency, pure Python 3.9 stdlib multi-chain inspection, RPC benchmarking,
and cryptocurrency unit conversion.
"""

__version__ = "1.0.0"
__author__ = "Autonomous Revenue Engine"

from web3_utility.src.inspector import (
    keccak256,
    to_checksum_address,
    inspect_address,
    detect_zero_width_chars,
    detect_homoglyphs,
    check_poisoning_heuristic,
)
from web3_utility.src.rpc_monitor import (
    RPCMonitor,
    benchmark_chain,
    benchmark_all,
)
from web3_utility.src.converter import (
    convert_units,
    calculate_gas_cost,
    format_decimal,
)

__all__ = [
    "keccak256",
    "to_checksum_address",
    "inspect_address",
    "detect_zero_width_chars",
    "detect_homoglyphs",
    "check_poisoning_heuristic",
    "RPCMonitor",
    "benchmark_chain",
    "benchmark_all",
    "convert_units",
    "calculate_gas_cost",
    "format_decimal",
]
