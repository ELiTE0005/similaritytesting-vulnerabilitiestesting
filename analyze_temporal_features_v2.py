"""
Temporal Feature Analysis Script (v2)
Analyzes temporal features extracted from NFT contracts
"""

import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

def load_temporal_features(filename: str = 'temporal_features.json') -> dict:
    """Load temporal features from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def analyze_contract_activity(data: dict) -> dict:
    """Analyze overall contract activity patterns"""
    contracts = data['contracts']
    
    stats = {
        'total_contracts': len(contracts),
        'contracts_with_activity': 0,
        'contracts_with_nft_transfers': 0,
        'total_transactions': 0,
        'total_nft_transfers': 0,
        'total_mint_events': 0,
        'total_burn_events': 0,
        'total_secondary_transfers': 0,
    }
    
    for contract_addr, features in contracts.items():
        if 'error' in features:
            continue
            
        data_collection = features.get('data_collection', {})
        nft_activity = features.get('nft_activity', {})
        
        normal_txs = data_collection.get('normal_transactions', 0)
        nft_transfers = data_collection.get('nft_transfers', 0)
        
        if normal_txs > 0 or nft_transfers > 0:
            stats['contracts_with_activity'] += 1
        
        if nft_transfers > 0:
            stats['contracts_with_nft_transfers'] += 1
            
        stats['total_transactions'] += normal_txs
        stats['total_nft_transfers'] += nft_transfers
        stats['total_mint_events'] += nft_activity.get('mint_events', 0)
        stats['total_burn_events'] += nft_activity.get('burn_events', 0)
        stats['total_secondary_transfers'] += nft_activity.get('secondary_transfers', 0)
    
    return stats

def rank_contracts_by_activity(data: dict) -> List[tuple]:
    """Rank contracts by transaction activity"""
    contracts = data['contracts']
    rankings = []
    
    for contract_addr, features in contracts.items():
        if 'error' in features:
            continue
            
        data_collection = features.get('data_collection', {})
        nft_activity = features.get('nft_activity', {})
        
        total_activity = (
            data_collection.get('normal_transactions', 0) +
            data_collection.get('internal_transactions', 0) +
            data_collection.get('nft_transfers', 0)
        )
        
        rankings.append({
            'address': contract_addr,
            'total_activity': total_activity,
            'normal_txs': data_collection.get('normal_transactions', 0),
            'internal_txs': data_collection.get('internal_transactions', 0),
            'nft_transfers': data_collection.get('nft_transfers', 0),
            'mint_events': nft_activity.get('mint_events', 0),
            'burn_events': nft_activity.get('burn_events', 0),
        })
    
    # Sort by total activity
    rankings.sort(key=lambda x: x['total_activity'], reverse=True)
    
    return rankings

def analyze_temporal_patterns(data: dict) -> dict:
    """Analyze temporal patterns across contracts"""
    contracts = data['contracts']
    
    patterns = {
        'age_distribution': defaultdict(int),
        'activity_ratio_distribution': defaultdict(int),
        'contracts_by_age': [],
        'hourly_activity_total': defaultdict(int),
    }
    
    for contract_addr, features in contracts.items():
        if 'error' in features:
            continue
            
        temporal = features.get('temporal_patterns', {})
        
        age_days = temporal.get('contract_age_days', 0)
        activity_ratio = temporal.get('activity_ratio', 0)
        hourly_dist = temporal.get('hourly_distribution', {})
        
        # Age distribution (buckets)
        if age_days == 0:
            patterns['age_distribution']['unknown'] += 1
        elif age_days < 30:
            patterns['age_distribution']['< 30 days'] += 1
        elif age_days < 90:
            patterns['age_distribution']['30-90 days'] += 1
        elif age_days < 180:
            patterns['age_distribution']['90-180 days'] += 1
        elif age_days < 365:
            patterns['age_distribution']['180-365 days'] += 1
        else:
            patterns['age_distribution']['> 365 days'] += 1
        
        # Activity ratio distribution
        if activity_ratio == 0:
            patterns['activity_ratio_distribution']['inactive'] += 1
        elif activity_ratio < 0.1:
            patterns['activity_ratio_distribution']['low (< 10%)'] += 1
        elif activity_ratio < 0.3:
            patterns['activity_ratio_distribution']['medium (10-30%)'] += 1
        else:
            patterns['activity_ratio_distribution']['high (> 30%)'] += 1
        
        # Collect for sorting
        patterns['contracts_by_age'].append({
            'address': contract_addr,
            'age_days': age_days,
            'creation_date': temporal.get('creation_date', 'Unknown'),
            'first_activity_date': temporal.get('first_activity_date', 'Unknown'),
        })
        
        # Aggregate hourly activity
        for hour, count in hourly_dist.items():
            patterns['hourly_activity_total'][int(hour)] += count
    
    # Sort by age
    patterns['contracts_by_age'].sort(key=lambda x: x['age_days'], reverse=True)
    
    return patterns

def analyze_nft_metrics(data: dict) -> dict:
    """Analyze NFT-specific metrics"""
    contracts = data['contracts']
    
    metrics = {
        'total_unique_tokens': 0,
        'total_unique_senders': 0,
        'total_unique_receivers': 0,
        'contracts_with_mints': 0,
        'contracts_with_burns': 0,
        'avg_tokens_per_contract': 0,
    }
    
    total_tokens = 0
    active_contracts = 0
    
    for contract_addr, features in contracts.items():
        if 'error' in features:
            continue
            
        nft_activity = features.get('nft_activity', {})
        
        unique_tokens = nft_activity.get('unique_tokens_transferred', 0)
        mint_events = nft_activity.get('mint_events', 0)
        burn_events = nft_activity.get('burn_events', 0)
        
        if unique_tokens > 0:
            total_tokens += unique_tokens
            active_contracts += 1
        
        metrics['total_unique_tokens'] += unique_tokens
        metrics['total_unique_senders'] += nft_activity.get('unique_senders', 0)
        metrics['total_unique_receivers'] += nft_activity.get('unique_receivers', 0)
        
        if mint_events > 0:
            metrics['contracts_with_mints'] += 1
        if burn_events > 0:
            metrics['contracts_with_burns'] += 1
    
    if active_contracts > 0:
        metrics['avg_tokens_per_contract'] = round(total_tokens / active_contracts, 2)
    
    return metrics

def generate_markdown_report(data: dict, stats: dict, rankings: List[dict], 
                            patterns: dict, nft_metrics: dict) -> str:
    """Generate comprehensive markdown report"""
    
    report = f"""# Temporal Features Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analysis Date:** {data.get('analysis_date', 'N/A')}

