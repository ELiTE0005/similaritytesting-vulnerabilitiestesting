"""
Analyze and summarize temporal features extracted from NFT contracts
Generates comprehensive reports and visualizations
"""

import json
from datetime import datetime
from collections import defaultdict
import statistics

def load_temporal_features(filename='temporal_features.json'):
    """Load temporal features from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def generate_summary_report(data):
    """Generate summary statistics from temporal features"""
    
    contracts = data.get('contracts', {})
    
    # Initialize counters
    total_contracts = len(contracts)
    successful_contracts = sum(1 for v in contracts.values() if 'error' not in v)
    
    # Collect metrics
    creator_tx_counts = []
    contract_tx_counts = []
    contract_ages = []
    mint_counts = []
    burn_counts = []
    transfer_counts = []
    
    creator_activity = defaultdict(int)
    contract_activity = defaultdict(int)
    
    for contract_addr, features in contracts.items():
        if 'error' in features:
            continue
        
        # Creator features
        creator_data = features.get('creator', {})
        creator_tx_counts.append(creator_data.get('total_transactions', 0))
        
        # Contract features
        contract_data = features.get('contract', {})
        contract_tx_counts.append(contract_data.get('total_normal_transactions', 0))
        
        # Temporal patterns
        temporal = contract_data.get('temporal_patterns', {})
        contract_ages.append(temporal.get('contract_age_days', 0))
        
        # Activity metrics
        activity = contract_data.get('transaction_activity', {})
        mint_counts.append(activity.get('mint_transactions', 0))
        burn_counts.append(activity.get('burn_transactions', 0))
        transfer_counts.append(activity.get('transfer_transactions', 0))
        
        # NFT activity
        nft_activity = contract_data.get('nft_activity', {})
        mint_counts.append(nft_activity.get('mint_events', 0))
        burn_counts.append(nft_activity.get('burn_events', 0))
    
    # Calculate statistics
    def safe_stats(data):
        if not data:
            return {'min': 0, 'max': 0, 'mean': 0, 'median': 0}
        return {
            'min': min(data),
            'max': max(data),
            'mean': round(statistics.mean(data), 2),
            'median': round(statistics.median(data), 2),
        }
    
    summary = {
        'overview': {
            'total_contracts_analyzed': total_contracts,
            'successful_analyses': successful_contracts,
            'failed_analyses': total_contracts - successful_contracts,
            'success_rate': f"{(successful_contracts/total_contracts*100):.1f}%" if total_contracts > 0 else "0%"
        },
        'creator_statistics': {
            'transaction_counts': safe_stats(creator_tx_counts),
            'total_transactions': sum(creator_tx_counts),
        },
        'contract_statistics': {
            'transaction_counts': safe_stats(contract_tx_counts),
            'total_transactions': sum(contract_tx_counts),
            'contract_ages_days': safe_stats(contract_ages),
        },
        'activity_statistics': {
            'mint_operations': {
                'total': sum(mint_counts),
                'stats': safe_stats(mint_counts),
            },
            'burn_operations': {
                'total': sum(burn_counts),
                'stats': safe_stats(burn_counts),
            },
            'transfer_operations': {
                'total': sum(transfer_counts),
                'stats': safe_stats(transfer_counts),
            },
        }
    }
    
    return summary

def generate_detailed_report(data):
    """Generate detailed markdown report"""
    
    summary = generate_summary_report(data)
    
    report = f"""# Temporal Feature Analysis Report

**Analysis Date:** {data.get('analysis_date', 'Unknown')}
**Total Contracts:** {data.get('total_contracts', 0)}

---

## 📊 Executive Summary

### Overview
- **Total Contracts Analyzed:** {summary['overview']['total_contracts_analyzed']}
- **Successful Analyses:** {summary['overview']['successful_analyses']}
- **Failed Analyses:** {summary['overview']['failed_analyses']}
- **Success Rate:** {summary['overview']['success_rate']}

---

## 👤 Creator Activity Analysis

### Transaction Statistics
- **Total Creator Transactions:** {summary['creator_statistics']['total_transactions']:,}
- **Min Transactions per Creator:** {summary['creator_statistics']['transaction_counts']['min']}
- **Max Transactions per Creator:** {summary['creator_statistics']['transaction_counts']['max']}
- **Mean Transactions per Creator:** {summary['creator_statistics']['transaction_counts']['mean']}
- **Median Transactions per Creator:** {summary['creator_statistics']['transaction_counts']['median']}

### Key Insights
"""
    
    # Add top creators by activity
    contracts = data.get('contracts', {})
    creator_activities = []
    
    for contract_addr, features in contracts.items():
        if 'error' not in features:
            creator_data = features.get('creator', {})
            creator_addr = creator_data.get('creator_address', 'Unknown')
            total_txs = creator_data.get('total_transactions', 0)
            creator_activities.append((contract_addr, creator_addr, total_txs))
    
    creator_activities.sort(key=lambda x: x[2], reverse=True)
    
    report += "\n#### Top 10 Most Active Creators\n\n"
    report += "| Rank | Contract | Creator | Total Transactions |\n"
    report += "|------|----------|---------|-------------------|\n"
    
    for idx, (contract, creator, txs) in enumerate(creator_activities[:10], 1):
        report += f"| {idx} | `{contract[:10]}...` | `{creator[:10]}...` | {txs:,} |\n"
    
    report += f"""

