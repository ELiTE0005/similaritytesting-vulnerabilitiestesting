"""
Mythril analysis prioritized by similarity report.
Analyzes contracts with high similarity scores first (likely clones with shared vulnerabilities).
"""

import json
import os
from pathlib import Path
from typing import List, Tuple, Optional
from eth_utils.address import to_checksum_address
from mythril_analyzer import MythrilAnalyzer
from etherscan_client import EtherscanClient


def load_similarity_report() -> Optional[dict]:
    """Load the similarity analysis report."""
    if os.path.exists('similarity_report.json'):
        with open('similarity_report.json') as f:
            return json.load(f)
    return None


def get_high_risk_contracts(similarity_report: dict, threshold: float = 0.95) -> List[str]:
    """
    Extract contracts involved in high-similarity pairs.
    
    Args:
        similarity_report: Similarity analysis results
        threshold: Minimum similarity (0-1 range, e.g., 0.95 = 95%)
        
    Returns:
        List of unique contract addresses sorted by risk
    """
    if not similarity_report:
        return []
    
    # Track contracts and their risk scores
    contract_risk = {}  # {address: risk_score}
    
    # Iterate through all pair comparisons
    for pair_key, pair_data in similarity_report.items():
        if isinstance(pair_data, dict):
            full_sim = pair_data.get('full_similarity', 0)
            partial_sim = pair_data.get('partial_similarity', 0)
            
            # High risk if either similarity is >= threshold
            if full_sim >= threshold or partial_sim >= threshold:
                addr1 = pair_data.get('contract1', '')
                addr2 = pair_data.get('contract2', '')
                
                # Risk score = max similarity
                risk_score = max(full_sim, partial_sim)
                
                # Update risk scores (keep highest)
                if addr1:
                    contract_risk[addr1] = max(contract_risk.get(addr1, 0), risk_score)
                if addr2:
                    contract_risk[addr2] = max(contract_risk.get(addr2, 0), risk_score)
    
    # Sort by risk score (highest first)
    sorted_contracts = sorted(contract_risk.items(), key=lambda x: x[1], reverse=True)
    
    return [addr for addr, score in sorted_contracts]


