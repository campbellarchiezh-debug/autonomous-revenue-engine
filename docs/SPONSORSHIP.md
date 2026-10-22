# Sponsorship & Multi-Chain Payment Rails Guide

The **Autonomous Revenue Engine** is an open-source, non-custodial software suite designed to deliver real utility and autonomous value without intermediation or tracking.

By directly funding these non-custodial multi-chain payment rails, you support continuous maintenance, RPC node infrastructure, open-source template expansion, and financial modeling research.

---

## 💎 Canonical Beneficiary Wallets

Every contribution is routed directly to the author's verified on-chain addresses. There are zero intermediaries, custodial smart contracts, or management fees.

| Network | Canonical Address | Checksum / Format | Supported Assets | Block Explorer Link |
| :--- | :--- | :--- | :--- | :--- |
| **Base EVM** | `0xef5766253e2d92e530e301ac22dcb8de78e89c55` | `0xeF5766253e2D92E530e301aC22dcB8DE78E89C55` (EIP-55) | ETH, USDC, DAI, any ERC-20 on Base (ChainID 8453) | [View on BaseScan](https://basescan.org/address/0xef5766253e2d92e530e301ac22dcb8de78e89c55) |
| **Solana** | `3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp` | 32-byte Ed25519 Base58 | SOL, USDC (SPL), any SPL Token | [View on Solscan](https://solscan.io/account/3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp) |
| **Bitcoin** | `bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e` | BIP-341/350 Taproot (Bech32m) | BTC (Native SegWit / Taproot) | [View on Mempool.space](https://mempool.space/address/bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e) |
| **Stellar** | `GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA` | StrKey Base32 + CRC16-XMODEM | XLM, Soroban smart contracts | [View on Stellar.expert](https://stellar.expert/explorer/public/account/GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA) |

---

## 🛡️ Address Verification & Anti-Poisoning Attestation

To safeguard against address poisoning and clipboard injection attacks, verify the cryptographic integrity of these addresses before sending funds:

```bash
# Verify using the project's built-in Address Inspector
python3 web3_utility/run_cli.py inspect 0xef5766253e2d92e530e301ac22dcb8de78e89c55
python3 web3_utility/run_cli.py inspect 3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp

# Or verify in terminal using Python standard library
python3 -c "
import urllib.request, json
from templates.rpc_client_template import BENEFICIARY_WALLETS
print('Beneficiary Wallets Verified:')
for k, v in BENEFICIARY_WALLETS.items():
    print(f'  {k.upper()}: {v}')
"
```

---

## 🏆 Sponsorship Tiers & Recognition

If you are an enterprise, validator operator, or institutional developer deploying these tools, consider joining one of our sponsorship tiers:

### 🥉 Tier 1: Micro-Tip / Builder Fuel ($5 – $50 equiv.)
- Helps fund public RPC endpoints and CI compute runners.
- Direct shout-out in community release notes.

### 🥈 Tier 2: Pro Developer Sponsor ($100 – $500 equiv.)
- Prioritized issue triaging and template feature requests.
- Inclusion of your organization or personal handle in `CONTRIBUTORS.md`.

### 🥇 Tier 3: Enterprise Infrastructure Patron ($1,000 – $2,500 equiv.)
- Customized B2B conversion leak audit models for your specialized vertical.
- Bespoke RPC failover routing policies and tailored staking APY calculation presets.
- Prominent logo placement on the Web3 SaaS Calculator dashboard.

### 👑 Tier 4: Genesis Validator Partner ($5,000+ equiv.)
- Permanent founding patron attribution in the repository `README.md` and distribution kit.
- Direct advisory on custom node monitoring pipelines and autonomous payment flows.

---

## 🔍 On-Chain Balance Auditing Script

You can verify balance updates programmatically using the included `verify_balances.py` script:

```bash
# Query live RPCs for incoming transaction receipts across all 4 chains
python3 verify_balances.py --chain all --json

# Run offline simulated verification
python3 verify_balances.py --simulate
```
