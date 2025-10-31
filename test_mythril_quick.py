"""Quick test of Mythril analyzer."""
from mythril_analyzer import MythrilAnalyzer

result = MythrilAnalyzer.analyze_source('test_contract.sol', 'TestNFT', 60)

print('\n' + '='*60)
print('MYTHRIL TEST RESULT')
print('='*60)
print(f'Success: {result["success"]}')
print(f'Issues found: {result["issue_count"]}')
print(f'Severity breakdown: {result["severity_breakdown"]}')

if result['issues']:
    print('\nIssue details:')
    for i, issue in enumerate(result['issues'], 1):
        print(f'\n[{i}] {issue["title"]}')
        print(f'    Severity: {issue["severity"]}')
        print(f'    SWC-ID: {issue.get("swc-id", "N/A")}')
        print(f'    Function: {issue.get("function", "N/A")}')
        print(f'    Line: {issue.get("lineno", "N/A")}')
        print(f'    Description: {issue["description"][:200]}...')