def main():
    """Main function - analyze high-risk contracts based on similarity."""
    
    # Check Mythril installation
    if not MythrilAnalyzer.check_mythril_installation():
        print("\nPlease install Mythril in WSL Ubuntu first.")
        return
    
    # Load similarity report
    print("Loading similarity analysis results...")
    sim_report = load_similarity_report()
    
    if not sim_report:
        print("Error: similarity_report.json not found!")
        print("Please run the similarity analysis first.")
        return
    
    # Get high-risk contracts (95%+ similarity = 0.95+)
    high_risk_addresses = get_high_risk_contracts(sim_report, threshold=0.95)
    
    if not high_risk_addresses:
        print("No high-risk clone pairs found (>= 95% similarity).")
        print("Running analysis on all contracts instead...")
        # Fallback to reading from contracts.txt
        with open("contracts.txt") as f:
            high_risk_addresses = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    
    print(f"\n{'='*70}")
    print(f"MYTHRIL ANALYSIS - PRIORITIZED BY SIMILARITY")
    print(f"{'='*70}")
    print(f"High-risk contracts to analyze: {len(high_risk_addresses)}")
    print(f"(Contracts with >= 95% similarity to others)\n")
    
    # Load configuration
    with open("config.json") as f:
        config = json.load(f)
    
    api_key = config.get("etherscan_api_key") or os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: No Etherscan API key found")
        return
    
    # Create temp directory
    temp_dir = Path("temp_contracts")
    temp_dir.mkdir(exist_ok=True)
    
    # Initialize
    client = EtherscanClient(api_key)
    analyzer = MythrilAnalyzer(timeout=60)
    
    results = []
    successful = 0
    failed = 0
    skipped = 0
    
    # Analyze each contract
    for i, addr in enumerate(high_risk_addresses, 1):
        try:
            checksum_addr = to_checksum_address(addr)
        except:
            checksum_addr = addr
        
        print(f"\n[{i}/{len(high_risk_addresses)}] {checksum_addr[:10]}...")
        
        # Fetch source
        print(f"  Fetching source code...")
        contract_data = client.get_contract_source(checksum_addr)
        
        if not contract_data:
            print(f"  ✗ Skipped: Source code not available")
            skipped += 1
            results.append({
                "address": checksum_addr,
                "status": "skipped",
                "reason": "Source code not available"
            })
            continue
        
        # Handle multi-file contracts
        contract_code = ""
        contract_name = f"Contract_{checksum_addr[:8]}"
        
        if isinstance(contract_data, dict):
            main_file = None
            for filename, code in contract_data.items():
                if 'contract' in filename.lower() or filename.endswith('.sol'):
                    main_file = filename
                    contract_code = code
                    break
            if not main_file:
                main_file = list(contract_data.keys())[0]
                contract_code = contract_data[main_file]
            contract_name = Path(main_file).stem
        else:
            contract_code = contract_data
        
        # Save to temp file
        temp_file = temp_dir / f"{contract_name}.sol"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(contract_code)
        
        # Analyze with Mythril
        result = analyzer.analyze_source(str(temp_file), contract_name, timeout=60)
        result['address'] = checksum_addr
        
        results.append(result)
        
        # Print summary
        if result.get('success'):
            successful += 1
            issue_count = result.get('issue_count', 0)
            if issue_count > 0:
                severity = result.get('severity_breakdown', {})
                print(f"  🚨 VULNERABILITIES FOUND: {issue_count} issues")
                print(f"    🔴 High: {severity.get('High', 0)}")
                print(f"    🟡 Medium: {severity.get('Medium', 0)}")
                print(f"    🟢 Low: {severity.get('Low', 0)}")
                
                # Print critical issues
                for issue in result.get('issues', []):
                    if issue.get('severity') in ['High', 'Medium']:
                        print(f"      - [{issue.get('severity')}] {issue.get('title')}")
            else:
                print(f"  ✓ No vulnerabilities detected")
        else:
            failed += 1
            error = result.get('error', 'Unknown error')
            print(f"  ✗ Failed: {error[:100]}")
    
    # Generate prioritized report
    report = {
        'analysis_type': 'similarity_prioritized',
        'similarity_threshold': 95.0,
        'total_contracts': len(high_risk_addresses),
        'successful': successful,
        'failed': failed,
        'skipped': skipped,
        'total_issues': sum(r.get('issue_count', 0) for r in results if r.get('success')),
        'results': results,
        'note': 'Analyzed contracts with >= 95% similarity (likely clones)'
    }
    
    output_file = 'mythril_prioritized_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"PRIORITIZED ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"High-Risk Contracts: {report['total_contracts']}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total Issues Found: {report['total_issues']}")
    print(f"\nReport saved to: {output_file}")
    
    # Find vulnerable clones
    vuln_contracts = [r for r in results if r.get('success') and r.get('issue_count', 0) > 0]
    
    if vuln_contracts:
        print(f"\n{'='*70}")
        print(f"⚠️  VULNERABLE CLONES DETECTED ({len(vuln_contracts)})")
        print(f"{'='*70}")
        print("These contracts have both HIGH SIMILARITY and VULNERABILITIES!")
        print("This indicates copied vulnerable code.\n")
        
        for result in vuln_contracts:
            addr = result.get('address', 'Unknown')
            count = result.get('issue_count', 0)
            severity = result.get('severity_breakdown', {})
            
            print(f"\n{addr}")
            print(f"  Issues: {count} total")
            print(f"  🔴 High: {severity.get('High', 0)}  "
                  f"🟡 Medium: {severity.get('Medium', 0)}  "
                  f"🟢 Low: {severity.get('Low', 0)}")
            
            # Print all High/Medium issues
            critical_issues = [
                i for i in result.get('issues', [])
                if i.get('severity') in ['High', 'Medium']
            ]
            
            if critical_issues:
                print(f"  Critical Issues:")
                for issue in critical_issues:
                    print(f"    - [{issue.get('severity')}] {issue.get('title')}")
    
    # Cross-reference with similarity
    print(f"\n{'='*70}")
    print(f"CLONE CLUSTER ANALYSIS")
    print(f"{'='*70}")
    
    # Find which vulnerable contracts are similar to each other
    if len(vuln_contracts) >= 2:
        vuln_addresses = {r['address'] for r in vuln_contracts}
        
        similar_pairs = []
        for pair_key, pair_data in sim_report.items():
            if isinstance(pair_data, dict):
                addr1 = pair_data.get('contract1', '')
                addr2 = pair_data.get('contract2', '')
                
                if addr1 in vuln_addresses and addr2 in vuln_addresses:
                    full_sim = pair_data.get('full_similarity', 0)
                    if full_sim >= 0.95:  # 95%
                        similar_pairs.append((addr1, addr2, full_sim * 100))  # Convert to percentage
        
        if similar_pairs:
            print(f"\nFound {len(similar_pairs)} vulnerable clone pairs:")
            for addr1, addr2, similarity in similar_pairs[:10]:
                print(f"  {addr1[:10]}... ↔ {addr2[:10]}... ({similarity:.1f}% similar)")
        else:
            print("\nNo vulnerable contracts are clones of each other.")
    
    # Cleanup
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print(f"\nTemp files cleaned up")


if __name__ == "__main__":
    main()
