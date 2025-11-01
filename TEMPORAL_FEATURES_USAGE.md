# Temporal Feature Extraction - Usage Guide

## Overview

This module extracts temporal features from NFT smart contracts and their creators, including:

### 1. Creator Transaction Activity
- Transfer patterns (transfer, transferFrom, etc.)
- Approval patterns (approve, setApprovalForAll)
- Transaction frequency and timing
- Value movements (ETH sent/received)
- Activity before and after contract creation

### 2. Smart Contract Transaction Activity
- Mint operations (token creation)
- Burn operations (token destruction)
- Withdraw operations (fund extraction)
- Transfer operations (token movements)
- NFT transfer events
- Temporal patterns and activity bursts

---

## Prerequisites

### 1. Etherscan API Key

You need a free Etherscan API key. Get one at: https://etherscan.io/apis

Set it as an environment variable:

**Windows (PowerShell):**
```powershell
$env:ETHERSCAN_API_KEY = "YourApiKeyHere"
```

**Linux/Mac:**
```bash
export ETHERSCAN_API_KEY="YourApiKeyHere"
```

Or edit the script directly and replace `'YourApiKeyToken'` with your actual API key.

### 2. Python Dependencies

```powershell
pip install requests
```

---

## Usage

### Step 1: Extract Temporal Features

Run the extraction script:

```powershell
python extract_temporal_features.py
```

**What it does:**
- Reads contract addresses from `contracts.txt`
- For each contract:
  - Identifies the contract creator
  - Fetches creator's transaction history
  - Fetches contract's transaction history
  - Extracts NFT transfer events
  - Analyzes temporal patterns
- Saves results to `temporal_features.json`

**Expected output:**
```
================================================================================
TEMPORAL FEATURE EXTRACTION FOR NFT CONTRACTS
================================================================================

Loaded 85 contract addresses

[1/85] Processing 0xA82F3a61F002F83Eba7D184c50bB2a8B359cA1cE...
  ✓ Creator: 0x1234...
  ✓ Created: 2021-05-15 14:23:45
  Extracting creator features for 0x1234...
  Extracting contract features for 0xA82F...
  ✓ Features extracted successfully
...
```

**Time estimate:** ~30-60 seconds per contract (with API rate limiting)

---

### Step 2: Analyze and Summarize Features

Generate summary reports:

```powershell
python analyze_temporal_features.py
```

**What it does:**
- Loads `temporal_features.json`
- Calculates summary statistics
- Generates detailed markdown report
- Saves outputs:
  - `temporal_features_summary.json` - Statistical summary
  - `TEMPORAL_FEATURES_REPORT.md` - Human-readable report

**Expected output:**
```
Loading temporal features...
Generating summary statistics...
Generating detailed report...
✓ Summary saved to: temporal_features_summary.json
✓ Detailed report saved to: TEMPORAL_FEATURES_REPORT.md

================================================================================
TEMPORAL FEATURE ANALYSIS SUMMARY
================================================================================

Total Contracts: 85
Successful: 78
Failed: 7
Success Rate: 91.8%

Total Creator Transactions: 45,234
Total Contract Transactions: 123,456

Total Mint Operations: 15,678
Total Burn Operations: 234
Total Transfer Operations: 89,012
```

---

## Output Files

### 1. `temporal_features.json`

Complete temporal feature data for all contracts:

```json
{
  "analysis_date": "2025-11-01 10:30:45",
  "total_contracts": 85,
  "contracts": {
    "0xA82F3a61F002F83Eba7D184c50bB2a8B359cA1cE": {
      "creator": {
        "creator_address": "0x1234...",
        "total_transactions": 1250,
        "post_creation_transactions": 450,
        "transaction_activity": {
          "sent_count": 600,
          "received_count": 650,
          "total_value_sent_wei": 150000000000000000000,
          "total_value_received_wei": 125000000000000000000
        },
        "transfer_patterns": {
          "transfer": 120,
          "approve": 45,
          "mint": 10
        },
        "temporal_patterns": {
          "first_transaction": 1621234567,
          "last_transaction": 1730123456,
          "time_span_days": 1234.5,
          "avg_daily_transactions": 1.01,
          "hourly_distribution": {...}
        }
      },
      "contract": {
        "contract_address": "0xA82F...",
        "creation_timestamp": 1621234567,
        "creation_date": "2021-05-15 14:23:45",
        "total_normal_transactions": 3456,
        "total_internal_transactions": 234,
        "total_nft_transfers": 5678,
        "transaction_activity": {
          "mint_transactions": 150,
          "burn_transactions": 5,
          "withdraw_transactions": 10,
          "transfer_transactions": 2000,
          "approve_transactions": 500
        },
        "nft_activity": {
          "total_transfers": 5678,
          "unique_tokens_transferred": 1234,
          "unique_senders": 456,
          "unique_receivers": 789,
          "mint_events": 150,
          "burn_events": 5,
          "secondary_transfers": 5523
        },
        "temporal_patterns": {
          "contract_age_days": 1234.5,
          "total_activity_days": 456,
          "avg_daily_transactions": 7.58,
          "hourly_distribution": {...},
          "burst_activity_days": 12,
          "activity_ratio": 0.3695
        }
      }
    }
  }
}
```

