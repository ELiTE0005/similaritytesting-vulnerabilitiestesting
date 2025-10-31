"""
Slither vulnerability analysis for NFT contracts.
Analyzes first 10 contracts using Slither static analyzer.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from eth_utils.address import to_checksum_address
from etherscan_client import EtherscanClient


def analyze_with_slither(contract_file: str, address: str) -> Dict:
    """
    Analyze a Solidity contract with Slither.
    
    Args:
        contract_file: Path to .sol file
        address: Contract address for reference
        
    Returns:
        Analysis results dictionary
    """
    try:
        print(f"  Running Slither analysis...")
        
        # Run Slither with JSON output
        cmd = ['slither', contract_file, '--json', '-', '--solc-disable-warnings']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Slither outputs JSON to stdout, but may also have stderr messages
        output = result.stdout.strip()
        
        # If no stdout but stderr exists, check if it's JSON error
        if not output and result.stderr:
            # Try to parse stderr as JSON (some errors come this way)
            try:
                data = json.loads(result.stderr)
                if isinstance(data, dict) and 'success' in data:
                    output = result.stderr
            except:
                pass
        
        # Parse JSON output
        if output:
            try:
                data = json.loads(output)
                
                if data.get('success'):
                    detectors = data.get('results', {}).get('detectors', [])
                    
                    # Count by impact
                    impact_counts = {
                        'High': 0,
                        'Medium': 0,
                        'Low': 0,
                        'Informational': 0,
                        'Optimization': 0
                    }
                    
                    for detector in detectors:
                        impact = detector.get('impact', 'Informational')
                        if impact in impact_counts:
                            impact_counts[impact] += 1
                    
                    return {
                        'success': True,
                        'address': address,
                        'issues': detectors,
                        'issue_count': len(detectors),
                        'impact_breakdown': impact_counts,
                        'error': None
                    }
                else:
                    # Slither failed
                    error_msg = data.get('error', 'Unknown Slither error')
                    return {
                        'success': False,
                        'address': address,
                        'error': error_msg,
                        'issues': [],
                        'issue_count': 0
                    }
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'address': address,
                    'error': f'JSON parse error: {str(e)}',
                    'issues': [],
                    'issue_count': 0
                }
        else:
            # No output at all
            error_msg = result.stderr[:500] if result.stderr else 'No output from Slither'
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
            'error': 'Analysis timed out after 30 seconds',
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
    """Main function - analyze first 10 contracts with Slither."""
    
    # Load configuration
    with open("config.json") as f:
        config = json.load(f)
    
    api_key = config.get("etherscan_api_key") or os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: No Etherscan API key found")
        return
    
    # Read contract addresses - FIRST 10 ONLY
    addresses_file = "contracts.txt"
    if not os.path.exists(addresses_file):
        print(f"Error: {addresses_file} not found")
        return
    
    with open(addresses_file) as f:
        addresses = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ][:10]  # FIRST 10 CONTRACTS
    
    print(f"\n{'='*70}")
    print(f"SLITHER VULNERABILITY ANALYSIS")
    print(f"{'='*70}")
    print(f"Analyzing first {len(addresses)} contracts\n")
    
    # Create temp directory
    temp_dir = Path("temp_contracts")
    temp_dir.mkdir(exist_ok=True)
    
    # Initialize
    client = EtherscanClient(api_key)
    
    results = []
    successful = 0
    failed = 0
    skipped = 0
    
    for i, addr in enumerate(addresses, 1):
        try:
            checksum_addr = to_checksum_address(addr)
        except:
            checksum_addr = addr
        
        print(f"\n[{i}/{len(addresses)}] {checksum_addr[:10]}...")
        
        # Fetch source
        print(f"  Fetching source code from Etherscan...")
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
            # Multiple files - use main contract
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
            # Single file
            contract_code = contract_data
        
        # Save to temp file
        temp_file = temp_dir / f"{contract_name}.sol"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(contract_code)
        
        # Analyze with Slither
        result = analyze_with_slither(str(temp_file), checksum_addr)
        results.append(result)
        
        # Print summary
        if result.get('success'):
            successful += 1
            issue_count = result.get('issue_count', 0)
            if issue_count > 0:
                impact = result.get('impact_breakdown', {})
                print(f"  ✓ Found {issue_count} issues:")
                print(f"    🔴 High: {impact.get('High', 0)}")
                print(f"    🟡 Medium: {impact.get('Medium', 0)}")
                print(f"    🔵 Low: {impact.get('Low', 0)}")
                print(f"    ℹ️  Info: {impact.get('Informational', 0)}")
                print(f"    ⚡ Opt: {impact.get('Optimization', 0)}")
            else:
                print(f"  ✓ No vulnerabilities detected")
        else:
            failed += 1
            error = result.get('error', 'Unknown error')
            print(f"  ✗ Failed: {error[:100]}")
    
    # Generate report
    report = {
        'tool': 'Slither',
        'version': '0.11.3',
        'sample_size': len(addresses),
        'total_contracts': len(addresses),
        'successful': successful,
        'failed': failed,
        'skipped': skipped,
        'total_issues': sum(r.get('issue_count', 0) for r in results if r.get('success')),
        'results': results
    }
    
    output_file = 'slither_analysis_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print final summary
    print(f"\n{'='*70}")
    print(f"SLITHER ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"Contracts Analyzed: {report['total_contracts']}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total Issues Found: {report['total_issues']}")
    print(f"\nReport saved to: {output_file}")
    
    # Print contracts with vulnerabilities
    vuln_contracts = [r for r in results if r.get('success') and r.get('issue_count', 0) > 0]
    if vuln_contracts:
        print(f"\n{'='*70}")
        print(f"CONTRACTS WITH VULNERABILITIES ({len(vuln_contracts)})")
        print(f"{'='*70}\n")
        
        for result in vuln_contracts:
            addr = result.get('address', 'Unknown')
            count = result.get('issue_count', 0)
            impact = result.get('impact_breakdown', {})
            
            print(f"\n{addr}")
            print(f"  Total Issues: {count}")
            print(f"  🔴 High: {impact.get('High', 0)}  "
                  f"🟡 Medium: {impact.get('Medium', 0)}  "
                  f"🔵 Low: {impact.get('Low', 0)}  "
                  f"ℹ️  Info: {impact.get('Informational', 0)}  "
                  f"⚡ Opt: {impact.get('Optimization', 0)}")
            
            # Print High and Medium severity issues
            critical_issues = [
                i for i in result.get('issues', [])
                if i.get('impact') in ['High', 'Medium']
            ]
            
            if critical_issues:
                print(f"  Critical Issues:")
                for issue in critical_issues[:5]:  # First 5 critical issues
                    print(f"    - [{issue.get('impact')}] {issue.get('check')}: {issue.get('description', '')[:80]}...")
    
    # Cleanup temp files
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print(f"\nTemp files cleaned up")


if __name__ == "__main__":
    main()
