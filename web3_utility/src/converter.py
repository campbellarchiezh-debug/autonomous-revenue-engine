"""
Cryptocurrency Unit Converter & Gas Fee Calculator Engine.

Pure Python 3.9 standard library implementation with zero external dependencies.
Features:
- High-precision conversion across EVM (Wei/Gwei/Eth), Solana (Lamports/Sol),
  Bitcoin (Sats/BTC), and Stellar (Stroops/XLM) using Python's `decimal.Decimal`.
- Comprehensive Gas Fee calculation with standard EVM transaction presets
  (ETH transfer, ERC-20 transfer, Uniswap swap, contract deployment) and USD valuation.
"""

from decimal import Decimal, InvalidOperation, getcontext
from typing import Any, Dict, Optional, Union

# Set global decimal precision to 36 digits to handle Wei up to trillions of ETH
getcontext().prec = 36

# Unit scale mappings (relative to the chain's smallest atomic unit: Wei, Lamport, Sat, Stroop)
UNIT_SCALES: Dict[str, Dict[str, Decimal]] = {
    "evm": {
        "wei": Decimal("1"),
        "kwei": Decimal("1e3"),
        "babbage": Decimal("1e3"),
        "mwei": Decimal("1e6"),
        "lovelace": Decimal("1e6"),
        "gwei": Decimal("1e9"),
        "shannon": Decimal("1e9"),
        "szabo": Decimal("1e12"),
        "microether": Decimal("1e12"),
        "finney": Decimal("1e15"),
        "milliether": Decimal("1e15"),
        "eth": Decimal("1e18"),
        "ether": Decimal("1e18"),
    },
    "solana": {
        "lamport": Decimal("1"),
        "lamports": Decimal("1"),
        "sol": Decimal("1e9"),
    },
    "bitcoin": {
        "sat": Decimal("1"),
        "sats": Decimal("1"),
        "satoshi": Decimal("1"),
        "satoshis": Decimal("1"),
        "bit": Decimal("1e2"),
        "bits": Decimal("1e2"),
        "mbtc": Decimal("1e5"),
        "millibtc": Decimal("1e5"),
        "btc": Decimal("1e8"),
        "bitcoin": Decimal("1e8"),
    },
    "stellar": {
        "stroop": Decimal("1"),
        "stroops": Decimal("1"),
        "xlm": Decimal("1e7"),
        "lumen": Decimal("1e7"),
        "lumens": Decimal("1e7"),
    },
}

# Transaction gas presets for EVM networks
GAS_PRESETS: Dict[str, Dict[str, Any]] = {
    "eth_transfer": {
        "name": "Native ETH / Base Transfer",
        "gas_limit": 21000,
        "description": "Standard standard native token transfer between EOAs",
    },
    "erc20_transfer": {
        "name": "ERC-20 Token Transfer",
        "gas_limit": 65000,
        "description": "Standard ERC-20 transfer method invocation",
    },
    "uniswap_swap": {
        "name": "DEX Swap (Uniswap / Aerodrome)",
        "gas_limit": 150000,
        "description": "Automated Market Maker router swap across liquidity pools",
    },
    "nft_mint": {
        "name": "ERC-721 / ERC-1155 NFT Mint",
        "gas_limit": 120000,
        "description": "Standard NFT minting smart contract transaction",
    },
    "contract_deployment": {
        "name": "Smart Contract Deployment",
        "gas_limit": 1500000,
        "description": "Deploying bytecode to on-chain state",
    },
}


def _find_chain_for_unit(unit_str: str) -> Optional[str]:
    """Identify which blockchain family owns a given unit name."""
    u = unit_str.lower().strip()
    for chain, units in UNIT_SCALES.items():
        if u in units:
            return chain
    return None


