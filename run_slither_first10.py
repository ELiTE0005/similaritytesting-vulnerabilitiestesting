"""
Slither vulnerability analysis for first 10 NFT contracts.
Fetches contracts from Etherscan and runs Slither analysis.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from etherscan_client import EtherscanClient


def check_slither():
    """Check if Slither is installed."""
    try:
        result = subprocess.run(['slither', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Slither found: {version}\n")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("✗ Slither not found. Install with: pip install slither-analyzer")
    return False


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
        print(f"  Running Slither analysis...")
        
        # Save output to a temp JSON file (more reliable than stdout)
        temp_json = f"temp_slither_{address}.json"
        
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
                
                print(f"  ✓ Found {len(issues)} issues")
                if len(issues) > 0:
                    for sev, count in severity_counts.items():
                        if count > 0:
                            emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 
                                    'Informational': 'ℹ️', 'Optimization': '⚡'}.get(sev, '•')
                            print(f"    {emoji} {sev}: {count}")
                
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
            # No JSON file created - check stderr
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
    print("="*70)
    print("SLITHER VULNERABILITY ANALYSIS - FIRST 10 CONTRACTS")
    print("="*70)
    print()
    
    # Check Slither installation
    if not check_slither():
        return
    
    # Load Etherscan API key from config.json
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
            addresses = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("✗ contracts.txt not found")
        return
    
    # Analyze first 10 contracts only
    sample_size = min(10, len(addresses))
    addresses = addresses[:sample_size]
    
    print(f"Analyzing first {sample_size} contracts from contracts.txt")
    print(f"{'='*70}\n")
    
    # Initialize Etherscan client
    etherscan = EtherscanClient(api_key)
    
    results = {}
    successful = 0
    failed = 0
    unavailable = 0
    total_issues = 0
    
    for idx, address in enumerate(addresses, 1):
        print(f"[{idx}/{sample_size}] Contract: {address}")
        
        # Fetch contract source
        print(f"  Fetching source code...")
        source_code = etherscan.get_contract_source(address)
        
        if not source_code:
            print(f"  ✗ Source code unavailable\n")
            results[address] = {
                'success': False,
                'error': 'Source code not available',
                'issues': [],
                'issue_count': 0
            }
            unavailable += 1
            time.sleep(0.25)  # Rate limiting
            continue
        
        print(f"  ✓ Retrieved ({len(source_code)} chars)")
        
        # Save contract to file
        contract_file = save_contract_file(address, source_code)
        print(f"  ✓ Saved to {contract_file}")
        
        # Run Slither analysis
        result = analyze_with_slither(contract_file, address)
        results[address] = result
        
        if result['success']:
            successful += 1
            total_issues += result['issue_count']
        else:
            failed += 1
            print(f"  ✗ Error: {result.get('error', 'Unknown')[:100]}")
        
        print()
        time.sleep(0.25)  # Rate limiting
    
    # Save results
    output_file = "slither_first10_report.json"
    report = {
        'sample_size': sample_size,
        'successful': successful,
        'failed': failed,
        'unavailable': unavailable,
        'total_issues': total_issues,
        'contracts': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"Contracts analyzed: {sample_size}")
    print(f"  ✓ Successful: {successful}")
    print(f"  ✗ Failed: {failed}")
    print(f"  ⚠ Unavailable: {unavailable}")
    print(f"  📋 Total issues found: {total_issues}")
    print(f"\nDetailed results saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    main()
