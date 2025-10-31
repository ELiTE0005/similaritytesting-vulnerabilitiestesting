"""
Complete NFT Contract Analysis Pipeline
1. Fetch all contracts from Etherscan
2. Calculate similarity between all contract pairs
3. Run Slither vulnerability analysis on all contracts
4. Generate comprehensive reports
"""

import json
import os
import subprocess
import time
from pathlib import Path
from etherscan_client import EtherscanClient
from code_similarity import CodeSimilarity


def save_contract_file(address, source_code, output_dir="retrieved_contracts"):
    """Save contract source code to a .sol file."""
    Path(output_dir).mkdir(exist_ok=True)
    filepath = os.path.join(output_dir, f"{address}.sol")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(source_code)
    return filepath


def analyze_with_slither(contract_file, address):
    """
    Analyze a Solidity contract with Slither.
    Returns analysis results dictionary.
    """
    try:
        # Save output to a temp JSON file (more reliable than stdout)
        temp_json = f"temp_slither_{address}.json"
        
        # Check if the contract file is in Standard JSON format
        with open(contract_file, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
        
        # Use solc-select to automatically choose the right compiler version
        # This allows Slither to work with contracts using different Solidity versions
        if first_char == '{':
            # Standard JSON format - use --solc-standard-json flag
            cmd = ['slither', contract_file, '--json', temp_json, '--solc-disable-warnings', '--solc-standard-json']
        else:
            # Regular Solidity file
            cmd = ['slither', contract_file, '--json', temp_json, '--solc-disable-warnings']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Read the JSON output file
        if os.path.exists(temp_json):
            with open(temp_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clean up temp file
            os.remove(temp_json)
            
            # Parse Slither results
            if data.get('success'):
                detectors = data.get('results', {}).get('detectors', [])
                
                issues = []
                severity_counts = {'High': 0, 'Medium': 0, 'Low': 0, 'Informational': 0, 'Optimization': 0}
                
                for detector in detectors:
                    impact = detector.get('impact', 'Unknown')
                    check = detector.get('check', 'unknown')
                    description = detector.get('description', 'No description')
                    
                    issues.append({
                        'severity': impact,
                        'type': check,
                        'description': description
                    })
                    
                    if impact in severity_counts:
                        severity_counts[impact] += 1
                
                return {
                    'success': True,
                    'address': address,
                    'issues': issues,
                    'issue_count': len(issues),
                    'severity_breakdown': severity_counts
                }
            else:
                error = data.get('error', 'Unknown error')
                return {
                    'success': False,
                    'address': address,
                    'error': error,
                    'issues': [],
                    'issue_count': 0
                }
        else:
            # No JSON file created
            error_msg = result.stderr[:500] if result.stderr else 'Slither did not produce output file'
            return {
                'success': False,
                'address': address,
                'error': error_msg,
                'issues': [],
                'issue_count': 0
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'address': address,
            'error': 'Analysis timeout (60s)',
            'issues': [],
            'issue_count': 0
        }
    except Exception as e:
        return {
            'success': False,
            'address': address,
            'error': str(e),
            'issues': [],
            'issue_count': 0
        }


def main():
    """Main analysis workflow."""
    print("="*80)
    print("COMPLETE NFT CONTRACT ANALYSIS PIPELINE")
    print("="*80)
    print("Phase 1: Fetch Contracts")
    print("Phase 2: Similarity Analysis")
    print("Phase 3: Vulnerability Analysis (Slither)")
    print("="*80)
    print()
    
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('etherscan_api_key') or os.environ.get('ETHERSCAN_API_KEY')
        if not api_key:
            print("✗ No API key found in config.json or ETHERSCAN_API_KEY env var")
            return
    except FileNotFoundError:
        print("✗ config.json not found")
        return
    
    # Load contract addresses
    try:
        with open('contracts.txt', 'r') as f:
            addresses = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except FileNotFoundError:
        print("✗ contracts.txt not found")
        return
    
    total_contracts = len(addresses)
    print(f"Loaded {total_contracts} contract addresses")
    print()
    
    # Initialize Etherscan client
    etherscan = EtherscanClient(api_key)
    
    # ========================================================================
    # PHASE 1: FETCH CONTRACTS
    # ========================================================================
    print("="*80)
    print("PHASE 1: FETCHING CONTRACTS FROM ETHERSCAN")
    print("="*80)
    print()
    
    contracts = {}
    unavailable = []
    
    for idx, addr in enumerate(addresses, 1):
        print(f"[{idx}/{total_contracts}] Fetching {addr}...", end=" ", flush=True)
        source_code = etherscan.get_contract_source(addr)
        
        if not source_code:
            print("UNAVAILABLE")
            unavailable.append(addr)
        else:
            print(f"OK ({len(source_code)} chars)")
            contracts[addr] = source_code
            # Save to file for Slither
            save_contract_file(addr, source_code)
        
        # Rate limiting: 5 requests/second max for free tier
        time.sleep(0.25)
    
    # Log unavailable contracts
    if unavailable:
        with open("unavailable_contracts.txt", "w") as f:
            for addr in unavailable:
                f.write(addr + "\n")
    
    retrieved_count = len(contracts)
    print()
    print(f"✓ Retrieved: {retrieved_count}/{total_contracts} contracts ({retrieved_count/total_contracts*100:.1f}%)")
    print(f"✗ Unavailable: {len(unavailable)} contracts")
    if unavailable:
        print(f"  (See unavailable_contracts.txt for details)")
    print()
    
    # ========================================================================
    # PHASE 2: SIMILARITY ANALYSIS
    # ========================================================================
    print("="*80)
    print("PHASE 2: CALCULATING SIMILARITY BETWEEN CONTRACT PAIRS")
    print("="*80)
    print()
    
    similarity_report = {}
    contract_addresses = list(contracts.keys())
    total_pairs = (len(contract_addresses) * (len(contract_addresses) - 1)) // 2
    pair_num = 0
    
    print(f"Analyzing {total_pairs} contract pairs...")
    print()
    
    for i in range(len(contract_addresses)):
        for j in range(i+1, len(contract_addresses)):
            pair_num += 1
            a1, a2 = contract_addresses[i], contract_addresses[j]
            
            if pair_num % 100 == 0 or pair_num == 1:
                print(f"[{pair_num}/{total_pairs}] Comparing {a1[:10]}... vs {a2[:10]}...")
            
            code1, code2 = contracts[a1], contracts[a2]
            full_sim = CodeSimilarity.full_similarity(code1, code2)
            partial_sim = CodeSimilarity.partial_similarity(code1, code2)
            
            # Use string key for JSON compatibility
            key = f"{a1}_{a2}"
            similarity_report[key] = {
                "contract1": a1,
                "contract2": a2,
                "full_similarity": full_sim,
                "partial_similarity": partial_sim
            }
    
    # Save similarity report
    with open("similarity_report.json", "w") as f:
        json.dump(similarity_report, f, indent=2)
    
    # Calculate high-risk clones
    high_risk_pairs = [
        pair for pair in similarity_report.values()
        if pair["full_similarity"] >= 0.95 or pair["partial_similarity"] >= 0.95
    ]
    
    print()
    print(f"✓ Similarity analysis complete: {total_pairs} pairs analyzed")
    print(f"  📊 High-risk clone pairs (≥95% similar): {len(high_risk_pairs)}")
    print(f"  💾 Report saved to: similarity_report.json")
    print()
    
    # ========================================================================
    # PHASE 3: VULNERABILITY ANALYSIS (SLITHER)
    # ========================================================================
    print("="*80)
    print("PHASE 3: VULNERABILITY ANALYSIS WITH SLITHER")
    print("="*80)
    print()
    
    # Check Slither installation
    try:
        result = subprocess.run(['slither', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Slither found: {version}")
        else:
            print("✗ Slither not found. Install with: pip install slither-analyzer")
            print("  Skipping vulnerability analysis...")
            return
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Slither not found. Install with: pip install slither-analyzer")
        print("  Skipping vulnerability analysis...")
        return
    
    print()
    print(f"Analyzing {retrieved_count} contracts with Slither...")
    print("(This may take a while - approximately 30-60s per contract)")
    print()
    
    vulnerability_report = {}
    vuln_successful = 0
    vuln_failed = 0
    total_issues = 0
    total_high = 0
    total_medium = 0
    total_low = 0
    
    for idx, addr in enumerate(contract_addresses, 1):
        print(f"[{idx}/{retrieved_count}] Analyzing {addr}...")
        
        contract_file = os.path.join("retrieved_contracts", f"{addr}.sol")
        
        if not os.path.exists(contract_file):
            print(f"  ✗ Contract file not found")
            vulnerability_report[addr] = {
                'success': False,
                'error': 'Contract file not found',
                'issues': [],
                'issue_count': 0
            }
            vuln_failed += 1
            continue
        
        # Run Slither analysis
        result = analyze_with_slither(contract_file, addr)
        vulnerability_report[addr] = result
        
        if result['success']:
            vuln_successful += 1
            issue_count = result['issue_count']
            total_issues += issue_count
            
            severity = result.get('severity_breakdown', {})
            high = severity.get('High', 0)
            medium = severity.get('Medium', 0)
            low = severity.get('Low', 0)
            
            total_high += high
            total_medium += medium
            total_low += low
            
            if issue_count > 0:
                print(f"  ✓ Found {issue_count} issues", end="")
                if high > 0 or medium > 0 or low > 0:
                    print(f" (🔴{high} 🟡{medium} 🟢{low})")
                else:
                    print()
            else:
                print(f"  ✓ No issues found")
        else:
            vuln_failed += 1
            error = result.get('error', 'Unknown')[:80]
            print(f"  ✗ Failed: {error}")
        
        # Small delay to avoid overwhelming system
        time.sleep(0.5)
    
    # Save vulnerability report
    with open("vulnerability_report.json", "w") as f:
        json.dump(vulnerability_report, f, indent=2)
    
    print()
    print(f"✓ Vulnerability analysis complete")
    print(f"  ✅ Successful: {vuln_successful}/{retrieved_count}")
    print(f"  ❌ Failed: {vuln_failed}/{retrieved_count}")
    print(f"  📋 Total issues found: {total_issues}")
    print(f"     🔴 High: {total_high}")
    print(f"     🟡 Medium: {total_medium}")
    print(f"     🟢 Low: {total_low}")
    print(f"  💾 Report saved to: vulnerability_report.json")
    print()
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("="*80)
    print("ANALYSIS COMPLETE - FINAL SUMMARY")
    print("="*80)
    print()
    print(f"📊 Contracts Retrieved: {retrieved_count}/{total_contracts} ({retrieved_count/total_contracts*100:.1f}%)")
    print(f"📊 Similarity Pairs Analyzed: {total_pairs}")
    print(f"📊 High-Risk Clone Pairs (≥95%): {len(high_risk_pairs)}")
    print(f"📊 Vulnerability Scans Successful: {vuln_successful}/{retrieved_count}")
    print(f"📊 Total Vulnerabilities Found: {total_issues}")
    print(f"   🔴 High Severity: {total_high}")
    print(f"   🟡 Medium Severity: {total_medium}")
    print(f"   🟢 Low Severity: {total_low}")
    print()
    print("📁 Generated Reports:")
    print("   • similarity_report.json - Similarity analysis of all contract pairs")
    print("   • vulnerability_report.json - Slither vulnerability analysis results")
    print("   • unavailable_contracts.txt - Contracts without source code")
    print("   • retrieved_contracts/ - All contract source files (.sol)")
    print()
    print("="*80)
    
    # Generate detailed summary report
    summary = {
        "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_contracts": total_contracts,
        "retrieved_contracts": retrieved_count,
        "unavailable_contracts": len(unavailable),
        "similarity_analysis": {
            "total_pairs_analyzed": total_pairs,
            "high_risk_clone_pairs": len(high_risk_pairs)
        },
        "vulnerability_analysis": {
            "successful_scans": vuln_successful,
            "failed_scans": vuln_failed,
            "total_issues": total_issues,
            "severity_breakdown": {
                "High": total_high,
                "Medium": total_medium,
                "Low": total_low
            }
        }
    }
    
    with open("ANALYSIS_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("📊 Quick summary saved to: ANALYSIS_SUMMARY.json")
    print("="*80)


if __name__ == "__main__":
    main()