def convert_units(
    amount: Union[str, int, float, Decimal],
    from_unit: str,
    to_unit: str,
    chain: Optional[str] = None,
) -> Decimal:
    """
    Convert cryptocurrency units with exact decimal precision.

    Examples:
        convert_units(1, "eth", "wei") -> Decimal('1000000000000000000')
        convert_units(1000000000, "lamports", "sol") -> Decimal('1.000000000')
        convert_units(100000000, "sats", "btc") -> Decimal('1.00000000')
    """
    try:
        dec_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Invalid numeric amount '{amount}': {e}")

    if dec_amount < 0:
        raise ValueError(f"Amount cannot be negative: '{amount}'")

    u_from = from_unit.lower().strip()
    u_to = to_unit.lower().strip()

    # Determine target chain
    target_chain = chain.lower().strip() if chain else None
    if not target_chain:
        chain_from = _find_chain_for_unit(u_from)
        chain_to = _find_chain_for_unit(u_to)
        if not chain_from:
            raise ValueError(f"Unrecognized source unit: '{from_unit}'")
        if not chain_to:
            raise ValueError(f"Unrecognized target unit: '{to_unit}'")
        if chain_from != chain_to:
            raise ValueError(
                f"Cannot cross-convert incompatible chains: '{from_unit}' ({chain_from}) to '{to_unit}' ({chain_to})"
            )
        target_chain = chain_from

    if target_chain not in UNIT_SCALES:
        raise ValueError(f"Unsupported chain '{target_chain}'. Choose from {list(UNIT_SCALES.keys())}")

    chain_table = UNIT_SCALES[target_chain]
    if u_from not in chain_table:
        raise ValueError(f"Unit '{from_unit}' not found in chain '{target_chain}'. Available: {list(chain_table.keys())}")
    if u_to not in chain_table:
        raise ValueError(f"Unit '{to_unit}' not found in chain '{target_chain}'. Available: {list(chain_table.keys())}")

    scale_from = chain_table[u_from]
    scale_to = chain_table[u_to]

    # Convert: (amount * scale_from) / scale_to
    atomic_value = dec_amount * scale_from
    result = atomic_value / scale_to
    return result.normalize()


def calculate_gas_cost(
    gas_limit: Optional[int] = None,
    gas_price_gwei: Union[str, float, Decimal] = 20.0,
    token_price_usd: Optional[Union[str, float, Decimal]] = None,
    preset: Optional[str] = None,
    priority_fee_gwei: Optional[Union[str, float, Decimal]] = None,
) -> Dict[str, Any]:
    """
    Calculate EVM transaction gas fees, native token cost, and USD value.

    Parameters:
        gas_limit: Integer gas units (e.g. 21000). If None, preset is required.
        gas_price_gwei: Base gas price in Gwei (e.g. 20.0 or 0.05 on Base).
        token_price_usd: Native token price in USD (e.g. 2600.0).
        preset: Standard preset key ('eth_transfer', 'erc20_transfer', 'uniswap_swap', etc.).
        priority_fee_gwei: Optional EIP-1559 tip / miner fee in Gwei.
    """
    preset_info = None
    if preset:
        p_key = preset.lower().strip()
        if p_key in GAS_PRESETS:
            preset_info = GAS_PRESETS[p_key]
            if gas_limit is None:
                gas_limit = preset_info["gas_limit"]
        else:
            raise ValueError(f"Unknown preset '{preset}'. Available: {list(GAS_PRESETS.keys())}")

    if gas_limit is None or gas_limit <= 0:
        raise ValueError(f"Invalid gas limit: {gas_limit}")

    dec_price_gwei = Decimal(str(gas_price_gwei))
    dec_priority_gwei = Decimal(str(priority_fee_gwei)) if priority_fee_gwei is not None else Decimal("0")

    total_effective_gwei = dec_price_gwei + dec_priority_gwei
    total_cost_gwei = Decimal(gas_limit) * total_effective_gwei
    total_cost_wei = total_cost_gwei * Decimal("1e9")
    total_cost_eth = total_cost_wei / Decimal("1e18")

    cost_usd = None
    if token_price_usd is not None:
        dec_usd_rate = Decimal(str(token_price_usd))
        cost_usd = (total_cost_eth * dec_usd_rate).quantize(Decimal("0.0001"))

    return {
        "preset": preset,
        "preset_name": preset_info["name"] if preset_info else "Custom",
        "gas_limit": gas_limit,
        "base_gas_price_gwei": dec_price_gwei.normalize(),
        "priority_fee_gwei": dec_priority_gwei.normalize(),
        "total_gas_price_gwei": total_effective_gwei.normalize(),
        "total_cost_wei": int(total_cost_wei),
        "total_cost_gwei": total_cost_gwei.normalize(),
        "total_cost_native": total_cost_eth.normalize(),
        "token_price_usd": Decimal(str(token_price_usd)).normalize() if token_price_usd else None,
        "total_cost_usd": cost_usd,
    }


def format_decimal(d: Decimal) -> str:
    """Format a Decimal number without scientific notation, removing trailing zeros."""
    s = f"{d:f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def get_supported_units() -> Dict[str, Dict[str, str]]:
    """Return dictionary of supported chains and units with decimal scales."""
    result = {}
    for chain, units in UNIT_SCALES.items():
        result[chain] = {u: str(scale) for u, scale in units.items()}
    return result
