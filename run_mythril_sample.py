"""
Run Mythril vulnerability analysis on first 15 NFT contracts (SAMPLE).
"""

import json
import os
from pathlib import Path
from eth_utils.address import to_checksum_address
from mythril_analyzer import MythrilAnalyzer
from etherscan_client import EtherscanClient


def main():
    """Main function to run Mythril analysis on first 15 contracts."""
    
    # Check Mythril installation
    if not MythrilAnalyzer.check_mythril_installation():
        print("\nPlease install Mythril in WSL Ubuntu first.")
        return
    
    # Load configuration
    with open("config.json") as f:
        config = json.load(f)
    
    api_key = config.get("etherscan_api_key") or os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: No Etherscan API key found")
        return
    
    # Read contract addresses
    addresses_file = "contracts.txt"
    if not os.path.exists(addresses_file):
        print(f"Error: {addresses_file} not found")
        return
    
    with open(addresses_file) as f:
        addresses = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    
    # LIMIT TO FIRST 15
    addresses = addresses[:15]
    
    print(f"\n{'='*70}")
    print(f"MYTHRIL VULNERABILITY ANALYSIS (SAMPLE)")
    print(f"{'='*70}")
    print(f"Analyzing first {len(addresses)} contracts\n")
    
    # Create temp directory for contract files
    temp_dir = Path("temp_contracts")
    temp_dir.mkdir(exist_ok=True)
    
    # Initialize Etherscan client and Mythril analyzer
    client = EtherscanClient(api_key)
    analyzer = MythrilAnalyzer(timeout=60)  # Reduced to 60 seconds
    
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
        
        # Fetch contract source
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
                print(f"  ✓ Found {issue_count} issues:")
                print(f"    🔴 High: {severity.get('High', 0)}")
                print(f"    🟡 Medium: {severity.get('Medium', 0)}")
                print(f"    🟢 Low: {severity.get('Low', 0)}")
            else:
                print(f"  ✓ No vulnerabilities detected")
        else:
            failed += 1
            error = result.get('error', 'Unknown error')
            print(f"  ✗ Failed: {error[:100]}")
    
    # Generate report
    report = {
        'sample_size': len(addresses),
        'total_contracts': len(addresses),
        'successful': successful,
        'failed': failed,
        'skipped': skipped,
        'total_issues': sum(r.get('issue_count', 0) for r in results if r.get('success')),
        'results': results
    }
    
    output_file = 'mythril_sample_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print final summary
    print(f"\n{'='*70}")
    print(f"SAMPLE ANALYSIS COMPLETE")
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
            severity = result.get('severity_breakdown', {})
            
            print(f"{addr[:10]}... - {count} issues")
            print(f"  🔴 High: {severity.get('High', 0)}  "
                  f"🟡 Medium: {severity.get('Medium', 0)}  "
                  f"🟢 Low: {severity.get('Low', 0)}")
            
            # Print issue titles
            for issue in result.get('issues', [])[:3]:
                title = issue.get('title', 'Unknown')
                print(f"    - {title}")
            if len(result.get('issues', [])) > 3:
                print(f"    ... and {len(result.get('issues', [])) - 3} more")
            print()
    
    # Cleanup temp files
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print(f"\nTemp files cleaned up")


if __name__ == "__main__":
    main()