---

## 📜 Smart Contract Activity Analysis

### Transaction Statistics
- **Total Contract Transactions:** {summary['contract_statistics']['total_transactions']:,}
- **Min Transactions per Contract:** {summary['contract_statistics']['transaction_counts']['min']}
- **Max Transactions per Contract:** {summary['contract_statistics']['transaction_counts']['max']}
- **Mean Transactions per Contract:** {summary['contract_statistics']['transaction_counts']['mean']}
- **Median Transactions per Contract:** {summary['contract_statistics']['transaction_counts']['median']}

### Contract Age Statistics
- **Youngest Contract:** {summary['contract_statistics']['contract_ages_days']['min']} days
- **Oldest Contract:** {summary['contract_statistics']['contract_ages_days']['max']} days
- **Mean Age:** {summary['contract_statistics']['contract_ages_days']['mean']} days
- **Median Age:** {summary['contract_statistics']['contract_ages_days']['median']} days

---

## 🎨 NFT Activity Patterns

### Mint Operations
- **Total Mints:** {summary['activity_statistics']['mint_operations']['total']:,}
- **Min Mints per Contract:** {summary['activity_statistics']['mint_operations']['stats']['min']}
- **Max Mints per Contract:** {summary['activity_statistics']['mint_operations']['stats']['max']}
- **Mean Mints per Contract:** {summary['activity_statistics']['mint_operations']['stats']['mean']}
- **Median Mints per Contract:** {summary['activity_statistics']['mint_operations']['stats']['median']}

### Burn Operations
- **Total Burns:** {summary['activity_statistics']['burn_operations']['total']:,}
- **Min Burns per Contract:** {summary['activity_statistics']['burn_operations']['stats']['min']}
- **Max Burns per Contract:** {summary['activity_statistics']['burn_operations']['stats']['max']}
- **Mean Burns per Contract:** {summary['activity_statistics']['burn_operations']['stats']['mean']}
- **Median Burns per Contract:** {summary['activity_statistics']['burn_operations']['stats']['median']}

### Transfer Operations
- **Total Transfers:** {summary['activity_statistics']['transfer_operations']['total']:,}
- **Min Transfers per Contract:** {summary['activity_statistics']['transfer_operations']['stats']['min']}
- **Max Transfers per Contract:** {summary['activity_statistics']['transfer_operations']['stats']['max']}
- **Mean Transfers per Contract:** {summary['activity_statistics']['transfer_operations']['stats']['mean']}
- **Median Transfers per Contract:** {summary['activity_statistics']['transfer_operations']['stats']['median']}

---

## 📈 Contract Activity Rankings

### Top 10 Most Active Contracts (by total transactions)

"""
    
    # Sort contracts by activity
    contract_activities = []
    for contract_addr, features in contracts.items():
        if 'error' not in features:
            contract_data = features.get('contract', {})
            total_txs = contract_data.get('total_normal_transactions', 0)
            nft_transfers = contract_data.get('total_nft_transfers', 0)
            age = contract_data.get('temporal_patterns', {}).get('contract_age_days', 0)
            contract_activities.append((contract_addr, total_txs, nft_transfers, age))
    
    contract_activities.sort(key=lambda x: x[1], reverse=True)
    
    report += "| Rank | Contract | Transactions | NFT Transfers | Age (days) |\n"
    report += "|------|----------|--------------|---------------|------------|\n"
    
    for idx, (contract, txs, transfers, age) in enumerate(contract_activities[:10], 1):
        report += f"| {idx} | `{contract[:10]}...` | {txs:,} | {transfers:,} | {age:.1f} |\n"
    
    report += "\n---\n\n"
    report += "**Report Generated:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
    
    return report

def main():
    """Main execution"""
    
    print("Loading temporal features...")
    data = load_temporal_features()
    
    print("Generating summary statistics...")
    summary = generate_summary_report(data)
    
    print("Generating detailed report...")
    report = generate_detailed_report(data)
    
    # Save summary as JSON
    with open('temporal_features_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Summary saved to: temporal_features_summary.json")
    
    # Save detailed report as Markdown
    with open('TEMPORAL_FEATURES_REPORT.md', 'w') as f:
        f.write(report)
    
    print("✓ Detailed report saved to: TEMPORAL_FEATURES_REPORT.md")
    
    # Print summary to console
    print("\n" + "=" * 80)
    print("TEMPORAL FEATURE ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\nTotal Contracts: {summary['overview']['total_contracts_analyzed']}")
    print(f"Successful: {summary['overview']['successful_analyses']}")
    print(f"Failed: {summary['overview']['failed_analyses']}")
    print(f"Success Rate: {summary['overview']['success_rate']}")
    print(f"\nTotal Creator Transactions: {summary['creator_statistics']['total_transactions']:,}")
    print(f"Total Contract Transactions: {summary['contract_statistics']['total_transactions']:,}")
    print(f"\nTotal Mint Operations: {summary['activity_statistics']['mint_operations']['total']:,}")
    print(f"Total Burn Operations: {summary['activity_statistics']['burn_operations']['total']:,}")
    print(f"Total Transfer Operations: {summary['activity_statistics']['transfer_operations']['total']:,}")
    print()

if __name__ == '__main__':
    main()
