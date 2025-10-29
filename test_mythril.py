"""
Test Mythril integration with a single contract.
This tests the new Mythril analyzer before running full analysis.
"""

from mythril_analyzer import MythrilAnalyzer
import json

print("="*70)
print("MYTHRIL INTEGRATION TEST")
print("="*70)

# Test with a well-known NFT contract (BAYC)
test_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"

print(f"\nTesting with Bored Ape Yacht Club (BAYC)")
print(f"Address: {test_address}")
print(f"Timeout: 120 seconds (2 minutes)")
print(f"\nStarting analysis...\n")

# Run analysis
result = MythrilAnalyzer.analyze_address(test_address, timeout=120)

# Display results
print("\n" + "="*70)
print("RESULTS")
print("="*70)

if result.get("success"):
    print(f"✅ Analysis completed successfully!")
    print(f"\nTotal issues found: {result['issue_count']}")
    
    severity = result.get("severity_breakdown", {})
    print(f"\nSeverity breakdown:")
    print(f"  🔴 High:   {severity.get('High', 0)}")
    print(f"  🟡 Medium: {severity.get('Medium', 0)}")
    print(f"  🟢 Low:    {severity.get('Low', 0)}")
    
    if result['issues']:
        print(f"\nTop 3 findings:")
        for i, issue in enumerate(result['issues'][:3], 1):
            print(f"\n  [{i}] {issue['title']}")
            print(f"      Severity: {issue['severity']}")
            print(f"      SWC-ID: {issue.get('swc_id', 'N/A')}")
            print(f"      Description: {issue['description'][:150]}...")
    else:
        print(f"\n✅ No vulnerabilities detected - contract appears secure!")
    
    # Save full report
    with open('mythril_test_report.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n📄 Full report saved to: mythril_test_report.json")
    
else:
    print(f"❌ Analysis failed")
    print(f"Error: {result.get('error', 'Unknown error')}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

# Print formatted report
print("\n\nFORMATTED REPORT:")
print(MythrilAnalyzer.format_report(result))