---

## Executive Summary

### Dataset Overview
- **Total Contracts Analyzed:** {stats['total_contracts']}
- **Contracts with Activity:** {stats['contracts_with_activity']} ({stats['contracts_with_activity']/stats['total_contracts']*100:.1f}%)
- **Contracts with NFT Transfers:** {stats['contracts_with_nft_transfers']} ({stats['contracts_with_nft_transfers']/stats['total_contracts']*100:.1f}%)

### Transaction Activity
- **Total Transactions:** {stats['total_transactions']:,}
- **Total NFT Transfers:** {stats['total_nft_transfers']:,}
- **Total Mint Events:** {stats['total_mint_events']:,}
- **Total Burn Events:** {stats['total_burn_events']:,}
- **Total Secondary Transfers:** {stats['total_secondary_transfers']:,}

### NFT Metrics
- **Total Unique Tokens:** {nft_metrics['total_unique_tokens']:,}
- **Average Tokens per Active Contract:** {nft_metrics['avg_tokens_per_contract']}
- **Contracts with Mint Events:** {nft_metrics['contracts_with_mints']}
- **Contracts with Burn Events:** {nft_metrics['contracts_with_burns']}

---

## Contract Activity Rankings

### Top 20 Most Active Contracts

| Rank | Contract Address | Total Activity | Normal TXs | Internal TXs | NFT Transfers | Mints | Burns |
|------|------------------|----------------|------------|--------------|---------------|-------|-------|
"""
    
    # Add top 20 contracts
    for idx, contract in enumerate(rankings[:20], 1):
        addr_short = f"{contract['address'][:6]}...{contract['address'][-4:]}"
        report += f"| {idx} | `{addr_short}` | {contract['total_activity']:,} | {contract['normal_txs']:,} | {contract['internal_txs']:,} | {contract['nft_transfers']:,} | {contract['mint_events']:,} | {contract['burn_events']:,} |\n"
    
    report += f"""
---

## Temporal Patterns

### Contract Age Distribution

