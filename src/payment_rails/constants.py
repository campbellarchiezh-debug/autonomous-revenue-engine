"""
Multi-Chain Payment Rails Constants & Configuration.

Contains canonical beneficiary wallet addresses, public RPC and REST endpoint pools
with multi-tier failover, asset metadata, and deterministic mock ledger fixtures.
"""

# Canonical beneficiary wallet addresses for revenue deposition
BENEFICIARY_WALLETS = {
    "base": "0xef5766253e2d92e530e301ac22dcb8de78e89c55",
    "solana": "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp",
    "bitcoin": "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e",
    "stellar": "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA",
}

# Public RPC & REST endpoint hierarchy with multi-tier failover
PUBLIC_RPC_ENDPOINTS = {
    "base": [
        "https://mainnet.base.org",
        "https://base.llamarpc.com",
        "https://1rpc.io/base",
    ],
    "solana": [
        "https://api.mainnet-beta.solana.com",
        "https://solana-mainnet.rpc.extrnode.com",
        "https://solana.publicnode.com",
    ],
    "bitcoin": [
        "https://mempool.space/api",
        "https://blockstream.info/api",
        "https://blockchain.info/q/addressbalance",
    ],
    "stellar": [
        "https://horizon.stellar.org",
        "https://horizon-pubnet.stellar.org",
    ],
}

# Asset metadata
ASSET_INFO = {
    "base": {"symbol": "ETH", "name": "Ethereum on Base", "decimals": 18},
    "solana": {"symbol": "SOL", "name": "Solana Native", "decimals": 9},
    "bitcoin": {"symbol": "BTC", "name": "Bitcoin (Taproot)", "decimals": 8},
    "stellar": {"symbol": "XLM", "name": "Stellar Lumens", "decimals": 7},
}

# Deterministic mock balances for sandboxed execution, simulation, and offline CI testing
MOCK_BALANCES = {
    "base": {
        "raw": "0x1bc16d674ec80000",
        "balance": 2.0,
        "formatted": "2.00000000 ETH",
        "status": "simulated",
    },
    "solana": {
        "raw": 5000000000,
        "balance": 5.0,
        "formatted": "5.000000000 SOL",
        "status": "simulated",
    },
    "bitcoin": {
        "raw": 25000000,
        "balance": 0.25,
        "formatted": "0.25000000 BTC",
        "status": "simulated",
    },
    "stellar": {
        "raw": "100.0000000",
        "balance": 100.0,
        "formatted": "100.0000000 XLM",
        "status": "simulated",
    },
}