### 2. `temporal_features_summary.json`

Statistical summary:

```json
{
  "overview": {
    "total_contracts_analyzed": 85,
    "successful_analyses": 78,
    "failed_analyses": 7,
    "success_rate": "91.8%"
  },
  "creator_statistics": {
    "transaction_counts": {
      "min": 10,
      "max": 5000,
      "mean": 580.23,
      "median": 234.5
    },
    "total_transactions": 45234
  },
  "contract_statistics": {...},
  "activity_statistics": {...}
}
```

### 3. `TEMPORAL_FEATURES_REPORT.md`

Human-readable markdown report with:
- Executive summary
- Creator activity analysis
- Smart contract activity analysis
- NFT activity patterns
- Contract rankings
- Top creators by activity
- Top contracts by activity

---

## Features Extracted

### Creator Features

| Feature | Description |
|---------|-------------|
| `total_transactions` | Total number of transactions by creator |
| `post_creation_transactions` | Transactions after creating the contract |
| `sent_count` | Number of outgoing transactions |
| `received_count` | Number of incoming transactions |
| `total_value_sent_wei` | Total ETH sent (in Wei) |
| `total_value_received_wei` | Total ETH received (in Wei) |
| `transfer_patterns` | Count by method (transfer, approve, mint, etc.) |
| `first_transaction` | Timestamp of first transaction |
| `last_transaction` | Timestamp of last transaction |
| `time_span_days` | Days between first and last transaction |
| `avg_daily_transactions` | Average transactions per day |
| `hourly_distribution` | Transaction count by hour of day |

### Contract Features

| Feature | Description |
|---------|-------------|
| `creation_timestamp` | Unix timestamp of contract creation |
| `creation_date` | Human-readable creation date |
| `total_normal_transactions` | External transactions to contract |
| `total_internal_transactions` | Internal contract calls |
| `total_nft_transfers` | Total NFT transfer events |
| `mint_transactions` | Number of mint operations |
| `burn_transactions` | Number of burn operations |
| `withdraw_transactions` | Number of withdraw operations |
| `transfer_transactions` | Number of transfer calls |
| `unique_tokens_transferred` | Unique token IDs transferred |
| `unique_senders` | Unique addresses sending NFTs |
| `unique_receivers` | Unique addresses receiving NFTs |
| `mint_events` | Mints (transfers from 0x0) |
| `burn_events` | Burns (transfers to 0x0) |
| `secondary_transfers` | Non-mint, non-burn transfers |
| `contract_age_days` | Days since contract creation |
| `total_activity_days` | Days with at least one transaction |
| `avg_daily_transactions` | Average transactions per day |
| `burst_activity_days` | Days with unusual high activity |
| `activity_ratio` | Ratio of active days to total age |

---

## Rate Limiting

The script respects Etherscan's rate limits:
- **Free tier:** 5 requests/second, 100,000 requests/day
- **Delay:** 0.2 seconds between requests

For 85 contracts, expect:
- ~4-6 API calls per contract
- ~340-510 total API calls
- ~68-102 seconds minimum (rate limited)
- **Total time:** ~5-10 minutes

---

## Troubleshooting

### Error: "Creator information not available"

Some contracts may not have creator information available via Etherscan API. This is normal for:
- Very old contracts
- Contracts created by other contracts
- Unverified contracts

### Error: "Rate limit exceeded"

If you see too many errors:
1. Increase `RATE_LIMIT_DELAY` in the script
2. Run script during off-peak hours
3. Consider using a paid Etherscan API key

### Error: "No transactions found"

Some contracts may have:
- Zero activity
- Activity too old (Etherscan historical limits)
- Activity not indexed by Etherscan

---

## Next Steps

After extracting temporal features, you can:

1. **Correlate with vulnerabilities** - Compare temporal patterns with vulnerability data
2. **Identify suspicious patterns** - Find contracts with unusual activity
3. **Cluster analysis** - Group contracts by temporal behavior
4. **Machine learning** - Use features for classification/prediction
5. **Time series analysis** - Analyze activity trends over time

---

## Example Analysis Questions

With temporal features, you can answer:

- Which creators are most active before/after contract deployment?
- What's the typical lifespan of NFT contracts?
- Are there burst periods of minting activity?
- Do high-vulnerability contracts have different temporal patterns?
- Which contracts are abandoned (no recent activity)?
- What are common transaction patterns for successful NFT projects?

---

## Files in This Module

| File | Purpose |
|------|---------|
| `extract_temporal_features.py` | Main extraction script |
| `analyze_temporal_features.py` | Analysis and reporting |
| `TEMPORAL_FEATURES_USAGE.md` | This documentation |
| `temporal_features.json` | Raw extracted data (generated) |
| `temporal_features_summary.json` | Statistical summary (generated) |
| `TEMPORAL_FEATURES_REPORT.md` | Detailed report (generated) |

---

**Created:** November 1, 2025  
**Version:** 1.0  
**Author:** NFT Analysis Pipeline