| Age Range | Count | Percentage |
|-----------|-------|------------|
"""
    
    total_contracts = sum(patterns['age_distribution'].values())
    for age_range, count in sorted(patterns['age_distribution'].items()):
        pct = (count / total_contracts * 100) if total_contracts > 0 else 0
        report += f"| {age_range} | {count} | {pct:.1f}% |\n"
    
    report += f"""
### Activity Ratio Distribution

| Activity Level | Count | Percentage |
|----------------|-------|------------|
"""
    
    total_contracts_ratio = sum(patterns['activity_ratio_distribution'].values())
    for level, count in sorted(patterns['activity_ratio_distribution'].items()):
        pct = (count / total_contracts_ratio * 100) if total_contracts_ratio > 0 else 0
        report += f"| {level} | {count} | {pct:.1f}% |\n"
    
    report += f"""
### Hourly Activity Distribution

The following shows the total activity across all contracts by hour of day (UTC):

| Hour | Activity Count |
|------|----------------|
"""
    
    for hour in range(24):
        count = patterns['hourly_activity_total'].get(hour, 0)
        if count > 0:
            report += f"| {hour:02d}:00 | {count:,} |\n"
    
    report += f"""
---

## Oldest Contracts

| Rank | Contract Address | Age (Days) | Creation Date | First Activity |
|------|------------------|------------|---------------|----------------|
"""
    
    for idx, contract in enumerate(patterns['contracts_by_age'][:10], 1):
        addr_short = f"{contract['address'][:6]}...{contract['address'][-4:]}"
        report += f"| {idx} | `{addr_short}` | {contract['age_days']:.0f} | {contract['creation_date']} | {contract['first_activity_date']} |\n"
    
    report += f"""
---

## Methodology

### Data Collection
- **Source:** Etherscan API
- **Endpoints Used:**
  - Normal Transactions (`txlist`)
  - Internal Transactions (`txlistinternal`)
  - ERC721 Transfers (`tokennfttx`)

### Features Extracted
1. **Transaction Activity:** Normal, internal, and total transaction counts
2. **NFT Activity:** Mints, burns, transfers, unique tokens/senders/receivers
3. **Temporal Patterns:** Contract age, activity ratios, hourly distributions
4. **ETH Movements:** Inbound/outbound ETH flows

### Limitations
- Creator information not available (Etherscan API v1 deprecated)
- Analysis focuses on on-chain contract activity
- Rate-limited to ~5 requests/second

---

**Report End**
"""
    
    return report

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("TEMPORAL FEATURES ANALYSIS")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading temporal features...")
    data = load_temporal_features()
    print(f"✓ Loaded data for {data.get('total_contracts', 0)} contracts\n")
    
    # Analyze contract activity
    print("Analyzing contract activity...")
    stats = analyze_contract_activity(data)
    print(f"✓ {stats['contracts_with_activity']} contracts with activity found\n")
    
    # Rank contracts
    print("Ranking contracts by activity...")
    rankings = rank_contracts_by_activity(data)
    print(f"✓ {len(rankings)} contracts ranked\n")
    
    # Analyze temporal patterns
    print("Analyzing temporal patterns...")
    patterns = analyze_temporal_patterns(data)
    print(f"✓ Temporal patterns analyzed\n")
    
    # Analyze NFT metrics
    print("Analyzing NFT metrics...")
    nft_metrics = analyze_nft_metrics(data)
    print(f"✓ NFT metrics calculated\n")
    
    # Generate report
    print("Generating markdown report...")
    report = generate_markdown_report(data, stats, rankings, patterns, nft_metrics)
    
    # Save report
    report_file = 'TEMPORAL_FEATURES_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ Report saved to: {report_file}\n")
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal Contracts: {stats['total_contracts']}")
    print(f"Active Contracts: {stats['contracts_with_activity']}")
    print(f"Total Transactions: {stats['total_transactions']:,}")
    print(f"Total NFT Transfers: {stats['total_nft_transfers']:,}")
    print(f"Total Mint Events: {stats['total_mint_events']:,}")
    print(f"\nTop 5 Most Active Contracts:")
    for idx, contract in enumerate(rankings[:5], 1):
        addr_short = f"{contract['address'][:6]}...{contract['address'][-4:]}"
        print(f"  {idx}. {addr_short}: {contract['total_activity']:,} total activity")
    print()

if __name__ == '__main__':
    main()
